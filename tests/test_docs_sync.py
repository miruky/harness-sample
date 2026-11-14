from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.fake_confluence import FakeConfluence
from tools import docs_sync

SPEC = (
    "# 予約のCSV出力\n\n- 列は `id`、`room`、`owner` の順\n\n"
    "```bash\nbooking export --format csv\n```\n"
)


@pytest.fixture
def wiki(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeConfluence]:
    fake = FakeConfluence()
    specs = tmp_path / "docs" / "specs"
    specs.mkdir(parents=True)
    (specs / "0001-export.md").write_text(SPEC, encoding="utf-8")
    monkeypatch.setattr(docs_sync, "ROOT", tmp_path)
    monkeypatch.setattr(docs_sync, "SPECS", specs)
    monkeypatch.setenv("CONFLUENCE_BASE_URL", fake.url)
    monkeypatch.setenv("CONFLUENCE_SPACE", "DEV")
    yield fake
    fake.close()


def run(command: str) -> int:
    return getattr(docs_sync, command)(docs_sync.Confluence())


def test_push_creates_page_and_verify_passes(wiki: FakeConfluence) -> None:
    assert run("push") == 0
    assert wiki.pages["予約のCSV出力"]["version"]["number"] == 1
    assert run("verify") == 0


def test_push_without_changes_keeps_version(wiki: FakeConfluence) -> None:
    run("push")
    run("push")
    assert wiki.pages["予約のCSV出力"]["version"]["number"] == 1


def test_changed_markdown_is_stale_until_pushed_again(wiki: FakeConfluence) -> None:
    run("push")
    spec = docs_sync.SPECS / "0001-export.md"
    spec.write_text(SPEC.replace("`owner` の順", "`owner`、`start` の順"), encoding="utf-8")
    assert run("verify") == 1
    run("push")
    assert wiki.pages["予約のCSV出力"]["version"]["number"] == 2
    assert run("verify") == 0


def test_edit_on_confluence_screen_is_detected(
    wiki: FakeConfluence, capsys: pytest.CaptureFixture[str]
) -> None:
    run("push")
    wiki.edit_on_screen("予約のCSV出力", "owner", "user")
    capsys.readouterr()
    assert run("verify") == 1
    assert "画面で編集されています" in capsys.readouterr().out
    run("push")
    assert run("verify") == 0


def test_missing_page_is_reported(wiki: FakeConfluence) -> None:
    assert run("verify") == 1
