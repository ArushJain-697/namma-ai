"""Command line: python -m sakshi {check,prepare,study,report}.

  run PASSAGE              everything the brief asks for: summary, quiz and run card on one screen
  check PASSAGE            is this passage usable (150-300 words)?
  prepare PASSAGE --out R  run the pipeline, save the run, print the run card
  study R                  the student quiz (no model needed: it plays a prepared run)
  report R                 tiers, witnesses, reasons and the run card (for teachers and judges)
  learn BANK               adaptive quiz with misconception diagnosis and a revision schedule
  plan BANK                the revision plan from the saved learner state
  simulate BANK            fast-forward N days and compare recall with and without revision
"""
from __future__ import annotations

import argparse
import os
import sys

from .backends.factory import add_backend_args, build_backend
from .gate import check_passage
from .metrics import run_card, write_metrics
from .pipeline import Run, prepare
from .quiz import Session


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_check(args) -> int:
    g = check_passage(_read(args.passage), override=args.gate_override)
    print(g.reason)
    return 0 if g.ok else 1


def cmd_prepare(args) -> int:
    run = prepare(_read(args.passage), build_backend(args), n_items=args.n_items, gate_override=args.gate_override)
    print(run.gate["reason"])
    if not run.items and not run.gate.get("status") == "OK":
        return 1
    run.save(args.out)
    if args.metrics:
        write_metrics(run, args.metrics)
    c = run.counts
    print(f"Saved {args.out}: {c['green']} green, {c['amber']} amber, {c['red']} red, {c['fallback']} fallback")
    print()
    print(run_card(run))
    return 0


def print_deliverable(run, out=print) -> int:
    """The brief's deliverables 2-4 on one screen: summary, at least three questions, and the run card."""
    from .pipeline import visible_items
    rule = "=" * 72
    out(rule)
    out(f"PASSAGE   {run.gate['reason']}")
    out(rule)
    s = run.summary or {}
    out("\nSUMMARY")
    out(s.get("text") or "(no summary)")
    items = visible_items(run)
    withheld = len(run.items) - len(items)
    out(f"\nQUIZ  ({len(items)} questions" + (f"; {withheld} more held back by the checks" if withheld else "") + ")")
    for n, it in enumerate(items, 1):
        tag = "  [fill-in-the-blank, built by code]" if it.fallback else ""
        out(f"\nQ{n}. {it.stem}{tag}")
        if it.options:
            for letter, opt in zip("ABCDEFG", it.options):
                out(f"     {letter}) {opt}")
            right = next((letter for letter, opt in zip("ABCDEFG", it.options) if opt == it.key), "?")
            out(f"     Answer: {right}) {it.key}")
        else:
            out(f"     Answer: {it.key}")
        out(f"     From the passage, sentence {it.witness_idx + 1}: \"{it.witness}\"")
    out("\n" + rule)
    out("RUN CARD   (model ran on this device through ExecuTorch; no cloud call anywhere)" if run.backend.get("name", "").startswith("executorch")
        else f"RUN CARD   (backend: {run.backend.get('name')}; NOT a real model, numbers are not results)")
    out(rule)
    out(run_card(run))
    return 0 if len(items) >= 3 else 1


def cmd_run(args) -> int:
    """prepare + print everything the brief asks for, in one go."""
    run = prepare(_read(args.passage), build_backend(args), n_items=args.n_items, gate_override=args.gate_override)
    if not run.items:
        print(run.gate["reason"])
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    run.save(args.out)
    write_metrics(run, args.metrics or os.path.splitext(args.out)[0] + "_metrics.json")
    code = print_deliverable(run)
    print(f"\nSaved the run to {args.out} (replay the quiz with:  python -m sakshi study {args.out})")
    return code


def cmd_study(args) -> int:
    run = Run.load(args.run)
    Session(run, include_amber=args.include_amber, summary_first=args.summary_first).run_quiz()
    return 0


