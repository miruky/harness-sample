"""docs/specs/ の Markdown を Confluence へ書き込み、ページがローカルと一致しているかを確かめる。

  uv run python tools/docs_sync.py push      # 変わったファイルだけ、ページを作るか更新する
  uv run python tools/docs_sync.py verify    # ページを全文取得して、ローカルと照らし合わせる
  uv run python tools/docs_sync.py verify-body <ファイル> < 本文   # MCPで取得した本文を照合する

元はリポジトリの Markdown で、Confluence は写し。照合は2つ行う。
  1. ページの末尾に書いた sha256 が、ローカルの Markdown の sha256 と同じか
  2. ページから取得した本文が、ローカルから作った本文と同じか（画面で編集されていないか）

接続先は環境変数で渡す。値はリポジトリに置かない。
  CONFLUENCE_BASE_URL   例 https://example.atlassian.net/wiki
  CONFLUENCE_SPACE      スペースキー
  CONFLUENCE_EMAIL、CONFLUENCE_API_TOKEN
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "docs" / "specs"
MARK = "docs-sync"
Page = dict[str, Any]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inline(text: str) -> str:
    """行の中の `code` と [文字](URL) を変換する。"""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', out)


def render(markdown: str, source: str) -> str:
    """Markdown を Confluence の保存形式へ変換する。見出し、段落、箇条書き、コードを扱う。"""
    parts: list[str] = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            body: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                body.append(lines[index])
                index += 1
            parts.append("<pre>" + html.escape("\n".join(body), quote=False) + "</pre>")
        elif heading := re.match(r"(#{1,4}) (.+)", line):
            level = len(heading.group(1))
            parts.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif re.match(r"[-*] ", line):
            items: list[str] = []
            while index < len(lines) and re.match(r"[-*] ", lines[index]):
                items.append(f"<li>{inline(lines[index][2:])}</li>")
                index += 1
            parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif line.strip():
            parts.append(f"<p>{inline(line)}</p>")
        index += 1
    note = f"{MARK}: {source} sha256:{digest(markdown)}"
    parts.append(
        f"<p>このページは {source} から自動で書き込まれます。直接編集しないでください。</p>"
    )
    parts.append(f"<p>{note}</p>")
    return "".join(parts)


def plain(storage: str) -> str:
    """APIで書いたページ（XHTML）から、タグ、記号、空白を除いた本文の文字。"""
    return squeeze(html.unescape(re.sub(r"<[^>]+>", " ", storage)))


def squeeze(text: str) -> str:
    """Markdown の記号と空白を除いた文字。"""
    return re.sub(r"[\s#*`\-]+", "", text)


def markdown_body(markdown: str, source: str) -> str:
    """MCPで書き込む本文。Markdown のまま、APIで書くページと同じ注意書きと sha256 を付ける。"""
    return (
        markdown.rstrip("\n")
        + f"\n\nこのページは {source} から自動で書き込まれます。直接編集しないでください。"
        + f"\n\n{MARK}: {source} sha256:{digest(markdown)}\n"
    )


def title_of(markdown: str, path: Path) -> str:
    first = markdown.splitlines()[0] if markdown else ""
    return first[2:].strip() if first.startswith("# ") else path.stem


class Confluence:
    def __init__(self) -> None:
        self.base = os.environ["CONFLUENCE_BASE_URL"].rstrip("/")
        self.space = os.environ["CONFLUENCE_SPACE"]
        user = os.environ.get("CONFLUENCE_EMAIL", "")
        token = os.environ.get("CONFLUENCE_API_TOKEN", "")
        self.auth = base64.b64encode(f"{user}:{token}".encode()).decode()

    def call(self, method: str, path: str, payload: dict[str, object] | None = None) -> Page:
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Authorization", f"Basic {self.auth}")
        request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=30) as response:
            result: Page = json.loads(response.read().decode())
            return result

    def find(self, title: str) -> Page | None:
        query = urllib.parse.urlencode(
            {"spaceKey": self.space, "title": title, "expand": "body.storage,version"}
        )
        results = self.call("GET", f"/rest/api/content?{query}")["results"]
        return results[0] if results else None

    def save(self, title: str, storage: str, page: Page | None) -> int:
        payload: dict[str, object] = {
            "type": "page",
            "title": title,
            "space": {"key": self.space},
            "body": {"storage": {"value": storage, "representation": "storage"}},
        }
        if page is None:
            return int(self.call("POST", "/rest/api/content", payload)["version"]["number"])
        payload["version"] = {"number": page["version"]["number"] + 1}
        return int(
            self.call("PUT", f"/rest/api/content/{page['id']}", payload)["version"]["number"]
        )


def targets() -> list[Path]:
    return sorted(p for p in SPECS.glob("*.md") if p.name != "README.md")


def push(wiki: Confluence) -> int:
    for path in targets():
        markdown = path.read_text(encoding="utf-8")
        source = str(path.relative_to(ROOT))
        title = title_of(markdown, path)
        page = wiki.find(title)
        storage = render(markdown, source)
        if page and plain(page["body"]["storage"]["value"]) == plain(storage):
            print(f"変更なし  {source} → 「{title}」 v{page['version']['number']}")
            continue
        version = wiki.save(title, storage, page)
        print(f"{'更新' if page else '作成'}      {source} → 「{title}」 v{version}")
    return 0


def mismatch(markdown: str, source: str, remote: str) -> str:
    """ページの本文がローカルと合わない理由。合っていれば空文字。APIでもMCPでも、照合はここを通す。"""
    recorded = re.search(rf"{MARK}: \S+ sha256:([0-9a-f]{{64}})", plain_keep_space(remote))
    if recorded is None or recorded.group(1) != digest(markdown):
        return "の sha256 がローカルと違います（ページが古いままです）"
    # MCPで書いたページは Markdown のまま保存される。山かっこをタグと取り違えないよう比べ方を変える
    written_as_markdown = "<p>" not in remote
    if written_as_markdown:
        same = squeeze(remote) == squeeze(markdown_body(markdown, source))
    else:
        same = plain(remote) == plain(render(markdown, source))
    if not same:
        return "の本文がローカルと違います（画面で編集されています）"
    return ""


def verify_body(path: Path, remote: str) -> int:
    markdown = path.read_text(encoding="utf-8")
    source = str(path.resolve().relative_to(ROOT))
    reason = mismatch(markdown, source, remote)
    if reason:
        print(f"{source}: ページ{reason}")
        print("直し方: 元は docs/specs/ です。ページを書き直してから、もう一度照合してください。")
        return 1
    print(f"一致      {source} sha256:{digest(markdown)[:12]}")
    return 0


def verify(wiki: Confluence) -> int:
    problems = 0
    for path in targets():
        markdown = path.read_text(encoding="utf-8")
        source = str(path.relative_to(ROOT))
        title = title_of(markdown, path)
        page = wiki.find(title)
        if page is None:
            print(f"{source}: ページ「{title}」がありません")
            problems += 1
            continue
        remote = page["body"]["storage"]["value"]
        number = page["version"]["number"]
        reason = mismatch(markdown, source, remote)
        if reason:
            print(f"{source}: ページ「{title}」{reason}")
            problems += 1
        else:
            print(f"一致      {source} = 「{title}」 v{number} sha256:{digest(markdown)[:12]}")
    if problems:
        print(f"\n{problems} 件が一致しません。")
        print("直し方: 元は docs/specs/ です。make docs-push で書き直してください。")
        print("画面で直した内容を残すときは、先に Markdown へ写してコミットします。")
    return 1 if problems else 0


def plain_keep_space(storage: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", storage))


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "verify-body" and len(sys.argv) == 3:
        return verify_body(Path(sys.argv[2]), sys.stdin.read())
    if command not in ("push", "verify"):
        print(__doc__)
        return 2
    if not os.environ.get("CONFLUENCE_BASE_URL"):
        print("CONFLUENCE_BASE_URL がないので、何もしません。")
        return 0
    wiki = Confluence()
    return push(wiki) if command == "push" else verify(wiki)


if __name__ == "__main__":
    sys.exit(main())
