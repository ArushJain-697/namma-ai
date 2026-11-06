#!/usr/bin/env bash
# Classroom Hotspot: make the Pi its own Wi-Fi network with NO route to the internet, for phones to join.
#   sudo SSID=Sakshi PASS='a-password-you-choose' bash scripts/hotspot.sh up
#   sudo bash scripts/hotspot.sh down
# STATUS: UNTESTED. Needs a Raspberry Pi with NetworkManager (default on Trixie) and a Wi-Fi radio. Test it with
# 5 phones (iPhone and Android) before relying on it (build map T30). The terminal quiz covers every beat if it fails.
# Never an open network: a password is required, and there is no default one.
set -eu
CON="sakshi-hotspot"
IFACE="${IFACE:-wlan0}"
case "${1:-}" in
  up)
    : "${SSID:?set SSID, e.g. SSID=Sakshi}"; : "${PASS:?set PASS (8+ characters). There is no default password.}"
    [ "${#PASS}" -ge 8 ] || { echo "PASS must be at least 8 characters"; exit 2; }
    command -v nmcli >/dev/null || { echo "nmcli not found: this needs NetworkManager"; exit 2; }
    BAND="${BAND:-a}"; CHANNEL="${CHANNEL:-36}"   # 5 GHz, channel 36 is not a DFS channel. BAND=bg CHANNEL=6 for 2.4 GHz.
    nmcli connection delete "$CON" >/dev/null 2>&1 || true
    nmcli connection add type wifi ifname "$IFACE" con-name "$CON" autoconnect no ssid "$SSID" \
      802-11-wireless.mode ap 802-11-wireless.band "$BAND" 802-11-wireless.channel "$CHANNEL" \
      ipv4.method shared ipv4.addresses 10.42.0.1/24 wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PASS"
    nmcli connection up "$CON"
    echo; echo "Hotspot up. Phones join:  SSID=$SSID   then open  http://10.42.0.1:8000/"
    echo "Tell judges to TURN OFF MOBILE DATA and stay connected if the phone says 'no internet'."
    if awk 'NR>1 && $2=="00000000"{f=1} END{exit !f}' /proc/net/route; then
      echo "WARNING: this machine still has a default route (an uplink). Unplug Ethernet before the demo; run scripts/prove_offline.sh"
    else
      echo "Good: no default route, so nothing here can reach the internet."
    fi ;;
  down) nmcli connection down "$CON" && nmcli connection delete "$CON" && echo "Hotspot removed." ;;
  *) echo "usage: sudo SSID=... PASS=... bash scripts/hotspot.sh up | down"; exit 2 ;;
esac
