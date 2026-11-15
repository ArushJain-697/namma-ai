#!/usr/bin/env bash
# Put passages on the device for Study -> Saved pages. Run on your laptop while the Pi is reachable, then you can
# disconnect: the device lists and runs them on its own.
#
#   pi/send_passages.sh judge1.txt judge2.txt     copy .txt files
#   pi/send_passages.sh --paste judge1             save the clipboard as judge1.txt (macOS: pbpaste)
#   pi/send_passages.sh --list                     show what is on the device
#   pi/send_passages.sh --clear                    remove all passages from the device
set -euo pipefail
PI="${SAKSHI_PI:-vishnu@vsc.local}"
DIR="passages"
ssh -o ConnectTimeout=8 "$PI" "mkdir -p ~/$DIR"
case "${1:-}" in
  --paste)
    name="${2:?give a name, e.g. --paste judge1}"
    pbpaste | ssh "$PI" "cat > ~/$DIR/${name%.txt}.txt"
    echo "saved clipboard as ~/$DIR/${name%.txt}.txt" ;;
  --list)  ssh "$PI" "cd ~/$DIR && wc -w *.txt 2>/dev/null || echo '(no passages)'" ;;
  --clear) ssh "$PI" "rm -f ~/$DIR/*.txt" && echo "cleared ~/$DIR" ;;
  "")      sed -n '2,9p' "$0" ;;
  *)       scp -q "$@" "$PI:$DIR/" && echo "sent $# file(s) to ~/$DIR" ;;
esac
