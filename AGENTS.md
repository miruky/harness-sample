# AGENTS.md

会議室予約のCLIです（Python 3.12、uv）。コードを見ても分からないことだけを、ここに書きます。

## 作業を終える前に

`make check` を通します。整形、リント、型、層の向き、テストをまとめて確かめる1本で、CIも同じものを実行します。
失敗したら出力に直し方が出るので、直してから完了を報告します。

```bash
make check                                  # 全部
make format                                 # 整形と、自動で直せるリントの修正
uv run pytest tests/test_service.py -k 名前  # テストを1件だけ
```

## 決まりごと

- 返答、コミットメッセージ、コードのコメント、利用者に見せる文言は日本語で書く。
- 利用者から見える変更は、`CHANGELOG.md` の「未リリース」に1行足す。
- 現在時刻は `Clock` から受け取る。`datetime.now()` を呼んでよいのは `src/booking/cli.py` だけ。
- 層の向きは domain → service → storage / cli。内側から外側を import しない（`tools/check_layers.py` が検査する）。

## 触らないもの

- `.env` は開かない。設定の名前は `.env.example` にある。
- `bookings.json` は利用者の実データ。動作を確かめるときは `BOOKING_DB` で一時ファイルを指定する。
- `uv.lock` は手で編集しない。依存を増やす前に、理由を添えて相談する。
- push、タグ付け、リリースはしない。

## もっと知りたいとき

- 構成と層の向き: `docs/architecture.md`
- 設計の判断と理由: `docs/decisions/`
