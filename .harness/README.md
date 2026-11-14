# .harness

フックが実行のたびに残す記録の置き場所です。`logs/` は共有しません（`.gitignore` の対象）。

```bash
uv run python tools/harness_stats.py   # どのフックが何回止めたかを数える
```
