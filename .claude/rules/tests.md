---
paths:
  - "tests/**/*.py"
---

# テストの決まり

- 時刻は `tests/conftest.py` の `at()` と `FixedClock` で作る。`datetime.now()` と実際の日付に頼らない。
- 1つのテストで確かめる振る舞いは1つ。名前は `test_<条件>_<結果>` の形で、読めば仕様が分かるようにする。
- 予約の決まりは service のテストで確かめる。CLIのテストは、表示と終了コードだけを見る。
- 保存先は `InMemoryRepository` か `tmp_path` を使う。リポジトリ直下の `bookings.json` に触れない。
