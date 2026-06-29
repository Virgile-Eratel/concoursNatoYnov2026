#!/usr/bin/env python3
"""
ftdi_extract.py — Reconstruit le flux série du SCANDIAG depuis une capture Wireshark USB.

Quand on sniffe l'outil au niveau USB (USBPcap), les données série FTDI arrivent dans
des transferts bulk. PROBLÈME FTDI : chaque paquet USB entrant (device -> PC) commence
par 2 octets de statut (modem status + line status) qu'il faut RETIRER pour reconstituer
le vrai flux série. Ce script fait ça, concatène, sauvegarde, et découpe les JPEG.

Procédure :
  1. Capturer avec Wireshark (USBPcap) pendant une mesure du logiciel officiel.
  2. Exporter les charges utiles avec tshark :

     # données venant de l'outil (IN, device -> host) = l'image / les mesures
     tshark -r scan.pcapng -Y "usb.capdata && usb.dst==\"host\"" -T fields -e usb.capdata > in_hex.txt

     # commandes envoyées par le logiciel (OUT, host -> device) = le déclencheur à rejouer
     tshark -r scan.pcapng -Y "usb.capdata && usb.src==\"host\"" -T fields -e usb.capdata > out_hex.txt

  3. Reconstruire :
     python ftdi_extract.py in_hex.txt  --strip 2 --out tool_stream.bin
     python ftdi_extract.py out_hex.txt --strip 0 --out pc_commands.bin

Le fichier hex de tshark contient une ligne par paquet, en hexadécimal continu
(ex: "01600102ff..."). --strip 2 enlève les 2 octets de statut FTDI par ligne (sens IN).
Pour le sens OUT (PC -> outil), pas de statut : --strip 0.
"""

import argparse
import sys


def load_hex(path, strip):
    raw = bytearray()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip().replace(":", "").replace(" ", "")
            if not line:
                continue
            try:
                pkt = bytes.fromhex(line)
            except ValueError:
                continue
            raw.extend(pkt[strip:] if len(pkt) > strip else b"")
    return raw


def carve_jpegs(data, prefix="frame"):
    count, start = 0, 0
    while True:
        soi = data.find(b"\xff\xd8\xff", start)
        if soi < 0:
            break
        eoi = data.find(b"\xff\xd9", soi)
        if eoi < 0:
            break
        with open(f"{prefix}_{count:03d}.jpg", "wb") as fp:
            fp.write(data[soi:eoi + 2])
        print(f"  -> image JPEG : {prefix}_{count:03d}.jpg ({eoi + 2 - soi} octets)")
        count += 1
        start = eoi + 2
    return count


def preview(data, n=96):
    b = bytes(data[:n])
    hx = " ".join(f"{x:02x}" for x in b)
    asc = "".join(chr(x) if 32 <= x < 127 else "." for x in b)
    print(f"  hex  : {hx}")
    print(f"  ascii: {asc}")


def main():
    ap = argparse.ArgumentParser(description="Reconstruit le flux série depuis un export tshark")
    ap.add_argument("hexfile", help="fichier hex exporté par tshark (-e usb.capdata)")
    ap.add_argument("--strip", type=int, default=2,
                    help="octets de statut FTDI à retirer par paquet (2 pour IN, 0 pour OUT)")
    ap.add_argument("--out", default="stream.bin")
    args = ap.parse_args()

    try:
        data = load_hex(args.hexfile, args.strip)
    except FileNotFoundError:
        sys.exit(f"Fichier introuvable : {args.hexfile}")

    print(f"Flux reconstruit : {len(data)} octets (statut FTDI retiré : {args.strip}/paquet)")
    if not data:
        sys.exit("Vide — vérifie le filtre tshark et le sens IN/OUT.")
    with open(args.out, "wb") as f:
        f.write(data)
    print(f"Enregistré : {args.out}\nAperçu :")
    preview(data)

    print("\nRecherche d'images JPEG...")
    if carve_jpegs(data) == 0:
        print("  (aucun JPEG) Indices de taille pour du RAW OV9712 :")
        print(f"    1280x800 mono/Y8 = 1 024 000 o | RAW16/RGB565 = 2 048 000 o")
        print(f"    640x480 mono     =   307 200 o | 320x240 mono =    76 800 o")
        print(f"    -> reçu {len(data)} o : compare aux tailles ci-dessus pour deviner le format.")


if __name__ == "__main__":
    main()
