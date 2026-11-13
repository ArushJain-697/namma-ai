#!/usr/bin/env bash
# Grow the misconception graph all day: propose new topics -> generate -> deepen -> assemble -> checks, forever.
#   bash scripts/grow_graph.sh            (stop with Ctrl-C; log: results/grow_graph.log)
# Safe to stop and restart at any point: every step skips finished work. Sonnet (Claude Code CLI) writes;
# Gemini is the backup when Sonnet hits its usage limit. Runs on its own git branch: see TEAMMATE_TODO.md.
set -u
cd "$(dirname "$0")/.."
LOG=results/grow_graph.log
mkdir -p results
ML=.venv-ml/bin/python
MODELS="claude:claude-sonnet-5-5,gemini-3-flash-preview,gemini-3.1-flash-lite"
say() { echo "[$(date '+%m-%d %H:%M')] $*" | tee -a "$LOG"; }
# subjects and focus areas to rotate through (edit freely)
AREAS=(
  "maths|Class 6-8 arithmetic and number sense" "maths|Class 9-10 algebra and geometry" "maths|data, measurement and everyday maths"
  "science|Class 6-8 physics in daily life" "science|Class 9-10 chemistry" "science|human body and health science"
  "science|plants, animals and ecology" "science|earth, weather and space science"
  "social|Indian history beyond the textbook basics" "social|world history" "social|Indian geography and states"
  "social|government, law and rights" "social|economics in daily life"
  "general|culture, festivals and arts of India" "general|careers, work and skills" "general|digital life and media"
  "general|agriculture and rural life" "general|cities, transport and infrastructure" "general|famous Indian scientists and inventors"
)
round=0
while true; do
  round=$((round + 1))
  pick="${AREAS[$(( (round - 1) % ${#AREAS[@]} ))]}"
  subject="${pick%%|*}"; area="${pick#*|}"
  say "== round $round: propose 8 new $subject topics ($area)"
  $ML scripts/propose_topics.py --subject "$subject" --n 8 --area "$area" 2>&1 | grep -vE "Warning|warn|W11|Loading" | tee -a "$LOG" | tail -3
  say "generate + deepen"
  python3 scripts/build_misconception_graph.py generate --workers 2 --models "$MODELS" 2>&1 | tee -a "$LOG" | tail -2
  python3 scripts/build_misconception_graph.py deepen --workers 2 --models "$MODELS" 2>&1 | tee -a "$LOG" | tail -1
  if [ $((round % 5)) -eq 0 ]; then  # every 5 rounds: re-link prerequisites and roots by meaning (Sonnet-checked)
    say "re-link by meaning (every 5 rounds)"
    mv data/misconceptions/links_v2.json data/misconceptions/links_v2.prev.json 2>/dev/null
    python3 scripts/build_misconception_graph.py assemble >/dev/null 2>&1   # plain graph for the fixer to read
    $ML scripts/fix_graph_links.py 2>&1 | grep -vE "Warning|warn|W11|Loading" | tail -4 | tee -a "$LOG"
    [ -f data/misconceptions/links_v2.json ] || mv data/misconceptions/links_v2.prev.json data/misconceptions/links_v2.json
  fi
  say "assemble + viewer + checks"
  python3 scripts/build_misconception_graph.py assemble 2>&1 | grep -E '"(topic|concept|misconception|root_belief)":' | tee -a "$LOG"
  python3 scripts/graph_viewer.py | tee -a "$LOG"
  .venv/bin/python scripts/check_library_match.py | grep -E "scored" | tee -a "$LOG"
  $ML scripts/calibrate_fallback.py 2>&1 | grep -E "suggested" | tee -a "$LOG"
  if grep -q "out of quota for today" <(tail -40 "$LOG"); then say "all teachers out of quota: sleeping 1 hour"; sleep 3600; fi
  sleep 30
done
