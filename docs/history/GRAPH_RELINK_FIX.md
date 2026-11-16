# Fix for the graph-growth loop: re-linking lost most links and all root names

Give this file to Claude Code on the graph-growth laptop and say: "Read GRAPH_RELINK_FIX.md and do it."

## What went wrong (13 Nov, commit a91e541 "Grow misconception graph: 248 topics")
Every 5 rounds `grow_graph.sh` re-links the whole graph with `scripts/fix_graph_links.py`. In that run Sonnet was
unavailable (usage limit), and the script silently wrote a much worse file:
- cross-topic prerequisite links fell from 1,955 (all Sonnet-checked) to 843 (none checked);
- all 120 root beliefs lost their names and explanations.
The new topics and misconceptions themselves are fine (no ids changed). Only `links_v2.json` and the graph built
from it are damaged. The good previous file is still in `data/misconceptions/links_v2.prev.json`, but the NEXT
re-link would overwrite it, so do this before the loop reaches another multiple of 5 rounds.

## The fix (already tested on the a91e541 data)
`fix_graph_links.py --incremental`: reuses every earlier Sonnet decision, asks Sonnet only about new topics, keeps
the 120 named roots and attaches new misconceptions to the closest one, and never writes a result worse than the
best saved file (`links_v2.good.json`). `grow_graph.sh` now calls it. Tested result on a91e541, Sonnet switched
off: 2,657 cross-topic links (2,391 Sonnet-checked), 488 unresolved prerequisites, 120 named roots.

## Steps (in the repo, on the graph-growth branch)
1. Stop the loop (Ctrl-C in its terminal). Make sure nothing else is running: `pgrep -fl grow_graph`.
2. Apply the patch below (it changes only `scripts/fix_graph_links.py` and `scripts/grow_graph.sh`; both are
   unchanged on this branch, so it applies cleanly). Save the patch block to `/tmp/relink.patch`, then:
```bash
git apply --check /tmp/relink.patch && git apply /tmp/relink.patch
```
3. Repair the links once (e9888dd is the commit that has the 1,955 Sonnet-checked links):
```bash
git show e9888dd:data/misconceptions/links_v2.json > data/misconceptions/links_v2.good.json
mv data/misconceptions/links_v2.json data/misconceptions/links_v2.bad.json
python3 scripts/build_misconception_graph.py assemble >/dev/null
.venv-ml/bin/python scripts/fix_graph_links.py --incremental
python3 scripts/build_misconception_graph.py assemble | tail -3
python3 scripts/graph_viewer.py
python3 -c "import json; s=json.load(open('data/misconceptions/graph/stats.json')); l=json.load(open('data/misconceptions/links_v2.json')); print('cross-topic links', s['cross_topic_needs'], '| named roots', sum(bool(r.get('explanation')) for r in l['roots']))"
```
   Expected: about 2,600+ cross-topic links and 120 named roots. If the numbers are far lower, stop and report.
4. Check nothing else broke:
```bash
.venv/bin/python -m pytest -q --ignore=tests/test_resident.py
.venv/bin/python scripts/check_library_match.py | tail -2      # top-1 topic right must stay >= 38/40
```
5. Commit everything (`git add scripts/fix_graph_links.py scripts/grow_graph.sh data/misconceptions` and a message
   like "Fix re-link: keep Sonnet links and named roots; repair a91e541"), push the graph-growth branch, open a PR to
   `ArushJain-697/namma-ai` branch `question-quality`. Do not commit `links_v2.bad.json` (delete it).
6. Restart the loop: `bash scripts/grow_graph.sh`.

If Sonnet keeps hitting its limit, that is fine now: new topics stay unlinked until the next re-link, nothing is lost.

