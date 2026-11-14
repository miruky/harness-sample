---
name: add-cli-command
description: booking のCLIにサブコマンドやオプションを足すときの手順。「コマンドを追加して」「オプションを足して」「CLIで〜できるようにして」と頼まれたら使う。
---

# CLIにコマンドやオプションを足す

入口から書き始めると、決まりごとが `cli.py` に入り込みやすい。内側から外側の順に進める。

## 手順

1. 決まりごとが増えるなら `src/booking/domain/` に書く。断る理由が増えるなら `errors.py` に `BookingError` の派生を足す。
2. 操作を `src/booking/service/booking_service.py` のメソッドにする。現在時刻が要るなら `self._clock.now()` を使う。
3. `src/booking/cli.py` に引数を足し、service を呼んで結果を表示する。`cli.py` には判定や集計を書かない。
4. テストを足す。決まりごとは `tests/test_service.py`、表示と終了コードは `tests/test_cli.py` に置く。書き方は `.claude/rules/tests.md` にある。
5. `README.md` の使い方と、`CHANGELOG.md` の「未リリース」に1行ずつ足す。
6. `make check` を通す。

## 確かめること

- 既存の予約ファイル（`bookings.json`）が、変更後もそのまま読めるか。保存する項目を変えたら `.claude/rules/storage.md` に従う。
- 断るときは終了コード1で、理由を標準エラーに日本語で出しているか。
- 複数の予約をまとめて作る操作は、1件でも断られたら1件も残していないか。
