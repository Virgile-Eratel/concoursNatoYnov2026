#!/usr/bin/env python3
"""
usb_dump.py — Énumère le FACOM SCANDIAG en USB et tente de récupérer une image.

Contexte : l'outil énumère comme une puce Cypress CYUSB (VID 0x04b4 / PID 0x1003,
nom "Texa Uniprobe"). Ce script liste sa configuration USB (interfaces, endpoints),
puis lit en boucle les endpoints IN (bulk/interrupt) et enregistre le flux brut.
Il cherche aussi des images JPEG (marqueurs FFD8...FFD9) et les découpe.

⚠️ WINDOWS : libusb/pyusb ne peut pas accéder au device tant que le driver Cypress
est installé dessus. Il faut d'abord rebinder le device sur WinUSB/libusbK avec Zadig
(https://zadig.akeo.ie/). Cela coupe temporairement le logiciel SCANDIAG officiel.

Pré-requis :
    pip install pyusb
    # backend libusb : pip install libusb  (fournit la DLL)  OU  installer libusb-1.0.

Usage :
    python usb_dump.py                 # cible 04b4:1003 par défaut
    python usb_dump.py --list          # liste tous les périphériques USB
    python usb_dump.py --vid 0x04b4 --pid 0x1003 --seconds 20 --out capture.bin
"""

import argparse
import sys
import time

try:
    import usb.core
    import usb.util
except ImportError:
    sys.exit("pyusb manquant -> pip install pyusb (et un backend libusb : pip install libusb)")


def list_all():
    print("=== Périphériques USB visibles par libusb ===")
    found = False
    for dev in usb.core.find(find_all=True):
        found = True
        try:
            man = usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else "?"
            prod = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "?"
        except Exception:
            man = prod = "(lecture chaîne impossible)"
        print(f"  VID:PID = {dev.idVendor:04x}:{dev.idProduct:04x}  | {man} - {prod}")
    if not found:
        print("  (aucun) — sous Windows, vérifie que le device est bindé sur WinUSB/libusbK via Zadig.")


def describe(dev):
    print(f"\n=== Device {dev.idVendor:04x}:{dev.idProduct:04x} ===")
    for cfg in dev:
        print(f"Configuration {cfg.bConfigurationValue} :")
        for intf in cfg:
            print(f"  Interface {intf.bInterfaceNumber}, alt {intf.bAlternateSetting}, "
                  f"classe 0x{intf.bInterfaceClass:02x}")
            for ep in intf:
                direction = "IN " if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
                ep_types = {0: "control", 1: "isoc", 2: "bulk", 3: "interrupt"}
                ep_type = ep_types.get(usb.util.endpoint_type(ep.bmAttributes), "?")
                print(f"    EP 0x{ep.bEndpointAddress:02x}  {direction}  {ep_type}  "
                      f"maxpkt={ep.wMaxPacketSize}")


def in_endpoints(dev):
    eps = []
    for cfg in dev:
        for intf in cfg:
            for ep in intf:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    t = usb.util.endpoint_type(ep.bmAttributes)
                    if t in (2, 3):  # bulk ou interrupt
                        eps.append(ep)
    return eps


def carve_jpegs(data, prefix="frame"):
    """Découpe les images JPEG (SOI FFD8 ... EOI FFD9) trouvées dans le flux brut."""
    count = 0
    start = 0
    while True:
        soi = data.find(b"\xff\xd8\xff", start)
        if soi < 0:
            break
        eoi = data.find(b"\xff\xd9", soi)
        if eoi < 0:
            break
        jpg = data[soi:eoi + 2]
        fname = f"{prefix}_{count:03d}.jpg"
        with open(fname, "wb") as f:
            f.write(jpg)
        print(f"  -> image JPEG extraite : {fname} ({len(jpg)} octets)")
        count += 1
        start = eoi + 2
    if count == 0:
        print("  (aucun marqueur JPEG trouvé — l'image est peut-être en RAW Bayer 1280x800, "
              "voir note RAW en bas de fichier)")
    return count


def main():
    ap = argparse.ArgumentParser(description="Dump USB du FACOM SCANDIAG")
    ap.add_argument("--vid", default="0x04b4")
    ap.add_argument("--pid", default="0x1003")
    ap.add_argument("--seconds", type=float, default=15.0, help="durée de lecture")
    ap.add_argument("--out", default="capture.bin", help="fichier de sortie brut")
    ap.add_argument("--list", action="store_true", help="liste tous les périphériques USB")
    args = ap.parse_args()

    if args.list:
        list_all()
        return

    vid, pid = int(args.vid, 16), int(args.pid, 16)
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        print(f"Device {vid:04x}:{pid:04x} introuvable.\n")
        list_all()
        print("\nWindows : binder le device sur WinUSB/libusbK via Zadig, puis relancer.")
        return

    # Détache le driver noyau (Linux/Mac). Sous Windows, libusbK/WinUSB gère déjà.
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except (NotImplementedError, usb.core.USBError):
        pass

    try:
        dev.set_configuration()
    except usb.core.USBError as e:
        print(f"set_configuration a échoué : {e}")
        print("Driver mal bindé ? (Zadig) ou device occupé par le logiciel officiel.")
        return

    describe(dev)

    eps = in_endpoints(dev)
    if not eps:
        print("\nAucun endpoint IN bulk/interrupt — l'image transite peut-être par "
              "isochrone (UVC) ou Bluetooth. Voir le guide de capture Wireshark.")
        return

    ep = eps[0]
    print(f"\n=== Lecture sur EP 0x{ep.bEndpointAddress:02x} pendant {args.seconds}s ===")
    print(">>> DÉCLENCHE UNE MESURE MAINTENANT (bouton + laser sur une surface mate) <<<")
    buf = bytearray()
    t_end = time.time() + args.seconds
    chunk = ep.wMaxPacketSize * 64
    while time.time() < t_end:
        try:
            data = dev.read(ep.bEndpointAddress, chunk, timeout=1000)
            buf.extend(data.tobytes() if hasattr(data, "tobytes") else bytes(data))
            print(f"\r  reçu : {len(buf)} octets", end="", flush=True)
        except usb.core.USBError as e:
            if "timeout" in str(e).lower():
                continue
            print(f"\n  USBError : {e}")
            break

    print(f"\n\nTotal reçu : {len(buf)} octets")
    if buf:
        with open(args.out, "wb") as f:
            f.write(buf)
        print(f"Flux brut enregistré : {args.out}")
        print("Recherche d'images JPEG...")
        carve_jpegs(buf)
    else:
        print("Rien reçu. L'image ne sort pas sur cet endpoint sans une commande de "
              "déclenchement spécifique (protocole propriétaire) -> privilégie la capture "
              "Wireshark pendant que le logiciel officiel fait un scan.")


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# NOTE RAW : l'OV9712 sort du RAW RGB (Bayer), pas forcément du JPEG. Si le .bin
# ne contient pas de JPEG mais ~2 Mo (1280*800*2 ≈ 2 048 000) ou ~1 Mo
# (1280*800 = 1 024 000), c'est probablement une trame RAW/Y8. Pour la visualiser :
#   python -c "import numpy as np,cv2; raw=np.fromfile('capture.bin',np.uint8)[:1024000]; \
#              img=raw.reshape(800,1280); cv2.imwrite('frame.png', img)"
# (ajuste l'offset/dimensions ; teste aussi reshape(800,1280) en Bayer + cv2.cvtColor
#  COLOR_BAYER_*2BGR pour la couleur)
# ---------------------------------------------------------------------------
