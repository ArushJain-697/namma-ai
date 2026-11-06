import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SAMPLE = ROOT / "data" / "passages" / "rust_ordinary.txt"


def sample_passage() -> str:
    return SAMPLE.read_text()
