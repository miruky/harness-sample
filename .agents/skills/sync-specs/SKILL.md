---
name: sync-specs
description: docs/specs/ の仕様を Confluence へ書き込み、写しが一致しているかを確かめる。「仕様を Confluence に反映して」「Confluence と合っているか確かめて」と頼まれたとき、終了前のフックに未反映を指摘されたときに使う。
---

# 仕様を Confluence へ書き込み、一致を確かめる

元は `docs/specs/` の Markdown で、Confluence は写し。ページの取得と書き込みはMCPのツール（atlassian）で行う。
ページの全文を取得すると、その文字が全部コンテキストに入る。取得は、下の順で必要になったときだけ行う。

## 書き込む

1. `uv run python tools/specs_sync.py status` を実行する。挙がったファイルだけが対象。0件ならここで終わる。
2. 対象のファイルごとに `uv run python tools/specs_sync.py payload <ファイル>` を実行し、出力をそのまま本文にする。自分で書き直さない。
3. 台帳（`docs/specs/` の `.sync.json`）にページIDがあれば `updateConfluenceContent`、なければ `createConfluenceContent` で書き込む。題名は Markdown の1行目の見出し。ページを探すための検索はしない。
4. 返ってきたページIDと版を `uv run python tools/specs_sync.py record <ファイル> <ページID> <版>` で記録する。

## 一致を確かめる

1. `listConfluenceContentVersions` で、ページのいちばん新しい版の番号だけを取得する。本文は取得しない。
2. `uv run python tools/specs_sync.py check <ファイル> <版>` を実行する。「一致」と出たら、そのファイルは終わり。
3. 版が進んでいたときだけ、`diffConfluenceContentVersions` で、台帳の版といまの版の差分を取得する。全文は取得しない。
4. 差分の内容を人に報告する。元は Markdown なので、指示がなければ「書き込む」の手順でページを書き直す。画面での変更を残すと決まったら、先に Markdown へ写す。

## してはいけないこと

- 確認のために、全ページを `getConfluenceContent` で取得する
- 台帳と一致しているファイルを書き込み直す
- `payload` の出力を要約したり、整形し直したりしてから書き込む
