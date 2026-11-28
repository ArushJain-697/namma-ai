#!/usr/bin/env python3
"""Run the REAL Sakshi quiz pipeline on saved passages (no camera) and prove it runs on the Pi CPU.

  ~/sakshi-venv/bin/python ~/Sakshi/quiz_test.py passages/friction.txt --runs 3 --n 3
  options: --seed N   (pass the same seed the engine used; omit for the engine's current behaviour)
           --no-summary

For every run it prints the summary and each kept question + key, and compares runs: identical or not.
A background sampler records CPU use of this process (all 4 cores = 400%), the Pi's CPU temperature, ARM clock
and throttle flags once a second, so you can see the model is really running on the Pi.
"""
import argparse, json, os, re, subprocess, sys, threading, time

R = os.path.expanduser("~/namma-ai")
sys.path[:0] = [f"{R}/scripts", f"{R}/src"]
os.chdir(R)


def vc(*a):
    try:
        return subprocess.check_output(["vcgencmd", *a], text=True).strip()
    except Exception as e:  # noqa: BLE001
        return f"ERR {e}"


class Sampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.rows, self.stop = [], threading.Event()

    def run(self):
        pid = os.getpid()
        def cpu_ticks():
            f = open(f"/proc/{pid}/stat").read().split(")")[-1].split()
            return int(f[11]) + int(f[12])  # utime + stime
        hz = os.sysconf("SC_CLK_TCK")
        last_t, last_c = time.time(), cpu_ticks()
        while not self.stop.wait(1.0):
            t, c = time.time(), cpu_ticks()
            pct = 100.0 * (c - last_c) / hz / (t - last_t)
            last_t, last_c = t, c
            temp = float(re.search(r"([\d.]+)", vc("measure_temp")).group(1))
            clk = int(vc("measure_clock", "arm").split("=")[1]) // 1_000_000
            thr = vc("get_throttled").split("=")[1]
            self.rows.append((round(t, 1), round(pct), temp, clk, thr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("passages", nargs="+")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--n", type=int, default=3, help="questions to keep per run")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-summary", action="store_true")
    a = ap.parse_args()

    import backup_quiz as bq
    from sakshi_app import model_dirs
    from sakshi.generate import summary_in_parts
    qd, sd = model_dirs(False)
    print(f"quiz model : {qd}\ncheck model: {sd}", flush=True)
    t = time.time()
    m, sm = bq.Model(qd), bq.Model(sd)
    print(f"loaded in {time.time()-t:.1f}s; backend temperature default = "
          f"{bq.Model.run.__defaults__}", flush=True)

    s = Sampler(); s.start()
    summary = {}
    for p in a.passages:
        path = p if os.path.isabs(p) else next((c for c in (os.path.join(os.path.expanduser(d), p) for d in ("~/passages", "~/Sakshi")) if os.path.exists(c)), p)
        passage = " ".join(open(path).read().split())
        runs = []
        for r in range(a.runs):
            t0 = time.time()
            summ = ""
            if not a.no_summary:
                summ = summary_in_parts(sm.run, passage, bq.split_sentences, bq.SUM_PART_SYSTEM,
                                        bq.SUM_PART_EXAMPLES).get("text", "")
            t_sum = time.time() - t0
            res = bq.quiz_2job(m, m, passage, n=a.n, checker=sm, seed=a.seed, min_keep=a.n)
            qs = [(k["q"], k["options"][k["answer"]], "ABCD"[k["answer"]]) for k in res["kept"]]
            runs.append({"summary": summ, "qs": qs})
            print(f"\n--- {os.path.basename(path)} run {r+1}: summary {t_sum:.0f}s, quiz {time.time()-t0-t_sum:.0f}s, "
                  f"kept {len(qs)}, dropped {len(res['rejected'])}", flush=True)
            print("SUMMARY:", summ)
            for q, key, letter in qs:
                print(f"  Q: {q}\n     key[{letter}]: {key}")
        qsets = [tuple(x[0] for x in r_["qs"]) for r_ in runs]
        keys = [tuple(x[1] for x in r_["qs"]) for r_ in runs]
        sums = [r_["summary"] for r_ in runs]
        allq = [q for r_ in runs for q, _, _ in r_["qs"]]
        summary[os.path.basename(path)] = {
            "runs": a.runs,
            "identical_question_sets": len(set(qsets)) == 1,
            "identical_answer_sets": len(set(keys)) == 1,
            "identical_summaries": len(set(sums)) == 1,
            "distinct_questions_total": len(set(allq)), "questions_total": len(allq)}
    s.stop.set(); s.join()

    print("\n=========== REPEATABILITY ===========")
    print(json.dumps(summary, indent=1))
    rows = s.rows
    if rows:
        cpu = [r[1] for r in rows]; tmp = [r[2] for r in rows]; clk = [r[3] for r in rows]
        print("\n=========== HARDWARE (sampled 1/s while generating) ===========")
        print(f"samples={len(rows)}  python-process CPU%: avg {sum(cpu)/len(cpu):.0f}  peak {max(cpu)}  (400 = all 4 cores)")
        print(f"CPU temp C: start {tmp[0]}  max {max(tmp)}  end {tmp[-1]}")
        print(f"ARM clock MHz: min {min(clk)}  max {max(clk)}")
        print(f"throttle flags seen: {sorted(set(r[4] for r in rows))}  (0x0 = never throttled / under-voltage)")
        print(f"arch: {os.uname().machine}; model device: CPU (ExecuTorch XNNPACK, no GPU on a Pi)")


if __name__ == "__main__":
    main()
