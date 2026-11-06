"""The Wi-Fi join string for a QR code (the format phones understand): WIFI:T:WPA;S:<ssid>;P:<password>;;"""


def _esc(s: str) -> str:
    for ch in ("\\", ";", ",", ":", '"'):
        s = s.replace(ch, "\\" + ch)
    return s


def wifi_string(ssid: str, password: str, security: str = "WPA") -> str:
    return f"WIFI:T:{security};S:{_esc(ssid)};P:{_esc(password)};;"
