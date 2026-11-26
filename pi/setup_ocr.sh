#!/usr/bin/env bash
# Better page reading on the device. Run ON the Pi, once (a minute or two; works offline with pi/ocr-wheels/):
#   bash pi/setup_ocr.sh            (WITH_VL=1 also installs PaddleOCR-VL: ~30 min per page on a Pi 5 CPU,
#                                    so only for a board with a GPU/NPU; the device keeps it off by default)
#
#  1. RapidOCR >= 3.10 in the screen app's Python (~/venv): PaddleOCR's PP-OCRv6 line models. The small model (the
#     device default) ships inside the package; medium is fetched only if there is internet (optional).
#  2-3. Only with WITH_VL=1: llama.cpp's llama-server built for this CPU + PaddleOCR-VL-1.5 (0.9B, Apache-2.0,
#     official PaddlePaddle GGUF, 1.8 GB) into ~/models/paddleocr-vl.
#  4. Copies sakshi.py + page_ocr.py + paddle_vl.py to the screen app (~/Sakshi), then times a read on this board.
# Every step is skipped when already done. Log: ~/setup_ocr.log
set -u -o pipefail
exec > >(tee "$HOME/setup_ocr.log") 2>&1
HERE="$(cd "$(dirname "$0")" && pwd)"
UIPY="${UIPY:-$HOME/venv/bin/python}"
APP="${APP:-$HOME/Sakshi}"
LLAMA="$HOME/llama.cpp"
VLDIR="$HOME/models/paddleocr-vl"
HF="https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5-GGUF/resolve/main"
ok()   { echo "  OK   $*"; }
bad()  { echo "  FAIL $*"; exit 1; }
step() { echo; echo "== $*"; }

