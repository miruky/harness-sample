# 構成

予約の決まりごとを内側に置き、保存先や画面は外側から差し込みます。

```text
src/booking/
  domain/    予約の決まりごと。標準ライブラリと domain だけを import する
  service/   予約の操作。domain を使い、保存先と時計は Protocol で受け取る
  storage/   保存先の実装（JSONファイル、メモリ）
  cli.py     入口。時計と保存先の実物を組み立てて service へ渡す
```

## 層の向き

| 層 | import してよい層 |
|:--|:--|
| domain | domain |
| service | domain、service |
| storage | domain、service、storage |
| cli | すべて |

内側の層が外側の機能を使いたいときは、`service/ports.py` に Protocol を足し、実物を `cli.py` で渡します。

## 時計

domain と service は現在時刻を直接取りません。`Clock` を引数で受け取り、テストでは `tests/conftest.py` の `FixedClock` を使います。
理由は [decisions/0002-inject-clock.md](decisions/0002-inject-clock.md) にあります。
