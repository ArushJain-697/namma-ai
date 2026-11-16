#!/usr/bin/env bash
# Download Sakshi's models from the GitHub release into models/ (and the misconception index into data/).
#
#   bash scripts/get_models.sh            what the device needs: GURU (4-bit), the summary model, the 2 helper
#                                         models and the index. Picks the fast or portable build for this CPU.
#   bash scripts/get_models.sh --8bit     also the 8-bit GURU (better quality, bigger)
#   bash scripts/get_models.sh --adapters also every LoRA adapter we trained (for retraining or comparison)
#   bash scripts/get_models.sh --all      everything in the release
#
# Needs curl and unzip. Files already present are skipped; model files are checked against pi/SHA256SUMS.
set -euo pipefail
cd "$(dirname "$0")/.."
REL="https://github.com/ArushJain-697/namma-ai/releases/download/guru-0.6b-v1"
mkdir -p models

# The fast summary model needs the Arm dot-product instructions (asimddp); Macs and x86 use the fast build too.
summary="qwen3-0.6b-fast"
if [ -r /proc/cpuinfo ] && grep -q "^Features" /proc/cpuinfo && ! grep -q asimddp /proc/cpuinfo; then
  summary="qwen3-0.6b-portable"
fi

want=(guru-0.6b-2job-executorch "$summary" helpers misconception-index)
for a in "$@"; do
  case "$a" in
    --8bit) want+=(guru-0.6b-2job-8bit) ;;
    --adapters) want+=(job-both job-q job-w job-w-mix qwen3-0.6b_BEST_adapter qwen3-0.6b_first-run_adapter qwen3-1.7b_adapter) ;;
    --all) want+=(guru-0.6b-2job-8bit qwen3-0.6b-fast qwen3-0.6b-portable job-both job-q job-w job-w-mix
                  qwen3-0.6b_BEST_adapter qwen3-0.6b_first-run_adapter qwen3-1.7b_adapter) ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown option: $a (try --help)"; exit 2 ;;
  esac
done

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
for name in $(printf "%s\n" "${want[@]}" | awk '!seen[$0]++'); do
  case "$name" in
    guru-0.6b-2job-executorch) dest=models; check=models/guru-0.6b-2job/model.pte ;;
    misconception-index)       dest=data/misconceptions; check=data/misconceptions/index/pte_bge-small-en-v1.5.npz ;;
    helpers)                   dest=models; check=models/helpers/nli/model.pte ;;
    job-*|qwen3-*adapter)      dest=models/adapters; check=models/adapters/$name ;;
    *)                         dest=models; check=models/$name/model.pte ;;
  esac
  if [ -e "$check" ]; then echo "have  $name"; continue; fi
  echo "get   $name"
  curl -fL --progress-bar -o "$tmp/$name.zip" "$REL/$name.zip"
  mkdir -p "$dest"
  if [ "$dest" = models/adapters ]; then
    mkdir -p "$dest/$name" && unzip -q -o "$tmp/$name.zip" -d "$dest/$name"
  else
    unzip -q -o "$tmp/$name.zip" -d "$dest"
  fi
  rm -f "$tmp/$name.zip"
done

# Verify the model files we have against the published checksums.
if command -v shasum >/dev/null; then sha="shasum -a 256"; else sha="sha256sum"; fi
bad=0
while read -r sum path; do
  [ -f "$path" ] || continue
  if [ "$($sha "$path" | cut -d' ' -f1)" = "$sum" ]; then echo "ok    $path"; else echo "BAD   $path"; bad=1; fi
done < pi/SHA256SUMS
[ "$bad" = 0 ] && echo "Models ready in models/." || { echo "A checksum did not match: delete that folder and rerun."; exit 1; }
