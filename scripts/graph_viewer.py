#!/usr/bin/env python3
"""Write data/misconceptions/graph/viewer.html: an offline-friendly page to browse the misconception graph.

  python scripts/graph_viewer.py      then open data/misconceptions/graph/viewer.html in a browser

The graph data is embedded in the page. Drawing uses cytoscape.js from cdnjs (needs internet once to load the
library); the side lists work without it.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
G = os.path.join(ROOT, "data", "misconceptions", "graph")

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Misconception graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<style>
:root{--bg:#fafaf9;--panel:#fff;--ink:#1c1917;--muted:#78716c;--line:#e7e5e4;--topic:#1e40af;--l1:#2563eb;--l2:#60a5fa;--l3:#bfdbfe;--mis:#dc2626;--root:#7c3aed;--ext:#059669}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#1c1917;--panel:#292524;--ink:#f5f5f4;--muted:#a8a29e;--line:#44403c}}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--ink);display:grid;grid-template-columns:300px 1fr 360px;height:100vh}
aside,section{overflow:auto;border-right:1px solid var(--line);background:var(--panel);padding:12px}
section{border-left:1px solid var(--line)}#cy{height:100vh}
h1{font-size:16px;margin:0 0 8px}h2{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin:14px 0 6px}
select,input{width:100%;padding:6px;margin:4px 0;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
.item{padding:6px 8px;border-radius:6px;cursor:pointer;border:1px solid transparent}.item:hover{border-color:var(--line)}
.mis{color:var(--mis)}.root{color:var(--root)}.ext{color:var(--ext)}.small{color:var(--muted);font-size:12px}
.legend span{display:inline-block;margin-right:10px}.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px;vertical-align:middle}
@media (max-width:900px){body{grid-template-columns:1fr;height:auto}#cy{height:60vh}}
</style></head><body>
<aside>
<h1>Misconception graph</h1><div class="small" id="stats"></div>
<h2>Topic</h2>
<select id="subject"></select><select id="topic"></select>
<input id="search" placeholder="Search misconceptions, concepts, roots…">
<div id="results"></div>
<h2>Shared root beliefs</h2><div id="roots"></div>
</aside>
<div id="cy"></div>
<section><div class="legend small">
<span><i class="dot" style="background:var(--l1)"></i>big idea</span><span><i class="dot" style="background:var(--l2)"></i>sub-concept</span>
<span><i class="dot" style="background:var(--l3)"></i>smallest idea</span><span><i class="dot" style="background:var(--mis)"></i>misconception</span>
<span><i class="dot" style="background:var(--ext)"></i>from another topic</span><span><i class="dot" style="background:var(--root)"></i>root belief</span></div>
<div id="detail"><p class="small">Pick a topic, then click any node.</p></div></section>
<script>
const NODES = __NODES__, EDGES = __EDGES__;
const byId = Object.fromEntries(NODES.map(n => [n.id, n]));
const out = {}, inn = {};
for (const e of EDGES) { (out[e.src] ||= []).push(e); (inn[e.dst] ||= []).push(e); }
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const count = t => NODES.filter(n => n.type === t).length;
document.getElementById("stats").textContent = `${count("topic")} topics · ${count("concept")} concepts · ${count("misconception")} misconceptions · ${count("root_belief")} root beliefs · ${EDGES.length} links`;
const subjSel = document.getElementById("subject"), topSel = document.getElementById("topic");
const subjects = [...new Set(NODES.filter(n => n.type === "topic").map(n => n.subject))].sort();
subjSel.innerHTML = subjects.map(s => `<option>${s}</option>`).join("");
function fillTopics() {
  const ts = NODES.filter(n => n.type === "topic" && n.subject === subjSel.value && n.generated)
    .sort((a, b) => Math.min(...a.grades) - Math.min(...b.grades) || a.name.localeCompare(b.name));
  topSel.innerHTML = ts.map(t => `<option value="${t.id}">Class ${t.grades.join("/")}: ${esc(t.name)}</option>`).join("");
  draw(topSel.value);
}
let cy = null;
const DARK = document.documentElement.dataset.theme === "dark" ||
  (document.documentElement.dataset.theme !== "light" && matchMedia("(prefers-color-scheme: dark)").matches);
window.addEventListener("resize", () => { if (cy) { cy.resize(); cy.fit(undefined, 30); } });
function draw(tid) {
  if (!tid) return;
  const els = [], seen = new Set();
  const add = (n, cls) => { if (!seen.has(n.id)) { seen.add(n.id); els.push({data: {id: n.id, label: n.type === "misconception" ? "✗ " + n.statement : n.name, cls}}); } };
  add(byId[tid], "topic");
  const concepts = NODES.filter(n => n.type === "concept" && n.topic_id === tid);
  for (const c of concepts) add(c, "l" + c.level);
  for (const c of concepts) for (const e of out[c.id] || []) {
    const d = byId[e.dst];
    if (e.type === "part_of") els.push({data: {id: c.id + ">" + d.id, source: d.id, target: c.id, cls: "tree"}});
    if (e.type === "needs") { if (d.topic_id !== tid) add(d, "ext"); els.push({data: {id: c.id + "~" + d.id, source: d.id, target: c.id, cls: "needs"}}); }
  }
  const mis = NODES.filter(n => n.type === "misconception" && n.topic_id === tid);
  for (const m of mis) { add(m, "mis"); els.push({data: {id: m.id + ">", source: m.concept_id, target: m.id, cls: "about"}}); }
  for (const m of mis) for (const e of out[m.id] || []) if (e.type === "causes") els.push({data: {id: m.id + "!" + e.dst, source: m.id, target: e.dst, cls: "causes"}});
  if (!window.cytoscape) { document.getElementById("cy").innerHTML = "<p style='padding:20px'>Drawing library could not load (offline). Use the lists on the left and right.</p>"; return; }
  cy && cy.destroy();
  cy = cytoscape({container: document.getElementById("cy"), elements: els, wheelSensitivity: .3,
    layout: {name: "breadthfirst", directed: true, roots: [tid], spacingFactor: 1.05},
    style: [
      {selector: "node", style: {label: "data(label)", "font-size": 10, "text-wrap": "wrap", "text-max-width": 130, "text-valign": "bottom", "text-margin-y": 3, width: 14, height: 14, color: DARK ? "#d6d3d1" : "#44403c", "text-background-color": DARK ? "#1c1917" : "#ffffff", "text-background-opacity": 0.7, "text-background-padding": 1}},
      {selector: "node[cls='topic']", style: {"background-color": "#1e40af", width: 24, height: 24, "font-size": 12, "font-weight": 700}},
      {selector: "node[cls='l1']", style: {"background-color": "#2563eb", width: 20, height: 20, "font-size": 11}},
      {selector: "node[cls='l2']", style: {"background-color": "#60a5fa"}},
      {selector: "node[cls='l3']", style: {"background-color": "#bfdbfe"}},
      {selector: "node[cls='mis']", style: {"background-color": "#dc2626", shape: "diamond", color: DARK ? "#fca5a5" : "#b91c1c"}},
      {selector: "node[cls='ext']", style: {"background-color": "#059669", shape: "round-rectangle", color: DARK ? "#6ee7b7" : "#047857"}},
      {selector: "edge", style: {width: 1, "line-color": "#d6d3d1", "curve-style": "bezier"}},
      {selector: "edge[cls='needs']", style: {"line-color": "#059669", "target-arrow-color": "#059669", "target-arrow-shape": "triangle", "line-style": "dashed"}},
      {selector: "edge[cls='causes']", style: {"line-color": "#dc2626", "target-arrow-color": "#dc2626", "target-arrow-shape": "triangle"}},
      {selector: ":selected", style: {"border-width": 3, "border-color": "#f59e0b"}}]});
  cy.on("tap", "node", ev => show(ev.target.id()));
  cy.one("layoutstop", () => cy.fit(undefined, 30));
  setTimeout(() => { cy.resize(); cy.fit(undefined, 30); }, 50);
  show(tid);
}
function show(id) {
  const n = byId[id]; if (!n) return;
  let h = `<h2>${esc(n.type.replace("_", " "))}</h2><p><b>${esc(n.type === "misconception" ? n.statement : n.name)}</b></p>`;
  if (n.type === "topic") h += `<p class="small">${esc(n.subject)} · ${esc(n.strand)} · Class ${n.grades.join("/")}</p>` +
     `<p class="small">Needs topics: ${(out[id] || []).filter(e => e.type === "topic_needs").map(e => esc(byId[e.dst].name)).join(", ") || "none linked"}</p>`;
  if (n.type === "concept") {
    h += `<p class="small">${esc(n.topic)} · level ${n.level}</p>`;
    const needs = (out[id] || []).filter(e => e.type === "needs");
    h += `<h2>Needs first</h2>` + (needs.map(e => `<div class="item ${byId[e.dst].topic_id !== n.topic_id ? "ext" : ""}" onclick="show('${e.dst}')">${esc(byId[e.dst].name)} <span class="small">${byId[e.dst].topic_id !== n.topic_id ? "(" + esc(byId[e.dst].topic) + ")" : ""}</span></div>`).join("") || "<p class='small'>nothing</p>");
    const unlocks = (inn[id] || []).filter(e => e.type === "needs");
    h += `<h2>Unlocks</h2>` + (unlocks.map(e => `<div class="item" onclick="show('${e.src}')">${esc(byId[e.src].name)} <span class="small">(${esc(byId[e.src].topic)})</span></div>`).join("") || "<p class='small'>nothing</p>");
    if (n.unresolved_prereqs) h += `<p class="small">Unlinked prerequisites: ${n.unresolved_prereqs.map(esc).join("; ")}</p>`;
    const ms = (inn[id] || []).filter(e => e.type === "about");
    h += `<h2>Misconceptions</h2>` + (ms.map(e => `<div class="item mis" onclick="show('${e.src}')">✗ ${esc(byId[e.src].statement)}</div>`).join("") || "<p class='small'>none</p>");
  }
  if (n.type === "misconception") {
    h += `<p class="small">${esc(n.topic)} → ${esc(n.concept)} · ${esc(n.error_type)} · ${esc(n.confidence)}${n.source_hint ? " (" + esc(n.source_hint) + ")" : ""}</p>`;
    h += `<h2>Why students think it</h2><p>${esc(n.why)}</p><h2>Fix</h2><p>${esc(n.fix)}</p>`;
    h += `<h2>Diagnostic probe</h2><p>${esc(n.probe?.question)}<br><span class="mis">Wrong answer: ${esc(n.probe?.wrong_answer)}</span></p>`;
    const rt = (out[id] || []).find(e => e.type === "from_root");
    if (rt) h += `<h2>Root belief</h2><div class="item root" onclick="showRoot('${rt.dst}')">${esc(byId[rt.dst].name)} <span class="small">(${byId[rt.dst].members} misconceptions)</span></div>`;
    const causes = (out[id] || []).filter(e => e.type === "causes"), causedBy = (inn[id] || []).filter(e => e.type === "causes");
    if (causes.length) h += `<h2>Leads to</h2>` + causes.map(e => `<div class="item mis" onclick="show('${e.dst}')">✗ ${esc(byId[e.dst].statement)}</div>`).join("");
    if (causedBy.length) h += `<h2>Caused by</h2>` + causedBy.map(e => `<div class="item mis" onclick="show('${e.src}')">✗ ${esc(byId[e.src].statement)}</div>`).join("");
    h += `<p class="small">id ${esc(id)} · cues: ${esc((n.trigger_cues || []).join(", "))}</p>`;
  }
  if (n.type === "root_belief") return showRoot(id);
  document.getElementById("detail").innerHTML = h;
  if (cy && cy.getElementById(id).length) { cy.$(":selected").unselect(); cy.getElementById(id).select(); }
}
function showRoot(rid) {
  const r = byId[rid];
  const ms = (inn[rid] || []).filter(e => e.type === "from_root").map(e => byId[e.src]);
  document.getElementById("detail").innerHTML = `<h2>root belief</h2><p class="root"><b>${esc(r.name)}</b></p><p class="small">${ms.length} misconceptions · ${r.subjects.join(", ")}</p>` +
    ms.map(m => `<div class="item mis" onclick="goTo('${m.id}')">✗ ${esc(m.statement)}<br><span class="small">${esc(m.subject)} · Class ${m.grades.join("/")} · ${esc(m.topic)}</span></div>`).join("");
}
function goTo(mid) { const m = byId[mid]; subjSel.value = m.subject; fillTopicsOnly(); topSel.value = m.topic_id; draw(m.topic_id); show(mid); }
function fillTopicsOnly() { const v = topSel.value; fillTopics.call(null); }
document.getElementById("roots").innerHTML = NODES.filter(n => n.type === "root_belief" && n.members > 2).sort((a, b) => b.members - a.members).slice(0, 40)
  .map(r => `<div class="item root" onclick="showRoot('${r.id}')">${esc(r.name)} <span class="small">${r.members} · ${r.subjects.join("/")}</span></div>`).join("");
document.getElementById("search").addEventListener("input", ev => {
  const q = ev.target.value.toLowerCase().trim();
  if (q.length < 3) { document.getElementById("results").innerHTML = ""; return; }
  const hits = NODES.filter(n => ((n.statement || "") + " " + (n.name || "")).toLowerCase().includes(q)).slice(0, 30);
  document.getElementById("results").innerHTML = hits.map(n => `<div class="item ${n.type === "misconception" ? "mis" : n.type === "root_belief" ? "root" : ""}" onclick="${n.type === "root_belief" ? `showRoot('${n.id}')` : `goTo2('${n.id}')`}">${esc(n.type === "misconception" ? "✗ " + n.statement : n.name)} <span class="small">${esc(n.topic || n.type)}</span></div>`).join("");
});
function goTo2(id) { const n = byId[id]; if (n.type === "topic") { subjSel.value = n.subject; fillTopics(); topSel.value = id; draw(id); return; } goTo(n.type === "misconception" ? id : (inn[id] || []).find(e => e.type === "about")?.src || id); if (n.type === "concept") { subjSel.value = n.subject; fillTopics(); topSel.value = n.topic_id; draw(n.topic_id); show(id); } }
subjSel.onchange = fillTopics; topSel.onchange = () => draw(topSel.value);
fillTopics();
</script></body></html>"""


def main():
    nodes = [json.loads(l) for l in open(os.path.join(G, "nodes.jsonl"), encoding="utf-8")]
    edges = [json.loads(l) for l in open(os.path.join(G, "edges.jsonl"), encoding="utf-8")]
    html = PAGE.replace("__NODES__", json.dumps(nodes, ensure_ascii=False)).replace("__EDGES__", json.dumps(edges, ensure_ascii=False))
    path = os.path.join(G, "viewer.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path} ({len(nodes)} nodes, {len(edges)} edges, {len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