## The patch
```diff
diff --git a/scripts/fix_graph_links.py b/scripts/fix_graph_links.py
index b85c36e..f63230b 100644
--- a/scripts/fix_graph_links.py
+++ b/scripts/fix_graph_links.py
@@ -25,9 +25,20 @@ import build_misconception_library as v1  # noqa: E402
 
 G = os.path.join(ROOT, "data", "misconceptions", "graph")
 OUT = os.path.join(ROOT, "data", "misconceptions", "links_v2.json")
+PREV = os.path.join(ROOT, "data", "misconceptions", "links_v2.prev.json")
+GOOD = os.path.join(ROOT, "data", "misconceptions", "links_v2.good.json")  # best file so far; only replaced by >= one
+
+
+def _quality(f: dict) -> tuple:
+    """(Sonnet-checked links, roots with an explanation): a re-link must never write something worse than this."""
+    return (sum(l.get("how") == "sonnet" for l in f.get("prereq_links", [])),
+            sum(bool(r.get("explanation")) for r in f.get("roots", [])))
 SONNET = "claude-sonnet-5-5"
 
 
+FAILED = []  # prompts Sonnet could not answer this run (usage limit, timeouts)
+
+
 def sonnet_json(prompt: str) -> dict:
     for attempt in range(3):
         try:
@@ -35,6 +46,7 @@ def sonnet_json(prompt: str) -> dict:
             return v1.loads_lenient(text)
         except Exception as e:  # noqa: BLE001
             print(f"  sonnet attempt {attempt + 1} failed: {str(e)[:120]}", flush=True)
+    FAILED.append(prompt[:80])
     return {}
 
 
@@ -44,6 +56,10 @@ def main():
     ap.add_argument("--ask", type=float, default=0.62, help="similarity from which Sonnet is asked")
     ap.add_argument("--roots", type=int, default=120, help="number of root-belief groups")
     ap.add_argument("--batch", type=int, default=40)
+    ap.add_argument("--incremental", action="store_true",
+                    help="reuse every earlier Sonnet decision and the named roots (from links_v2.json, .prev and "
+                         ".good); ask Sonnet only about new prerequisite names; attach new misconceptions to the "
+                         "closest existing root. Never loses links when Sonnet is unavailable. Use this in grow_graph.sh")
     ap.add_argument("--recheck-auto", action="store_true",
                     help="keep the Sonnet-judged links and roots in links_v2.json, send the auto-linked ones to Sonnet too")
     args = ap.parse_args()
@@ -70,12 +86,24 @@ def main():
     Q = enc([name for _, name in pairs])
     S = Q @ C.T
     links, ask, auto_pairs = [], [], set()
+    olds = [json.load(open(f)) for f in (OUT, PREV, GOOD) if os.path.exists(f)]
+    cache = {}
+    if args.incremental:
+        for f in olds:
+            for l in f.get("prereq_links", []):
+                if l.get("how") == "sonnet":
+                    cache.setdefault((l["src"], l["via"]), l)
+        print(f"incremental: {len(cache)} earlier Sonnet decisions available from {len(olds)} file(s)", flush=True)
     if args.recheck_auto:
         prev = json.load(open(OUT))
         links = [l for l in prev["prereq_links"] if l["how"] == "sonnet"]
         auto_pairs = {(l["src"], l["via"]) for l in prev["prereq_links"] if l["how"] == "meaning"}
     for k, (cid, name) in enumerate(pairs):
         me = by_id[cid]
+        hit = cache.get((cid, name))
+        if hit and hit["dst"] in by_id:
+            links.append(dict(hit))
+            continue
         ok = [j for j, c in enumerate(concepts) if c["topic_id"] != me["topic_id"]
               and min(c["grades"]) <= max(me["grades"])]
         if not ok:
@@ -124,9 +152,23 @@ def main():
         return
 
     # ---- 2. root beliefs -------------------------------------------------------------------------------
-    from sklearn.cluster import AgglomerativeClustering
     texts = [m.get("root_belief") or m["statement"] for m in mis]
     R = enc(texts)
+    named = [f for f in olds if _quality(f)[1] >= 0.9 * max(1, len(f.get("roots", [])))]
+    if args.incremental and named:
+        best = max(named, key=lambda f: (len(f.get("misconception_root", {})), _quality(f)))
+        roots = [dict(r) for r in best["roots"]]
+        ids = {r["id"] for r in roots}
+        RN = enc([r["name"] for r in roots])
+        assign, sims = {}, R @ RN.T
+        for i, m in enumerate(mis):  # keep earlier assignments; new misconceptions go to the closest named root
+            prev_root = best["misconception_root"].get(m["id"])
+            assign[m["id"]] = prev_root if prev_root in ids else roots[int(np.argmax(sims[i]))]["id"]
+        print(f"incremental: kept {len(roots)} named roots; attached "
+              f"{sum(m['id'] not in best['misconception_root'] for m in mis)} new misconceptions", flush=True)
+        _finish(links, roots, assign, mis)
+        return
+    from sklearn.cluster import AgglomerativeClustering
     lab = AgglomerativeClustering(n_clusters=args.roots, metric="cosine", linkage="average").fit_predict(R)
     groups = defaultdict(list)
     for i, l in enumerate(lab):
@@ -168,6 +210,10 @@ def main():
         best = int(np.argmax(sims[i]))
         assign[m["id"]] = roots[best if sims[i, best] - sims[i, own] > 0.05 else own]["id"]
 
+    _finish(links, roots, assign, mis)
+
+
+def _finish(links, roots, assign, mis) -> None:
     subj = defaultdict(set)
     cnt = Counter(assign.values())
     for m in mis:
@@ -175,7 +221,18 @@ def main():
     for r in roots:
         r["members"], r["subjects"] = cnt[r["id"]], sorted(subj[r["id"]])
     roots = [r for r in roots if r["members"]]
-    json.dump({"prereq_links": links, "roots": roots, "misconception_root": assign}, open(OUT, "w"), indent=1)
+    new = {"prereq_links": links, "roots": roots, "misconception_root": assign}
+    good = json.load(open(GOOD)) if os.path.exists(GOOD) else None
+    if good and _quality(new) < _quality(good):  # Sonnet was unavailable: never replace a better file with a worse one
+        print(f"WARNING: this run is worse than {os.path.basename(GOOD)} (Sonnet links, named roots) "
+              f"{_quality(new)} < {_quality(good)}; {len(FAILED)} Sonnet calls failed. Keeping the good file as links_v2.json.")
+        json.dump(new, open(OUT.replace(".json", ".failed.json"), "w"), indent=1)
+        json.dump(good, open(OUT, "w"), indent=1)
+        return
+    json.dump(new, open(OUT, "w"), indent=1)
+    json.dump(new, open(GOOD, "w"), indent=1)
+    if FAILED:
+        print(f"WARNING: {len(FAILED)} Sonnet calls failed; those prerequisites stay unresolved until the next re-link")
     print(f"\nwrote {OUT}")
     print(f"cross-topic prerequisite links: {len(links)} "
           f"({sum(l['how'] == 'meaning' for l in links)} by meaning, {sum(l['how'] == 'sonnet' for l in links)} checked by Sonnet)")
diff --git a/scripts/grow_graph.sh b/scripts/grow_graph.sh
index 1cc8e64..8cc014a 100644
--- a/scripts/grow_graph.sh
+++ b/scripts/grow_graph.sh
@@ -30,11 +30,11 @@ while true; do
   say "generate + deepen"
   python3 scripts/build_misconception_graph.py generate --workers 2 --models "$MODELS" 2>&1 | tee -a "$LOG" | tail -2
   python3 scripts/build_misconception_graph.py deepen --workers 2 --models "$MODELS" 2>&1 | tee -a "$LOG" | tail -1
-  if [ $((round % 5)) -eq 0 ]; then  # every 5 rounds: re-link prerequisites and roots by meaning (Sonnet-checked)
+  if [ $((round % 5)) -eq 0 ]; then  # every 5 rounds: link the NEW topics (earlier Sonnet links and named roots are kept)
     say "re-link by meaning (every 5 rounds)"
     mv data/misconceptions/links_v2.json data/misconceptions/links_v2.prev.json 2>/dev/null
     python3 scripts/build_misconception_graph.py assemble >/dev/null 2>&1   # plain graph for the fixer to read
-    $ML scripts/fix_graph_links.py 2>&1 | grep -vE "Warning|warn|W11|Loading" | tail -4 | tee -a "$LOG"
+    $ML scripts/fix_graph_links.py --incremental 2>&1 | grep -vE "Warning|warn|W11|Loading" | tail -6 | tee -a "$LOG"
     [ -f data/misconceptions/links_v2.json ] || mv data/misconceptions/links_v2.prev.json data/misconceptions/links_v2.json
   fi
   say "assemble + viewer + checks"
```
