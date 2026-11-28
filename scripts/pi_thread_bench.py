"""Prefill/decode speed on the board by thread count. Fixed 128 new tokens, greedy, 3 timed runs after a warm-up.

    python scripts/pi_thread_bench.py            # -> results/pi_thread_bench.json
"""
import json, os, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
MODELS = {"guru-0.6b-2job": "models/guru-0.6b-2job", "qwen3-0.6b-fast": "models/qwen3-0.6b-fast"}
PASSAGE = ("Friction is a force that acts between two surfaces in contact. It opposes relative motion. "
           "Rough surfaces produce more friction than smooth ones. Friction lets us walk and lets brakes stop a "
           "vehicle, but it also wears out machine parts and wastes energy as heat. ") * 3
PROMPT = f"<|im_start|>user\nSummarise this passage:\n{PASSAGE}<|im_end|>\n<|im_start|>assistant\n"


def vc(arg):
    try:
        return subprocess.check_output(["vcgencmd", *arg], text=True).strip()
    except OSError:
        return None


def child(name, threads):
    from sakshi.backends.executorch_backend import ExecuTorchBackend, load_kernel_libraries
    load_kernel_libraries()
    from executorch.extension.pybindings.portable_lib import _unsafe_reset_threadpool
    _unsafe_reset_threadpool(threads)
    d = ROOT / MODELS[name]
    b = ExecuTorchBackend(str(d / "model.pte"), str(d / "tokenizer.json"), eos_ids=())
    b.generate(PROMPT, max_new_tokens=16)
    runs = [b.generate(PROMPT, max_new_tokens=128) for _ in range(3)]
    rss = next(int(l.split()[1]) for l in open("/proc/self/status") if l.startswith("VmHWM"))
    print("RESULT " + json.dumps({
        "prompt_tokens": runs[0].prompt_tokens, "new_tokens": [r.new_tokens for r in runs],
        "prefill_tok_s": statistics.median(r.extra["prefill_tokens_per_s"] for r in runs),
        "decode_tok_s": statistics.median(r.tokens_per_s for r in runs),
        "peak_rss_mb": round(rss / 1024), "load_s": b.load_s}))


def main():
    out = {"board": Path("/proc/device-tree/model").read_text().strip("\0"), "throttled_before": vc(["get_throttled"]), "runs": []}
    for name in MODELS:
        for threads in (1, 2, 4):
            p = subprocess.run([sys.executable, __file__, name, str(threads)], capture_output=True, text=True)
            line = next((l for l in p.stdout.splitlines() if l.startswith("RESULT ")), None)
            r = {"model": name, "threads": threads, **(json.loads(line[7:]) if line else {"error": p.stderr[-500:]}),
                 "temp_after": vc(["measure_temp"]), "arm_clock_after": vc(["measure_clock", "arm"]),
                 "throttled_after": vc(["get_throttled"])}
            out["runs"].append(r)
            print(r, flush=True)
            time.sleep(30)
    (ROOT / "results" / "pi_thread_bench.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    child(sys.argv[1], int(sys.argv[2])) if len(sys.argv) > 2 else main()
