#!/bin/bash
# 課題とモデルの組み合わせを、4本ずつ並べて実行する
#   evals/matrix.sh <ref> <label> <runs> <workroot> [モデル...]
set -u
ref=$1; label=$2; runs=$3; workroot=$4; shift 4
models=("$@"); [ ${#models[@]} -eq 0 ] && models=(haiku sonnet)
cd "$(dirname "$0")/.."
for model in "${models[@]}"; do
  for task in list-date cancel-deadline business-hours stats repeat-weekly; do
    echo "$task $model"
  done
done | xargs -P 5 -L 1 sh -c 'python3 evals/run.py --ref "$0" --label "$1-$5" --runs "$2" --workroot "$3" --task "$4" --model "$5" 2>&1 | grep -v "^$"' "$ref" "$label" "$runs" "$workroot" 
