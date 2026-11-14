# booking

会議室予約のCLIです。

## セットアップ

```bash
uv sync
```

## 使い方

```bash
uv run booking add --room A --owner miruky --start 2026-12-01T10:00 --end 2026-12-01T11:00
uv run booking list
uv run booking cancel <予約ID>
```

予約は `bookings.json` に保存されます。保存先は環境変数 `BOOKING_DB` で変えられます。

## 開発

```bash
make check    # 整形、リント、型、層の向き、テスト
make format   # 整形と、自動で直せるリントの修正
```
