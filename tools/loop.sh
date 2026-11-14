#!/bin/bash
# 完了の条件が通るまで、同じ依頼を新しいセッションで渡し直す。
#   tools/loop.sh "<依頼>" "<完了の条件のコマンド>" [最大の回数]
# 条件はコマンドの終了コードで決める。エージェントの「終わりました」では止めない。
set -u
prompt=$1; done_when=$2; max=${3:-3}
for i in $(seq 1 "$max"); do
  if bash -c "$done_when" >/dev/null 2>&1; then
    echo "完了の条件を満たしました（${i}回目の前）"; exit 0
  fi
  echo "--- ${i}回目 ---"
  # 前回の続きは会話ではなく、ファイルと git の状態から拾わせる
  claude -p "$prompt 前の回の作業が残っている場合は、git status と git diff で確かめてから続けてください。" \
    --permission-mode acceptEdits --permission-prompts none --allowedTools Bash \
    --model "${LOOP_MODEL:-claude-opus-5-5}" --effort "${LOOP_EFFORT:-high}" | tail -5
done
if bash -c "$done_when" >/dev/null 2>&1; then echo "完了の条件を満たしました"; exit 0; fi
echo "${max}回で完了の条件を満たせませんでした。人の確認が必要です。"; exit 1
