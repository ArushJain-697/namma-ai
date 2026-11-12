#!/usr/bin/env bash
# Save evidence that nothing leaves this machine. Run ON the Pi:  bash scripts/prove_offline.sh [tag]
# Evidence goes to results/<tag>/. It shows "no route out": a claim about the network state at that
# moment, not a mathematical proof. Model-process isolation (unshare -n) is a separate step (T20).
# A probe that cannot run is reported as UNKNOWN, never as a pass.
set -u
cd "$(dirname "$0")/.."
TAG="${1:-offline-$(date +%Y%m%d-%H%M%S)}"
OUT="results/$TAG"; mkdir -p "$OUT"
FAIL=0; UNKNOWN=0
{
  echo "# offline evidence $(date -Is) on $(uname -n)"

  echo "## default route, from /proc/net/route (always present on Linux)"
  if [ -r /proc/net/route ]; then
    DEF="$(awk 'NR>1 && $2=="00000000" {print $1}' /proc/net/route | tr '\n' ' ')"
    if [ -n "$DEF" ]; then echo "DEFAULT ROUTE PRESENT via: $DEF -> NOT OFFLINE"; else echo "no default route: good"; fi
  else
    echo "cannot read /proc/net/route -> UNKNOWN"
  fi

  echo "## routes and interfaces (informational)"
  if command -v ip >/dev/null; then ip route 2>&1; ip -br addr 2>&1; else echo "ip not installed (informational only)"; fi

  echo "## proxy settings (a proxy can hide the real network state)"
  env | grep -i -E '^(https?|all)_proxy=' | sed 's/=.*/=<set>/' || true
  env | grep -qi -E '^(https?|all)_proxy=' && echo "WARNING: a proxy is configured; the probes below bypass it"

  echo "## DNS lookup (should fail)"
  if command -v getent >/dev/null; then
    getent hosts example.com >/dev/null 2>&1 && echo "DNS RESOLVED -> NOT OFFLINE" || echo "DNS failed: good"
  else echo "getent missing -> UNKNOWN"; fi

  echo "## ping 1.1.1.1 (should fail)"
  if command -v ping >/dev/null; then
    ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 && echo "PING SUCCEEDED -> NOT OFFLINE" || echo "ping failed: good"
  else echo "ping missing -> UNKNOWN"; fi

  echo "## HTTPS direct, proxies bypassed (should fail)"
  if command -v curl >/dev/null; then
    curl --noproxy '*' -s -m 5 -o /dev/null https://example.com && echo "HTTPS SUCCEEDED -> NOT OFFLINE" || echo "https failed: good"
  else echo "curl missing -> UNKNOWN"; fi
} 2>&1 | tee "$OUT/offline_evidence.txt"

# Match only this script's own markers ("-> ..."): `ip -br addr` prints the loopback state as "UNKNOWN", which
# once turned a clean result into UNKNOWN on the Arduino UNO Q.
grep -q -- "-> NOT OFFLINE" "$OUT/offline_evidence.txt" && FAIL=1
grep -q -- "-> UNKNOWN" "$OUT/offline_evidence.txt" && UNKNOWN=1
echo
if [ "$FAIL" = 1 ]; then
  echo "RESULT: NOT OFFLINE (see above). Unplug Ethernet and any uplink, then run again."; exit 1
elif [ "$UNKNOWN" = 1 ]; then
  echo "RESULT: UNKNOWN. Some probes could not run, so this is NOT a pass. Install the missing tools and run again."; exit 2
fi
echo "RESULT: no route out. Evidence saved to $OUT/offline_evidence.txt"
