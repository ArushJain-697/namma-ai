#!/usr/bin/env python3
"""Make the two QR cards to print BEFORE the event (never generate QR codes live): join the Wi-Fi, open the page.

  python scripts/make_qr_cards.py --ssid Sakshi --password 'the-password' [--url http://10.42.0.1:8000/] [--out print]
Writes print/join_wifi.svg and print/open_page.svg (needs `pip install qrcode`; any QR tool works with the two strings
this prints). Do not commit the password.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from sakshi.qr import wifi_string  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--ssid", required=True)
p.add_argument("--password", required=True)
p.add_argument("--url", default="http://10.42.0.1:8000/")
p.add_argument("--out", default="print")
a = p.parse_args()
w = wifi_string(a.ssid, a.password)
print("Wi-Fi QR string:", w)
print("Page QR string: ", a.url)
try:
    import qrcode
    import qrcode.image.svg
except ImportError:
    sys.exit("qrcode is not installed (pip install qrcode). Paste the two strings above into any offline QR generator.")
os.makedirs(a.out, exist_ok=True)
for name, data in (("join_wifi", w), ("open_page", a.url)):
    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage)
    img.save(os.path.join(a.out, name + ".svg"))
    print("wrote", os.path.join(a.out, name + ".svg"))
print("Also print: 'Turn OFF mobile data. If your phone says no internet, stay connected.'")
