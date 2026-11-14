# AGENTS.md

会議室予約のCLIです（Python 3.12、uv）。コードを見ても分からないことだけを、ここに書きます。

## 作業を終える前に

次の4つを通します。1つでも失敗したら、直してから完了を報告します。

```bash
uv run ruff format .
uv run ruff check .
uv run mypy
uv run pytest
```

## 決まりごと

- 返答、コミットメッセージ、コードのコメント、利用者に見せる文言は日本語で書く。
- 利用者から見える変更は、`CHANGELOG.md` の「未リリース」に1行足す。
- 現在時刻は `Clock` から受け取る。`datetime.now()` を呼んでよいのは `src/booking/cli.py` だけ。
- 層の向きは domain → service → storage / cli。内側から外側を import しない。

## 触らないもの

- `.env` は開かない。設定の名前は `.env.example` にある。
- `bookings.json` は利用者の実データ。動作を確かめるときは `BOOKING_DB` で一時ファイルを指定する。
- `uv.lock` は手で編集しない。依存を増やす前に、理由を添えて相談する。
- push、タグ付け、リリースはしない。

## もっと知りたいとき

- 構成と層の向き: `docs/architecture.md`
- 設計の判断と理由: `docs/decisions/`
