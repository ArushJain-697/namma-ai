#!/usr/bin/env bash
# Run ON the Raspberry Pi, from the repo root:   bash scripts/pi_setup.sh
# Checks the machine, builds a venv, installs the ExecuTorch runner, runs the tests.
# Needs the internet ONCE (to install). Does not need the model yet.
# Everything printed is also saved to results/pi_setup.log: paste that file back.
set -u
cd "$(dirname "$0")/.."
mkdir -p results
exec > >(tee results/pi_setup.log) 2>&1

VENV="${VENV:-$HOME/sakshi-venv}"
sec() { printf '\n== %s\n' "$1"; }

sec "machine"
[ -r /proc/device-tree/model ] && { tr -d '\0' < /proc/device-tree/model; echo; }
uname -a
grep PRETTY_NAME /etc/os-release
echo "arch: $(uname -m)   cores: $(nproc)"
python3 --version
free -m | sed -n 1,2p
df -h . | tail -1
echo "glibc: $(ldd --version 2>&1 | head -1)"
if grep -q -m1 asimddp /proc/cpuinfo; then echo "asimddp (dot-product): present"; else echo "asimddp (dot-product): NOT FOUND"; fi
if grep -q -m1 i8mm /proc/cpuinfo; then echo "i8mm: present"; else echo "i8mm: absent (expected on a Pi 5; dot-product kernels will be used)"; fi
if command -v vcgencmd >/dev/null; then
  vcgencmd measure_temp; vcgencmd get_throttled; vcgencmd get_config arm_freq
else
  echo "vcgencmd: not found (is this a Raspberry Pi?)"
fi
[ "$(uname -m)" = "aarch64" ] || echo "WARNING: not aarch64. The ExecuTorch wheel needs 64-bit Raspberry Pi OS (Trixie)."

sec "venv at $VENV"
python3 -m venv "$VENV" || { echo "venv failed (try: sudo apt install python3-venv)"; exit 1; }
PY="$VENV/bin/python"; PIP="$VENV/bin/pip"
"$PIP" install --quiet --upgrade pip

check_import() {
  "$PY" - <<'EOF'
import time
t = time.time()
from executorch.extension.llm.runner import TextLLMRunner, GenerationConfig  # noqa: F401
print("runner import OK in %.1fs" % (time.time() - t))
EOF
}

sec "install (slim first: executorch has no dependency on pandas, scikit-learn, scipy or coremltools for the runner)"
"$PIP" install --no-deps executorch==1.5.1 && "$PIP" install torch numpy tqdm typing_extensions pytest
if check_import; then
  echo "slim install works"
else
  echo "slim install did not import; falling back to the full dependency set (bigger and slower)"
  "$PIP" install executorch==1.5.1 torch pytest
  check_import || { echo "RUNNER IMPORT FAILED. Paste this log back; do not continue."; exit 1; }
fi
"$PIP" list 2>/dev/null | grep -i -E '^(executorch|torch|numpy) '
echo "venv size: $(du -sh "$VENV" | cut -f1)"

sec "project self-check (stub model only, proves the pipeline logic on this machine)"
PYTHON="$PY" bash scripts/selfcheck.sh

sec "done"
echo "Next: copy the .pte and tokenizer onto the Pi, then:"
echo "  $PY scripts/pi_smoke.py --model /path/to/model.pte --tokenizer /path/to/tokenizer.model"
echo "Paste results/pi_setup.log back to me."