def cmd_report(args) -> int:
    run = Run.load(args.run)
    print("Draft: checked by rules, not by a person.\n")
    print(f"Passage: {run.gate['reason']}")
    s = run.summary
    if s:
        print("\nSummary (each sentence comes from a passage sentence):")
        for x in s["sentences"]:
            tag = " [FALLBACK: original sentence]" if x["fallback"] else ""
            print(f"  [sentence {x['src_idx'] + 1}]{tag} {x['text']}")
            for why in x["reasons"]:
                print(f"      note: {why}")
        for c in s["checks"]:
            if not c["passed"]:
                print(f"  summary check failed: {c['name']}: {c['detail']}")
    print("\nQuestions:")
    for it in run.items:
        flag = " [FALLBACK cloze]" if it.fallback else ""
        print(f"\n  #{it.id} {it.tier}{flag}  witness: sentence {it.witness_idx + 1}")
        if it.tier == "RED":
            print("      WITHHELD from students. Reasons:")
            for why in it.reasons:
                print(f"        - {why}")
            continue
        print(f"      Q: {it.stem}")
        if it.options:
            print("      options: " + " | ".join(it.options))
        print(f"      answer: {it.key}")
        print(f'      witness: "{it.witness}"')
        for why in it.reasons:
            print(f"      look closer: {why}")
    print("\n" + run_card(run))
    return 0


