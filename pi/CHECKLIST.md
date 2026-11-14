# Pi day checklist (print this)

The kit folder (`pi-kit/`, ~2 GB) holds everything: packages for Python 3.11 / 3.12 / 3.13, the Qwen3-0.6B models
(fast for Pi 5, portable for older chips), the helper models, and the project code. **No internet needed.**

## Before leaving home
- [ ] Copy `pi-kit/` to a USB stick (exFAT or ext4; FAT32 fails on files over 4 GB, ours are under 1 GB but use exFAT).
- [ ] Also copy it to the laptop (second copy) and charge everything.
- [ ] USB-C power supply for the Pi 5 (27 W official), a fan/heatsink, micro-SD reader, HDMI adapter, Ethernet cable.

## At the venue (about 20 minutes)
1. **Get a terminal on the Pi** (keyboard + screen, or SSH from the laptop over Ethernet/same Wi-Fi):
   `ssh pi@<ip>` (find the IP on the Pi with `hostname -I`).
2. **Copy the kit**: plug in the USB stick, then
   `cp -r /media/$USER/<stick>/pi-kit ~/` (or `scp -r pi-kit pi@<ip>:~/` from the laptop).
3. **Install**: `cd ~/pi-kit && bash install.sh`. Read the 7 steps; every one should say OK.
4. **Test**: `bash test.sh`. Write down: load time, reading speed, writing speed, total time, peak memory.
5. **Organiser passage**: save it as `~/passage.txt`, then `bash test.sh ~/passage.txt`.
6. **Offline proof for judges**: unplug Ethernet / turn Wi-Fi off (`sudo nmcli radio wifi off`), run `bash test.sh`
   again, show the "no route out" line.

## If a step fails

| Step / message | What it means | Fix |
|---|---|---|
| 1: "not a 64-bit ARM OS" | 32-bit Raspberry Pi OS | Ask organisers for 64-bit OS image; nothing else works on 32-bit |
| 1: "no packages for Python NN" | Pi has a Python we did not pack (e.g. 3.10 or 3.14) | If there is internet: `python3 -m venv ~/sakshi-venv && ~/sakshi-venv/bin/pip install executorch==1.5.1 torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple` then rerun install.sh. No internet: try `sudo apt install python3.11` if the image has it cached; else ask for a Pi OS Bookworm (3.11) or Trixie (3.13) image |
| 2: "could not create venv" | venv module missing | `sudo apt install python3-venv` (needs internet) or use `python3 -m pip install --user --no-index --find-links wheels/pyNN ...` without a venv |
| 3: install error | wrong kit copy or disk full | `df -h ~` (needs ~3 GB free); recopy the kit |
| 4: "runner import failed" | torch/executorch mismatch | Check `install.log`; the kit pins torch 2.14.1+cpu with executorch 1.5.1, do not let pip pull another torch |
| 6: "model file is corrupted" | bad copy | Recopy `pi-kit/models/` from the laptop copy |
| test 1: "Illegal instruction" | chip lacks dot-product (Pi 4 = Cortex-A72) but the fast model was chosen | Edit `~/namma-ai/.kit_model` to `MODEL_DIR=$HOME/namma-ai/models/qwen3-0.6b-portable` and rerun |
| test 1: killed / out of memory | another program using RAM, or swap off | Close the desktop, `free -m`; both models need ~1.7 GB |
| test 1: very slow writing (under 2 tokens/s) on a Pi 5 | portable model chosen, or CPU throttling | Check `.kit_model` says fast; check `vcgencmd get_throttled` is `0x0`; add the fan; use the official power supply |
| test 2: fewer than 3 questions | quiz checks rejected too many | Normal for the plain model; the fine-tuned model fixes this. Rerun with another passage to confirm the pipeline itself works |

## What the judges asked for (fill in on the day)
| | Value |
|---|---|
| Board, RAM | |
| Model | Qwen3-0.6B, ExecuTorch 8da4w (4-bit weights), XNNPACK |
| Model file size | 469 MB (fast) / 470 MB (portable) |
| Load time | |
| Reading speed (tokens/s) | |
| Writing speed (tokens/s) | |
| Total time for summary + quiz | |
| Peak memory | |
| Offline proof | "no route out" |

## Known facts from rehearsals
- Arduino UNO Q (Cortex-A53, no dot-product): the fast model crashes ("Illegal instruction"); the portable model
  works but writes at ~0.4 tokens/s (a full run took 56 minutes). A Pi 5 (Cortex-A76) has dot-product: use fast.
- Apple M4 (same fast model): ~95 tokens/s writing, ~830 tokens/s reading, whole run ~20 s, peak memory 1.7 GB.
- Run the Pi with the fan on and record the second run, not the first: a Pi 5 without cooling slows down as it heats.
- The fast model has never run on Linux ARM yet: if it fails on the Pi 5, the portable one is the fallback.
