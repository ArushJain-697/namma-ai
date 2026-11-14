#!/usr/bin/env bash
# Pi day kit: offline install of the whole project. Run ON the Pi, from inside the kit folder:
#   bash install.sh            (log: install.log next to this script)
# Needs no internet. Takes ~5-10 minutes. Safe to run again.
set -u -o pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
LOG="$KIT/install.log"
exec > >(tee "$LOG") 2>&1
VENV="$HOME/sakshi-venv"
REPO="$HOME/namma-ai"
ok()   { echo "  OK   $*"; }
bad()  { echo "  FAIL $*"; echo; echo ">>> See CHECKLIST.md, section for this step. Log: $LOG"; exit 1; }
step() { echo; echo "== $*"; }

step "1/7 What machine is this?"
MODEL="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo unknown)"
ARCH="$(uname -m)"; CORES="$(nproc)"
PYV="$(python3 -c 'import sys; print(f"{sys.version_info[0]}{sys.version_info[1]}")' 2>/dev/null || echo none)"
DOTPROD=no; grep -q -m1 asimddp /proc/cpuinfo && DOTPROD=yes
echo "  board: $MODEL | arch: $ARCH | cores: $CORES | python: $PYV | dot-product CPU: $DOTPROD"
free -m | sed -n 2p | awk '{print "  RAM total MB: "$2", free MB: "$7}'
df -h "$HOME" | tail -1 | awk '{print "  disk free in home: "$4}'
[ "$ARCH" = "aarch64" ] || bad "not a 64-bit ARM OS (arch $ARCH). Needs 64-bit Raspberry Pi OS."
[ "$PYV" != "none" ] || bad "python3 not found"
WHEELS="$KIT/wheels/py$PYV"
[ -d "$WHEELS" ] || bad "no packages for Python $PYV in the kit (have: $(ls "$KIT/wheels"))"
ok "packages for Python $PYV found"

step "2/7 Python environment at $VENV"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv --without-pip "$VENV" || bad "could not create venv"
fi
PY="$VENV/bin/python"
if ! "$PY" -m pip --version >/dev/null 2>&1; then
  PIPW="$(ls "$WHEELS"/pip-*.whl | head -1)"
  "$PY" "$PIPW/pip" install -q --no-index --find-links "$WHEELS" pip || bad "could not install pip from the kit"
fi
ok "venv + pip ready"

step "3/7 Install ExecuTorch, torch (CPU) and helpers, offline"
"$PY" -m pip install -q --no-index --find-links "$WHEELS" --no-deps executorch==1.5.1 || bad "executorch install"
"$PY" -m pip install -q --no-index --find-links "$WHEELS" --no-deps "torch==2.14.1+cpu" || bad "torch install"
"$PY" -m pip install -q --no-index --find-links "$WHEELS" numpy tqdm typing_extensions pytest pyyaml packaging \
  flatbuffers pytorch-tokenizers tokenizers fsrs filelock sympy networkx jinja2 fsspec setuptools || bad "other packages"
# the general ExecuTorch runtime (used by the two helper models that link wrong answers to misconceptions)
# imports these two small pure-Python packages; missing on the Pi on 14 Nov until installed
"$PY" -m pip install -q --no-index --find-links "$WHEELS" ruamel.yaml tabulate 2>/dev/null \
  || "$PY" -m pip install -q ruamel.yaml tabulate || bad "ruamel.yaml / tabulate"
ok "installed ($(du -sh "$VENV" | cut -f1))"

step "4/7 Can ExecuTorch's LLM runner load?"
"$PY" -c "from executorch.extension.llm.runner import TextLLMRunner, GenerationConfig; print('  runner import OK')" \
  2>&1 | grep -v "^I tokenizers" || bad "runner import failed"

step "5/7 Project code at $REPO"
mkdir -p "$REPO" && tar -xmf "$KIT/namma-ai.tar" -C "$REPO" 2>/dev/null || bad "could not unpack namma-ai.tar"
mkdir -p "$REPO/models"
ln -sfn "$KIT/models/qwen3-0.6b-fast" "$REPO/models/qwen3-0.6b-fast"
ln -sfn "$KIT/models/qwen3-0.6b-portable" "$REPO/models/qwen3-0.6b-portable"
ln -sfn "$KIT/models/helpers" "$REPO/models/helpers"
for m in guru-0.6b-2job guru-0.6b-2job-8bit; do [ -d "$KIT/models/$m" ] && ln -sfn "$KIT/models/$m" "$REPO/models/$m"; done
ok "code unpacked, models linked"

step "6/7 Check model files are intact"
( cd "$KIT" && shasum -a 256 -c models/SHA256SUMS 2>/dev/null || sha256sum -c models/SHA256SUMS ) | sed 's/^/  /' \
  || bad "a model file is corrupted: copy the kit again"
if [ "$DOTPROD" = "yes" ]; then CHOSEN=qwen3-0.6b-fast; else CHOSEN=qwen3-0.6b-portable; fi
echo "MODEL_DIR=$REPO/models/$CHOSEN" > "$REPO/.kit_model"
ok "will use $CHOSEN (dot-product CPU: $DOTPROD)"

step "7/7 Project self-test (no model, ~30 s on a Pi 5)"
( cd "$REPO" && "$PY" -m pytest -q -p no:cacheprovider --ignore=tests/test_resident.py 2>&1 | tail -2 | sed 's/^/  /' )

echo; echo "INSTALL DONE. Next:  bash $KIT/test.sh"