def cmd_resident(args) -> int:
    from .resident import ResidentServer
    if not args.socket:
        sys.exit("resident needs --socket PATH")
    if args.backend == "resident":
        sys.exit("a resident process holds a real or stub model; --backend resident would point it at itself")
    srv = ResidentServer(build_backend(args), args.socket)
    srv.start()
    print(f"ready: resident model process on {args.socket} (pid {__import__('os').getpid()})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.close()
    return 0


def cmd_serve(args) -> int:
    from .serve import make_server
    run = Run.load(args.run)
    srv, counts = make_server(run, args.host, args.port, args.include_amber)
    print(f"Serving the quiz on port {args.port}. Phones on this machine's Wi-Fi open  http://<this machine's address>:{args.port}/", flush=True)
    print("Room view (anonymous counts, in memory only):  /room", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


def cmd_villain(args) -> int:
    import json
    from .villain import render
    with open(args.file, encoding="utf-8") as f:
        print(render(json.load(f)))
    return 0


def cmd_probe(args) -> int:
    import json
    from .resident import ResidentClient
    c = ResidentClient(args.socket)
    print(json.dumps(c.probe_network(), indent=2))
    c.close()
    return 0


def cmd_edit(args) -> int:
    from .regen import edit, item_sentences, render_report, replace_sentence
    run = Run.load(args.run)
    if args.list:
        for idx in sorted(item_sentences(run)):
            print(f"sentence {idx + 1} has a question: {run.passage and __import__('sakshi.text', fromlist=['x']).split_sentences(run.passage)[idx]}")
        return 0
    if args.sentence is None or args.text is None:
        sys.exit("edit needs --sentence N and --text 'new sentence' (or --list)")
    new_passage = replace_sentence(run.passage, args.sentence - 1, args.text)
    new_run, rep = edit(run, new_passage, build_backend(args))
    print(render_report(rep))
    if args.out:
        new_run.save(args.out)
        print(f"Saved {args.out}")
    return 0


def _retention():
    try:
        import fsrs  # noqa: F401
    except ImportError:
        sys.exit("The retention engine needs py-fsrs:  pip install fsrs   (and matplotlib for the PNG chart)")
    from . import retention
    return retention


def _parse_now(s: str | None):
    from datetime import datetime, timezone
    if not s:
        return datetime.now(timezone.utc)
    t = datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def cmd_learn(args) -> int:
    _retention()
    from .retention.bank import load_bank
    from .retention.io import ModelStudent, ScriptedIO, TerminalIO
    from .retention.session import AdaptiveSession, SessionConfig
    from .retention.state import LearnerState
    bank = load_bank(args.bank)
    for n in bank.notes:
        print(f"note: {n}", file=sys.stderr)
    if args.student is not None:
        knows = {x for x in args.student.split(",") if x and "M" not in x}
        holds = {x for x in args.student.split(",") if x and "M" in x}
        io = ModelStudent(knows, holds, echo=True, verbose=args.verbose)
    elif args.answers:
        io = ScriptedIO(args.answers.split(","), echo=True, verbose=args.verbose)
    else:
        io = TerminalIO(verbose=args.verbose)
    state = LearnerState() if args.fresh else LearnerState.load(args.state)
    cfg = SessionConfig(max_questions=args.max_questions, show_summary=not args.no_summary)
    AdaptiveSession(bank, state, io, cfg, now=_parse_now(args.now)).run()
    state.save(args.state)
    print(f"\nSaved learner state to {args.state}")
    return 0


def cmd_plan(args) -> int:
    _retention()
    from .retention.bank import load_bank
    from .retention.fsrs_sched import make_scheduler
    from .retention.ranker import revision_plan
    from .retention.state import LearnerState
    bank, state = load_bank(args.bank), LearnerState.load(args.state)
    if not any(c.fsrs_card for c in state.concepts.values()):
        sys.exit(f"No reviewed concepts in {args.state}: run `learn` first.")
    now = _parse_now(args.now)
    rows = revision_plan(state, {k: c.name for k, c in bank.concepts.items()}, make_scheduler(), now)
    print(f"Revision plan on {now:%a %d %b %Y} (most at risk first):")
    for i, r in enumerate(rows, 1):
        due = r.due.strftime("%a %d %b") if r.due else "-"
        print(f"  {i}. {r.name:<42} mastery {r.mastery:4.0%}  recall today {r.recall:4.0%}  risk {r.priority:4.0%}  due {due}")
    return 0


def cmd_simulate(args) -> int:
    _retention()
    from .retention.bank import load_bank
    from .retention.fsrs_sched import make_scheduler
    from .retention.simulate import ascii_chart, review_log, save_chart, simulate
    from .retention.state import LearnerState
    bank, state = load_bank(args.bank), LearnerState.load(args.state)
    try:
        res = simulate(state, make_scheduler(), days=args.days, seed=args.seed)
    except ValueError as e:
        sys.exit(str(e))
    names = {k: c.name for k, c in bank.concepts.items()}
    print(f"Fast-forwarding {args.days} days (pretend student; recall numbers from the FSRS memory model)\n")
    print(review_log(res, names))
    print("\n" + ascii_chart(res) + "\n")
    for d in sorted({min(7, args.days), args.days}):
        print(f"Day {d:>2}: remembered with no revision {res.daily_once[d - 1]:.0%}, "
              f"with our schedule {res.daily_scheduled[d - 1]:.0%} (just before that day's revision)")
    print(f"Revision sessions needed: {len({e.day for e in res.events})} days, {len(res.events)} concept reviews")
    if args.chart:
        if save_chart(res, args.chart, f"{bank.title}: predicted recall over {args.days} days"):
            print(f"Chart saved to {args.chart}")
        else:
            print("matplotlib is not installed, so no PNG chart (the text chart above has the same numbers)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sakshi", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check")
    c.add_argument("passage")
    c.add_argument("--gate-override", action="store_true", help="accept any length (testing only)")
    c.set_defaults(fn=cmd_check)

    pr = sub.add_parser("prepare")
    pr.add_argument("passage")
    pr.add_argument("--out", required=True)
    pr.add_argument("--metrics", help="also write metrics.json here")
    add_backend_args(pr)
    pr.add_argument("--n-items", type=int, default=6)
    pr.add_argument("--gate-override", action="store_true")
    pr.set_defaults(fn=cmd_prepare)

    rn = sub.add_parser("run", help="the whole deliverable: summary, quiz and run card on one screen")
    rn.add_argument("passage")
    rn.add_argument("--out", default="results/run.json")
    rn.add_argument("--metrics", help="metrics JSON path (default: next to --out)")
    add_backend_args(rn)
    rn.add_argument("--n-items", type=int, default=6)
    rn.add_argument("--gate-override", action="store_true")
    rn.set_defaults(fn=cmd_run)

    st = sub.add_parser("study")
    st.add_argument("run")
    st.add_argument("--include-amber", action="store_true", help="also ask AMBER items, labelled for a teacher")
    st.add_argument("--summary-first", action="store_true", help="show the summary before the questions (gives answers away)")
    st.set_defaults(fn=cmd_study)

    rs = sub.add_parser("resident", help="hold the model in one process behind a Unix socket")
    add_backend_args(rs)  # also defines --socket
    rs.set_defaults(fn=cmd_resident)

    sv = sub.add_parser("serve", help="serve a prepared quiz to phones over this machine's own Wi-Fi (no internet needed)")
    sv.add_argument("run")
    sv.add_argument("--host", default="0.0.0.0", help="0.0.0.0 so phones can reach it; 127.0.0.1 serves nobody else")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--include-amber", action="store_true")
    sv.set_defaults(fn=cmd_serve)

    vl = sub.add_parser("villain", help="show the saved baseline failure for the demo")
    vl.add_argument("file")
    vl.set_defaults(fn=cmd_villain)

    pb = sub.add_parser("probe", help="ask a resident process what network it can see")
    pb.add_argument("--socket", required=True)
    pb.set_defaults(fn=cmd_probe)

    ed = sub.add_parser("edit", help="change one sentence; only the questions that depend on it change")
    ed.add_argument("run")
    ed.add_argument("--list", action="store_true", help="list the sentences that have a question")
    ed.add_argument("--sentence", type=int, help="1-based sentence number to replace")
    ed.add_argument("--text", help="the new sentence")
    ed.add_argument("--out")
    add_backend_args(ed)
    ed.set_defaults(fn=cmd_edit)

    rp = sub.add_parser("report")
    rp.add_argument("run")
    rp.set_defaults(fn=cmd_report)

    ln = sub.add_parser("learn", help="adaptive quiz: diagnose misconceptions, walk the concept graph, schedule revision")
    ln.add_argument("bank", help="question bank JSON (see data/banks/)")
    ln.add_argument("--state", default="state/learner.json")
    ln.add_argument("--fresh", action="store_true", help="ignore any saved state and start a new learner")
    ln.add_argument("--verbose", action="store_true", help="show the engine's reasoning (for judges and teachers)")
    ln.add_argument("--student", help="a pretend student instead of the keyboard: concepts known and misconceptions "
                                      "held, e.g. C1,C2M1,C4M1")
    ln.add_argument("--answers", help="fixed answers instead of the keyboard, e.g. B,D,A")
    ln.add_argument("--max-questions", type=int, default=12)
    ln.add_argument("--no-summary", action="store_true")
    ln.add_argument("--now", help="pretend the session happens at this ISO time (demos and tests)")
    ln.set_defaults(fn=cmd_learn)

    pl = sub.add_parser("plan", help="the revision plan from the saved learner state")
    pl.add_argument("bank")
    pl.add_argument("--state", default="state/learner.json")
    pl.add_argument("--now", help="ISO time to plan for (default: now)")
    pl.set_defaults(fn=cmd_plan)

    sm = sub.add_parser("simulate", help="fast-forward N days: recall with and without our revision schedule")
    sm.add_argument("bank")
    sm.add_argument("--state", default="state/learner.json")
    sm.add_argument("--days", type=int, default=14)
    sm.add_argument("--seed", type=int, default=7)
    sm.add_argument("--chart", help="also save a PNG chart here (needs matplotlib)")
    sm.set_defaults(fn=cmd_simulate)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except BrokenPipeError:  # e.g. `sakshi report RUN | head`: the reader left; that is not an error
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
