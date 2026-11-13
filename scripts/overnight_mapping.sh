#!/usr/bin/env bash
# Second overnight chain: misconception-mapping upgrades, run after scripts/overnight.sh has finished.
#   bash scripts/overnight_mapping.sh      (log: results/overnight_mapping.log)
set -u
cd "$(dirname "$0")/.."
LOG=results/overnight_mapping.log
say() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }
ML=.venv-ml/bin/python
quiet() { grep -vE "Warning|warn|W11|regex|Loading|cpuinfo|^\s*$"; }

say "waiting for the data pipeline (results/overnight.log: '7/7 done')"
until grep -q "7/7 done" results/overnight.log 2>/dev/null; do sleep 120; done

say "== 1/6 fine-tune the retriever on teacher-labelled pairs (Eedi recipe)"
$ML train/finetune_retriever.py 2>&1 | quiet | tail -5 | tee -a "$LOG"
say "== 2/6 learn fusion weights (base and fine-tuned retriever) on training items"
$ML scripts/eval_mapping.py --fit 2>&1 | quiet | tail -5 | tee -a "$LOG"
say "== 3/6 compare mapping methods on test items -> results/mapping/"
$ML scripts/eval_mapping.py --limit 800 2>&1 | quiet | tail -12 | tee -a "$LOG"

say "== 4/6 export the best retriever to ExecuTorch for the device"
if [ -d models/retriever-finetuned ] && python3 - <<'EOF'
import json, sys
r = {x["method"]: x for x in json.load(open("results/mapping/mapping_results.json"))}
ft, base = r.get("finetuned retriever + learned"), r.get("learned") or r.get("full (+NLI)")
sys.exit(0 if ft and base and ft["MAP@25"] > base["MAP@25"] else 1)
EOF
then
  say "fine-tuned retriever wins: exporting it"
  cp models/helpers/embed/meta.json models/helpers/embed/meta.base.json 2>/dev/null
  $ML scripts/export_helpers.py --embed models/retriever-finetuned --only embed 2>&1 | quiet | tail -3 | tee -a "$LOG"
  cp data/misconceptions/index/weights_finetuned.json data/misconceptions/index/weights.json
else
  say "keeping the base retriever (fine-tuned did not win, or is missing)"
fi

say "== 5/6 smoke check: plain Qwen3-0.6B with the new mapper on 40 test passages (the full 200 run is for the fine-tuned model)"
PYTHONPATH=src $ML scripts/eval_diagnostic.py --limit 40 --out results/eval_diag_base_mapper --mapper pte --backend executorch \
  --model models/qwen3-0.6b-8da4w/model.pte --tokenizer models/qwen3-0.6b-8da4w-portable/tokenizer.json 2>/dev/null \
  | tail -20 | tee -a "$LOG"
say "== 6/6 done"