step "1/4 PP-OCRv6 line models in $UIPY"
[ -x "$UIPY" ] || bad "no Python at $UIPY (set UIPY=/path/to/python)"
# Offline first when the kit has the wheel (made on a laptop: pip download rapidocr==3.10.0 colorlog omegaconf six
# tqdm --no-deps -d pi/ocr-wheels). The PP-OCRv6 small models are inside the wheel. --no-deps is the fallback because
# rapidocr 3.10 names opencv-python-headless while the camera venv may have opencv-python (same cv2); the model
# check below proves the result works.
if ls "$HERE"/ocr-wheels/rapidocr-*.whl >/dev/null 2>&1 \
   && { "$UIPY" -m pip install -q --no-index --find-links "$HERE/ocr-wheels" "rapidocr>=3.10" 2>/dev/null \
        || "$UIPY" -m pip install -q --no-index --no-deps "$HERE"/ocr-wheels/*.whl; }; then
  ok "rapidocr from pi/ocr-wheels (offline)"
else
  "$UIPY" -m pip install -q -U "rapidocr>=3.10" onnxruntime || bad "pip install rapidocr (needs internet or pi/ocr-wheels/)"
fi
"$UIPY" - <<'EOF' || bad "PP-OCRv6 models"
from rapidocr import ModelType, OCRVersion, RapidOCR
for t in ("SMALL", "MEDIUM"):
    m = getattr(ModelType, t)
    try:
        RapidOCR(params={"Det.ocr_version": OCRVersion.PPOCRV6, "Rec.ocr_version": OCRVersion.PPOCRV6,
                         "Det.model_type": m, "Rec.model_type": m, "Global.log_level": "error"})
        print("  PP-OCRv6", t.lower(), "ready")
    except Exception as e:  # medium needs a one-time download; small is inside the package
        if t == "SMALL":
            raise
        print("  PP-OCRv6 medium skipped (no internet?); small is the default anyway")
EOF
ok "line models"

if [ "${WITH_VL:-0}" = "1" ]; then
  step "2/4 llama-server (llama.cpp, CPU build)"
  if [ -x "$LLAMA/build/bin/llama-server" ]; then
    ok "already built"
  else
    command -v cmake >/dev/null && command -v g++ >/dev/null && command -v git >/dev/null \
      || sudo apt-get install -y cmake build-essential git || bad "needs cmake, g++ and git"
    [ -d "$LLAMA" ] || git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LLAMA" || bad "git clone"
    cmake -S "$LLAMA" -B "$LLAMA/build" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF \
      -DGGML_NATIVE=ON >/dev/null || bad "cmake configure"
    cmake --build "$LLAMA/build" -j"$(nproc)" --target llama-server || bad "build"
    ok "built $LLAMA/build/bin/llama-server"
  fi

  step "3/4 PaddleOCR-VL-1.5 model files"
  mkdir -p "$VLDIR"
  for f in PaddleOCR-VL-1.5.gguf PaddleOCR-VL-1.5-mmproj.gguf; do
    curl -fL -C - --retry 3 -o "$VLDIR/$f" "$HF/$f" || bad "download $f"
  done
  ls -la "$VLDIR" | sed 's/^/  /'
  ok "model in $VLDIR"
fi

step "4/4 screen app files, then a timed read of pi/ocr_sample.jpg on this board"
mkdir -p "$APP"
[ -f "$APP/sakshi.py" ] && cp "$APP/sakshi.py" "$APP/sakshi.py.before-ocr-$(date +%Y%m%d-%H%M%S)"
cp "$HERE/ui/page_ocr.py" "$HERE/ui/paddle_vl.py" "$HERE/ui/sakshi.py" "$APP/" \
  && ok "copied to $APP (the old sakshi.py is kept as sakshi.py.before-ocr-*)"
cd "$APP" && SAKSHI_LLAMA_SERVER="$LLAMA/build/bin/llama-server" SAMPLE="$HERE/ocr_sample.jpg" \
  TRUTH="$HERE/ocr_sample.txt" "$UIPY" - <<'EOF'
# One simulated webcam photo (half a page, slightly blurred) from scripts/ocr_bench.py, timed on THIS board.
import os, re, time, cv2, page_ocr, paddle_vl
from rapidocr import ModelType, OCRVersion, RapidOCR
img, truth = cv2.imread(os.environ["SAMPLE"]), open(os.environ["TRUTH"]).read()
words = lambda s: re.findall(r"[a-z0-9]+", s.lower())
def wrong(text):  # share of the true words missing from the read (rough, order-free)
    got = set(words(text)); w = words(truth)
    return sum(x not in got for x in w) / len(w)
for t in ("SMALL", "MEDIUM"):
    m = getattr(ModelType, t)
    try:
        eng = RapidOCR(params={"Det.ocr_version": OCRVersion.PPOCRV6, "Rec.ocr_version": OCRVersion.PPOCRV6,
                               "Det.model_type": m, "Rec.model_type": m, "Global.log_level": "error"})
    except Exception:
        continue
    eng(img)                                    # warm-up
    t0 = time.time(); text, info = page_ocr.read_page(eng, img); dt = time.time() - t0
    print(f"  PP-OCRv6 {t.lower():6s} {dt:5.1f} s  conf {info['conf']:.3f}  {info['words']} words  "
          f"~{100 * wrong(text):.0f}% of true words missed")
vl = paddle_vl.VLServer()
if vl.available():
    t0 = time.time(); vl.start(); print(f"  PaddleOCR-VL loaded in {time.time() - t0:.1f} s")
    box = page_ocr.text_region(eng(img), img.shape)
    t0 = time.time(); text = paddle_vl.to_text(vl.read(img, box=box)); dt = time.time() - t0
    print(f"  PaddleOCR-VL    {dt:5.1f} s  ~{100 * wrong(text):.0f}% of true words missed")
    vl.stop()
else:
    print("  PaddleOCR-VL not installed (fine: the line model alone is used)")
print("  The device uses v6 small (fewest errors in our bench); SAKSHI_OCR=v6m in ~/start_sakshi.sh switches.")
EOF
echo; echo "DONE. Start the device as before: ~/start_sakshi.sh"
