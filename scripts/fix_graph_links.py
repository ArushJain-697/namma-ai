#!/usr/bin/env python3
"""Rebuild the graph's two weak link types by MEANING instead of by shared words, with Sonnet as the judge.

  .venv-ml/bin/python scripts/fix_graph_links.py            # writes data/misconceptions/links_v2.json
  python3 scripts/build_misconception_graph.py assemble     # assemble uses links_v2.json when it exists

1. Cross-topic "needs first" links. Every prerequisite name a topic gave (e.g. "multiplication of decimals") is
   compared by meaning with every concept taught in the same or an earlier class in another topic.
   Clear winners link directly; close calls go to Sonnet in batches ("which of these 5, or none?").
2. Root beliefs. The deeper reason behind each misconception was written in different words every time, so word
   matching left almost every misconception alone. Here the reasons are grouped by meaning into ~120 groups,
   Sonnet names each group as one clear root belief, and every misconception is attached to its closest root.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_misconception_library as v1  # noqa: E402

G = os.path.join(ROOT, "data", "misconceptions", "graph")
OUT = os.path.join(ROOT, "data", "misconceptions", "links_v2.json")
SONNET = "claude-sonnet-5-5"


def sonnet_json(prompt: str) -> dict:
    for attempt in range(3):
        try:
            text, _ = v1.claude_generate(prompt, SONNET, timeout=900)
            return v1.loads_lenient(text)
        except Exception as e:  # noqa: BLE001
            print(f"  sonnet attempt {attempt + 1} failed: {str(e)[:120]}", flush=True)
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", type=float, default=0.86, help="similarity at which a prerequisite links without asking")
    ap.add_argument("--ask", type=float, default=0.62, help="similarity from which Sonnet is asked")
    ap.add_argument("--roots", type=int, default=120, help="number of root-belief groups")
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--recheck-auto", action="store_true",
                    help="keep the Sonnet-judged links and roots in links_v2.json, send the auto-linked ones to Sonnet too")
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    emb = SentenceTransformer("BAAI/bge-small-en-v1.5")
    enc = lambda xs: np.asarray(emb.encode(xs, normalize_embeddings=True, batch_size=128, show_progress_bar=False))  # noqa: E731

    nodes = [json.loads(l) for l in open(os.path.join(G, "nodes.jsonl"), encoding="utf-8")]
    edges = [json.loads(l) for l in open(os.path.join(G, "edges.jsonl"), encoding="utf-8")]
    concepts = [n for n in nodes if n["type"] == "concept" and n.get("topic_id") != "GEN-READ"]
    mis = [n for n in nodes if n["type"] == "misconception" and n.get("subject") != "reading_skill"]

    # ---- 1. prerequisites ------------------------------------------------------------------------------
    wanted = defaultdict(list)  # concept id -> prerequisite names it asked for
    for e in edges:
        if e["type"] == "needs" and "via" in e:
            wanted[e["src"]].append(e["via"])
    for c in concepts:
        wanted[c["id"]] += c.get("unresolved_prereqs", [])
    pairs = [(cid, name) for cid, names in wanted.items() for name in dict.fromkeys(names)]
    by_id = {c["id"]: c for c in concepts}
    C = enc([f"{c['name']} ({c['topic']})" for c in concepts])
    Q = enc([name for _, name in pairs])
    S = Q @ C.T
    links, ask, auto_pairs = [], [], set()
    if args.recheck_auto:
        prev = json.load(open(OUT))
        links = [l for l in prev["prereq_links"] if l["how"] == "sonnet"]
        auto_pairs = {(l["src"], l["via"]) for l in prev["prereq_links"] if l["how"] == "meaning"}
    for k, (cid, name) in enumerate(pairs):
        me = by_id[cid]
        ok = [j for j, c in enumerate(concepts) if c["topic_id"] != me["topic_id"]
              and min(c["grades"]) <= max(me["grades"])]
        if not ok:
            continue
        sims = S[k, ok]
        order = np.argsort(-sims)[:5]
        top = [(concepts[ok[i]], float(sims[i])) for i in order]
        if args.recheck_auto:
            if (cid, name) in auto_pairs:
                ask.append((cid, name, top))
            continue
        if top[0][1] >= args.auto and (len(top) < 2 or top[0][1] - top[1][1] >= 0.02):
            links.append({"src": cid, "dst": top[0][0]["id"], "via": name, "how": "meaning", "score": round(top[0][1], 3)})
        elif top[0][1] >= args.ask:
            ask.append((cid, name, top))
    print(f"prerequisite names: {len(pairs)}; linked by meaning: {len(links)}; asking Sonnet: {len(ask)}", flush=True)

    for b in range(0, len(ask), args.batch):
        chunk = ask[b: b + args.batch]
        lines = []
        for i, (cid, name, top) in enumerate(chunk):
            me = by_id[cid]
            opts = "; ".join(f"{j + 1}) {c['name']} [{c['topic']}, class {'/'.join(map(str, c['grades']))}]"
                             for j, (c, _) in enumerate(top))
            lines.append(f"{i}. A student learning \"{me['name']}\" ({me['topic']}, class {'/'.join(map(str, me['grades']))}) "
                         f"must first know: \"{name}\". Options: {opts}")
        prompt = ("For each numbered item, pick the option that IS the prerequisite named in quotes (the same idea, "
                  "not just a related one). Answer 0 if none of the options is that idea.\n\n" + "\n".join(lines) +
                  '\n\nReturn only JSON: {"choices": [{"item": 0, "option": 2}, ...]} with one entry per item.')
        out = sonnet_json(prompt)
        for ch in out.get("choices", []):
            try:
                i, o = int(ch["item"]), int(ch["option"])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= i < len(chunk) and 1 <= o <= len(chunk[i][2]):
                cid, name, top = chunk[i]
                links.append({"src": cid, "dst": top[o - 1][0]["id"], "via": name, "how": "sonnet",
                              "score": round(top[o - 1][1], 3)})
        print(f"  sonnet batch {b // args.batch + 1}/{(len(ask) + args.batch - 1) // args.batch}: links now {len(links)}", flush=True)

    if args.recheck_auto:  # roots were already done: keep them
        prev["prereq_links"] = links
        json.dump(prev, open(OUT, "w"), indent=1)
        print(f"rechecked: {len(links)} links ({sum(l['how'] == 'sonnet' for l in links)} Sonnet-checked)")
        return

    # ---- 2. root beliefs -------------------------------------------------------------------------------
    from sklearn.cluster import AgglomerativeClustering
    texts = [m.get("root_belief") or m["statement"] for m in mis]
    R = enc(texts)
    lab = AgglomerativeClustering(n_clusters=args.roots, metric="cosine", linkage="average").fit_predict(R)
    groups = defaultdict(list)
    for i, l in enumerate(lab):
        groups[int(l)].append(i)
    print(f"root groups: {len(groups)} (sizes: largest {max(map(len, groups.values()))}, "
          f"singletons {sum(len(g) == 1 for g in groups.values())})", flush=True)
    names = {}
    gids = sorted(groups, key=lambda g: -len(groups[g]))
    for b in range(0, len(gids), 30):
        chunk = gids[b: b + 30]
        lines = []
        for g in chunk:
            idx = groups[g][:8]
            ex = " | ".join(dict.fromkeys(texts[i] for i in idx))
            st = " | ".join(mis[i]["statement"] for i in groups[g][:3])
            lines.append(f"group {g} ({len(groups[g])} misconceptions). Reasons: {ex}. Examples: {st}")
        prompt = ("Each group below collects student misconceptions that share a deeper reason. Name that deeper reason "
                  "as ONE clear, general belief a student holds, in at most 10 simple words, phrased so it applies "
                  "across subjects (e.g. \"a bigger number always means a bigger amount\"). Add a one-sentence "
                  "explanation for teachers.\n\n" + "\n".join(lines) +
                  '\n\nReturn only JSON: {"roots": [{"group": 3, "name": "...", "explanation": "..."}, ...]}')
        out = sonnet_json(prompt)
        for r in out.get("roots", []):
            try:
                names[int(r["group"])] = (str(r["name"]).strip().rstrip("."), str(r.get("explanation", "")).strip())
            except (KeyError, TypeError, ValueError):
                continue
        print(f"  named {len(names)}/{len(groups)} root groups", flush=True)
    roots = []
    for g in gids:
        name, expl = names.get(g, (texts[groups[g][0]], ""))
        roots.append({"id": f"ROOT-{len(roots) + 1}", "group": g, "name": name, "explanation": expl})
    # attach every misconception to its closest named root (meaning of the root name vs the misconception's reason)
    RN = enc([r["name"] for r in roots])
    assign = {}
    sims = R @ RN.T
    for i, m in enumerate(mis):
        own = next(k for k, r in enumerate(roots) if r["group"] == int(lab[i]))
        best = int(np.argmax(sims[i]))
        assign[m["id"]] = roots[best if sims[i, best] - sims[i, own] > 0.05 else own]["id"]

    subj = defaultdict(set)
    cnt = Counter(assign.values())
    for m in mis:
        subj[assign[m["id"]]].add(m["subject"])
    for r in roots:
        r["members"], r["subjects"] = cnt[r["id"]], sorted(subj[r["id"]])
    roots = [r for r in roots if r["members"]]
    json.dump({"prereq_links": links, "roots": roots, "misconception_root": assign}, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")
    print(f"cross-topic prerequisite links: {len(links)} "
          f"({sum(l['how'] == 'meaning' for l in links)} by meaning, {sum(l['how'] == 'sonnet' for l in links)} checked by Sonnet)")
    print(f"root beliefs: {len(roots)}, every misconception attached; spanning 2+ subjects: "
          f"{sum(len(r['subjects']) > 1 for r in roots)}; biggest: "
          + "; ".join(f"{r['name']} ({r['members']})" for r in sorted(roots, key=lambda r: -r["members"])[:6]))


if __name__ == "__main__":
    main()
