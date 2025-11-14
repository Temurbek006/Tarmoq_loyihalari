import subprocess
import re
import json
from datetime import datetime

def scan_windows_once():
    """Windows tizimida Wi-Fi tarmoqlarni aniqlaydi"""
    proc = subprocess.run(
        ["netsh", "wlan", "show", "networks", "mode=bssid"],
        capture_output=True, text=True, shell=False
    )
    return proc.stdout

def parse_windows_output(output):
    """Netsh chiqishini tahlil qiladi va tarmoqlar ro‘yxatini qaytaradi"""
    networks = []
    current = {}
    ssid_re = re.compile(r'^\s*SSID\s+\d+\s+:\s*(.*)$')
    bssid_re = re.compile(r'^\s*BSSID\s+\d+\s+:\s*(.*)$')
    signal_re = re.compile(r'^\s*Signal\s+:\s*(\d+)%')
    auth_re = re.compile(r'^\s*Authentication\s+:\s*(.*)$')
    enc_re = re.compile(r'^\s*Encryption\s+:\s*(.*)$')

    for line in output.splitlines():
        m = ssid_re.match(line)
        if m:
            if current:
                networks.append(current)
            current = {
                "Tarmoq nomi": m.group(1).strip(),
                "MAC manzil": None,
                "Signal kuchi (%)": None,
                "Autentifikatsiya turi": None,
                "Shifrlash turi": None
            }
            continue

        m = bssid_re.match(line)
        if m:
            current["MAC manzil"] = m.group(1).strip()
            continue

        m = signal_re.match(line)
        if m:
            current["Signal kuchi (%)"] = int(m.group(1))
            continue

        m = auth_re.match(line)
        if m:
            current["Autentifikatsiya turi"] = m.group(1).strip()
            continue

        m = enc_re.match(line)
        if m:
            current["Shifrlash turi"] = m.group(1).strip()
            continue

    if current:
        networks.append(current)

    return networks

def scan_and_print():
    """Wi-Fi tarmoqlarni aniqlab, natijani JSON shaklida chiqaradi"""
    output = scan_windows_once()
    networks = parse_windows_output(output)

    vaqt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # faqat sana, soat, minut, sekund

    results = []
    for net in networks:
        entry = {"Vaqt": vaqt, **net}
        results.append(entry)

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    scan_and_print()
