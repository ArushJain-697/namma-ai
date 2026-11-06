"""Command line: python -m sakshi {check,prepare,study,report}.

  check PASSAGE            is this passage usable (150-300 words)?
  prepare PASSAGE --out R  run the pipeline, save the run, print the run card
  study R                  the student quiz (no model needed: it plays a prepared run)
  report R                 tiers, witnesses, reasons and the run card (for teachers and judges)
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
