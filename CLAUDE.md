@AGENTS.md

## Claude Code で使うもの

- 決まった手順のある作業はスキルを使う。CLIに機能を足すときは `/add-cli-command`、設計の判断を残すときは `/write-adr`。
- 実装が終わって `make check` が通ったら、コミットの前に `reviewer` サブエージェントへ見直しを頼む。
- 失敗の振り返りは、人が `/harness-retro` で始める。自分からは始めない。
