# harness-sample

AIのコーディングエージェントが働くためのハーネス一式を、小さなリポジトリに入れた見本です。
題材は会議室予約のCLI（`booking`）で、Claude Code と Codex の両方から同じ決まりで作業できるようにしてあります。

解説記事: （公開後に追記）

## 入っているもの

| 置き場所 | 何をするか | 使うツール |
|:--|:--|:--|
| `AGENTS.md` | コードから読み取れない決まりごとの目次 | Claude Code、Codex ほか |
| `CLAUDE.md` | `AGENTS.md` の取り込みと、Claude Code だけの補足 | Claude Code |
| `.claude/rules/` | 特定のフォルダを触るときだけ読み込む決まり | Claude Code |
| `.agents/skills/` | 手順書（スキル）。`.claude/skills` はここへのリンク | Claude Code、Codex |
| `.claude/agents/`、`.codex/agents/` | 変更を別の文脈で見直すレビュー役 | Claude Code、Codex |
| `.agents/hooks/` | 実行前に止める、編集後に検査する、終了前に確かめるフック | Claude Code、Codex |
| `.claude/settings.json` | 権限（allow、ask、deny）、フックの登録、返答の言語 | Claude Code |
| `.codex/config.toml`、`.codex/hooks.json` | サンドボックスと承認の既定、フックの登録 | Codex |
| `Makefile`、`tools/check_layers.py` | 整形、リント、型、層の向き、テストを1本で確かめる | 人、エージェント、CI |
| `tools/check_harness.py` | 指示ファイルや設定が古くなっていないかの検査 | CI |
| `tools/harness_stats.py` | フックが止めた回数の集計 | 人 |
| `.github/workflows/ci.yml` | `make check` とハーネスの検査 | GitHub Actions |
| `docs/architecture.md`、`docs/decisions/` | 構成と、設計の判断の理由 | 人、エージェント |
| `docs/plans/` | 長い作業の計画と進み具合 | 人、エージェント |
| `docs/harness-log.md` | 失敗をハーネスへ戻した記録 | 人 |
| `evals/` | ハーネスを変えたときに測り直すための評価 | 人 |

## 動かす

```bash
uv sync        # 依存を入れる
make check     # 整形、リント、型、層の向き、テスト
```

```bash
uv run booking add --room A --owner miruky --start 2026-12-01T10:00 --end 2026-12-01T11:00
uv run booking list
uv run booking cancel <予約ID>
```

予約は `bookings.json` に保存されます。保存先は環境変数 `BOOKING_DB` で変えられます。

## エージェントと使う

```bash
claude         # Claude Code。AGENTS.md、スキル、フック、権限の設定が読み込まれる
codex          # Codex。AGENTS.md、スキル、.codex/ の設定が読み込まれる
```

Codex のフックは、初回に `/hooks` で内容を確かめて信頼すると動きます。

## 育てた順番

ハーネスは一度に作らず、エージェントを走らせて起きたことを1件ずつ戻しました。各時点はタグで残してあります。

| タグ | 足したもの |
|:--|:--|
| `stage-0` | 予約CLI、テスト、ruff、mypy だけ |
| `stage-1` | `AGENTS.md` と `docs/` |
| `stage-2` | 検査（`make check`、層の向き）、フック、権限の設定、CI |
| `stage-3` | スキル、場所ごとのルール、レビュー役、Codex の設定、評価 |

経緯は `docs/harness-log.md`、各時点で同じ課題を解かせた結果は `evals/results/` にあります。

## 動作を確かめた範囲

- Claude Code 2.1.321（Claude Opus 5.5）と Codex CLI 0.166.0（GPT-6 Astra）で、指示ファイル、スキル、フックが働くことを確かめました。
- Cursor と GitHub Copilot は `AGENTS.md` を読み込みますが、このリポジトリでは実機で確かめていません。

## ライセンス

MIT
