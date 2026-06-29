"""
Proxy "homme du milieu" : SCANDIAG <-> COM20 <-> [ce script] <-> COM15 <-> FACOM
Logue tout le trafic et cherche des images JPEG.
Pré-requis : com0com installé avec la paire COM20 <-> COM21
             SCANDIAG configuré sur COM20
"""

import serial
import threading
import time
from pathlib import Path

DEVICE_PORT  = "COM15"   # port réel vers l'outil FACOM
PROXY_PORT   = "COM21"   # côté script de la paire com0com (SCANDIAG utilise COM20)
BAUD         = 115200
LOG_DIR      = Path(__file__).parent / "mitm_logs"
LOG_DIR.mkdir(exist_ok=True)

log_raw   = open(LOG_DIR / "raw_traffic.bin", "wb")
jpeg_count = [0]

JPEG_SOI = bytes([0xFF, 0xD8])
JPEG_EOI = bytes([0xFF, 0xD9])
buf_device = bytearray()


def save_jpegs(data: bytes, direction: str):
    global jpeg_count
    pos = 0
    while True:
        start = data.find(JPEG_SOI, pos)
        if start == -1:
            break
        end = data.find(JPEG_EOI, start + 2)
        if end != -1:
            jpeg_count[0] += 1
            fname = LOG_DIR / f"{direction}_frame_{jpeg_count[0]:04d}.jpg"
            fname.write_bytes(data[start:end + 2])
            print(f"  [IMAGE] {direction} JPEG #{jpeg_count[0]} ({end-start} octets) → {fname.name}")
            pos = end + 2
        else:
            break


def relay(src: serial.Serial, dst: serial.Serial, direction: str):
    """Lit de src, écrit dans dst, logue tout."""
    while True:
        try:
            data = src.read(4096)
            if data:
                dst.write(data)
                log_raw.write(data)
                log_raw.flush()
                ts = time.strftime("%H:%M:%S")
                preview = data[:24].hex(' ').upper()
                print(f"[{ts}] {direction:20s} {len(data):5d} octets | {preview}")
                save_jpegs(data, direction)
        except Exception as e:
            print(f"[ERREUR {direction}] {e}")
            break


def main():
    print("=" * 60)
    print("  FACOM MITM Proxy")
    print(f"  SCANDIAG → COM20 → COM21(proxy) → COM15 → FACOM")
    print("=" * 60)
    print(f"\n[INFO] Logs dans : {LOG_DIR}")
    print("[INFO] Configure SCANDIAG sur COM20, puis lance-le.\n")

    dev  = serial.Serial(DEVICE_PORT, BAUD, timeout=0.05)
    prx  = serial.Serial(PROXY_PORT,  BAUD, timeout=0.05)
    print(f"[OK] {DEVICE_PORT} et {PROXY_PORT} ouverts. En attente de trafic…\n")

    t1 = threading.Thread(target=relay, args=(prx, dev, "SCANDIAG→FACOM"), daemon=True)
    t2 = threading.Thread(target=relay, args=(dev, prx, "FACOM→SCANDIAG"), daemon=True)
    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] Proxy arrêté.")
        log_raw.close()


if __name__ == "__main__":
    main()
