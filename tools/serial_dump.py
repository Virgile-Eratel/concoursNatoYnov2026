#!/usr/bin/env python3
"""
serial_dump.py — Écoute le FACOM SCANDIAG sur son port série FTDI (FT232R, 0403:6001).

L'outil communique avec le PC via un pont USB-série FTDI : côté Windows il apparaît
comme "USB Serial Port (COMx)". Ce script ouvre ce port et enregistre tout ce que
l'outil envoie pendant une mesure. Il teste aussi plusieurs débits (baud) pour
trouver le bon, et tente de découper des images JPEG dans le flux.

⚠️ Il faut le driver FTDI VCP (port COM), PAS un binding Zadig/libusbK.

Pré-requis :
    pip install pyserial

Usage :
    python serial_dump.py --list                       # liste les ports COM
    python serial_dump.py --scan-baud --port COM3       # teste plusieurs débits
    python serial_dump.py --port COM3 --baud 115200 --seconds 20 --out serial.bin
"""

import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial manquant -> pip install pyserial")

COMMON_BAUDS = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000, 3000000]


def list_serial_ports():
    print("=== Ports série détectés ===")
    ports = list(list_ports.comports())
    if not ports:
        print("  (aucun) — branche l'outil et installe le driver FTDI VCP (port COM).")
        return
    for p in ports:
        vidpid = f"{p.vid:04x}:{p.pid:04x}" if p.vid else "?"
        print(f"  {p.device:8s} | {p.description} | VID:PID {vidpid}")
        if p.vid == 0x0403:
            print("           ^-- FTDI : c'est très probablement le SCANDIAG.")


def hexdump(data, n=64):
    b = bytes(data[:n])
    hx = " ".join(f"{x:02x}" for x in b)
    asc = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
    return f"{hx}\n  ascii: {asc}"


def read_for(port, baud, seconds):
    """Ouvre le port, lit pendant `seconds`, retourne les octets reçus."""
    buf = bytearray()
    try:
        ser = serial.Serial(port, baud, timeout=0.5)
    except serial.SerialException as e:
        print(f"  ouverture {port}@{baud} impossible : {e}")
        return buf
    with ser:
        ser.reset_input_buffer()
        t_end = time.time() + seconds
        while time.time() < t_end:
            data = ser.read(4096)
            if data:
                buf.extend(data)
    return buf


def scan_baud(port, seconds=4):
    print(f"=== Test des débits sur {port} ({seconds}s chacun) ===")
    print(">>> Déclenche une mesure (bouton + laser) pendant le test ! <<<\n")
    best = None
    for baud in COMMON_BAUDS:
        data = read_for(port, baud, seconds)
        printable = sum(1 for x in data if 9 <= x <= 126)
        ratio = (printable / len(data)) if data else 0
        flag = ""
        if data and (best is None or len(data) > best[1]):
            best = (baud, len(data))
            flag = "  <-- le plus de données"
        print(f"  {baud:>8} baud : {len(data):>7} octets  (texte ~{ratio:.0%}){flag}")
        if data:
            print(f"      {hexdump(data)}")
    if best:
        print(f"\nMeilleur candidat : {best[0]} baud. Relance avec --baud {best[0]} pour capturer.")
    else:
        print("\nRien reçu à aucun débit. L'outil n'émet peut-être qu'après une commande "
              "spécifique -> envisage le sniff du logiciel officiel (Wireshark/serial monitor).")


def carve_jpegs(data, prefix="frame"):
    count, start = 0, 0
    while True:
        soi = data.find(b"\xff\xd8\xff", start)
        if soi < 0:
            break
        eoi = data.find(b"\xff\xd9", soi)
        if eoi < 0:
            break
        with open(f"{prefix}_{count:03d}.jpg", "wb") as f:
            f.write(data[soi:eoi + 2])
        print(f"  -> image JPEG : {prefix}_{count:03d}.jpg ({eoi + 2 - soi} octets)")
        count += 1
        start = eoi + 2
    if count == 0:
        print("  (aucun JPEG — peut-être du RAW 1280x800, ou du protocole/profil et pas une photo)")
    return count


def main():
    ap = argparse.ArgumentParser(description="Dump série du FACOM SCANDIAG (FTDI)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--scan-baud", action="store_true")
    ap.add_argument("--port", help="ex: COM3")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--out", default="serial.bin")
    args = ap.parse_args()

    if args.list:
        list_serial_ports()
        return
    if not args.port:
        print("Précise --port COMx (voir --list).")
        list_serial_ports()
        return
    if args.scan_baud:
        scan_baud(args.port)
        return

    print(f"=== Capture {args.port} @ {args.baud} baud pendant {args.seconds}s ===")
    print(">>> DÉCLENCHE UNE MESURE MAINTENANT (bouton + laser sur surface mate) <<<")
    data = read_for(args.port, args.baud, args.seconds)
    print(f"\nReçu : {len(data)} octets")
    if data:
        with open(args.out, "wb") as f:
            f.write(data)
        print(f"Brut enregistré : {args.out}")
        print(f"Aperçu :\n  {hexdump(data)}")
        print("Recherche d'images JPEG...")
        carve_jpegs(data)
    else:
        print("Rien reçu. Essaie --scan-baud, garde l'outil réveillé (bouton), "
              "et vérifie que le logiciel officiel n'occupe pas déjà le port COM.")


if __name__ == "__main__":
    main()
