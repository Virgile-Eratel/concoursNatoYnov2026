# `tools/` — Outils de rétro-ingénierie de la liaison SCANDIAG

Ce dossier regroupe les scripts utilisés pour **dialoguer avec le FACOM SCANDIAG et en extraire
les données** (images / mesures), dans le cadre de la Phase 1 (rétro-ingénierie) et de la préparation
du POC.

## Architecture de communication de l'outil

Le SCANDIAG ne fait pas de l'USB « image » classique : il expose **deux canaux, tous deux de type
série (UART)** vers le PC.

```
                    ┌───────────────────────────── SCANDIAG ─────────────────────────────┐
                    │  MCU  ──UART──┬── pont FTDI FT232R ──► USB Mini-B   (0403:6001)       │
                    │              └── module Bluetooth ──► radio 2.4 GHz (SPP)            │
                    └─────────────────────────────────────────────────────────────────────┘
                               │                                   │
                       câble USB │                          sans fil │
                               ▼                                   ▼
                  Port COM "USB Serial Port"        Port COM "Standard Serial over Bluetooth"
                  (canal service / firmware)        (canal de mesure utilisé par le logiciel)
                               │                                   │
                               └──────────────► PC ◄───────────────┘
                                      (logiciel SCANDIAG officiel, .NET)
```

Points établis pendant la rétro-ingénierie :

- En USB, l'outil énumère comme un **FTDI FT232R (VID `0x0403` / PID `0x6001`)**, pas comme le Cypress
  que laissaient supposer les drivers du CD (le `cyusb.inf` « Texa Uniprobe » concernait un autre
  produit TEXA). Le canal USB est donc un **port série virtuel**, vraisemblablement réservé au
  service / firmware (le manuel indique la prise USB « charge / service uniquement »).
- En Bluetooth, l'outil s'annonce en **Bluetooth Classic / SPP** sous le nom **`LSG1MT6LT000889`**
  (numéro de série 000889) et crée, après appairage, un **port COM série** côté Windows. C'est le
  canal qu'utilise le logiciel officiel pour récupérer les acquisitions.

Conséquence pratique : **dans les deux cas on se ramène à lire un port COM série**, ce que font les
scripts ci-dessous.

## Contenu du dossier

### `serial_dump.py` — écoute du port série (outil principal)
Ouvre un port COM (FTDI en USB **ou** SPP Bluetooth) avec *pyserial*, teste plusieurs débits
(`--scan-baud`), capture le flux brut et tente d'en découper des images JPEG.
```bash
pip install pyserial
python serial_dump.py --list                    # liste les ports COM
python serial_dump.py --scan-baud --port COM3    # trouve le bon débit (déclencher une mesure pendant)
python serial_dump.py --port COM3 --baud 115200 --seconds 20 --out serial.bin
```
À privilégier une fois qu'un port COM (USB ou Bluetooth) est disponible.

### `usb_dump.py` — sondage USB bas niveau (diagnostic)
Énumère le périphérique via *pyusb/libusb* et lit ses endpoints. C'est ce script qui a **révélé que
l'outil est un FTDI** et non un Cypress. Sous Windows, il exige de rebinder le device sur WinUSB/libusbK
via **Zadig**, ce qui coupe temporairement le logiciel officiel — à n'utiliser que pour le diagnostic.
```bash
pip install pyusb libusb
python usb_dump.py --list
```

### `ftdi_extract.py` — reconstruction depuis une capture Wireshark
Quand l'écoute passive ne donne rien (l'outil n'émet qu'**après une commande** du logiciel officiel),
on capture l'échange au niveau USB avec **Wireshark + USBPcap** pendant un scan, puis ce script
reconstitue le flux série. Il **retire les 2 octets de statut que le FTDI insère en tête de chaque
paquet entrant** (sinon le flux est corrompu) et découpe les JPEG.
```bash
# export depuis la capture
tshark -r scan.pcapng -Y "usb.capdata && usb.dst==\"host\"" -T fields -e usb.capdata > in_hex.txt
python ftdi_extract.py in_hex.txt --strip 2 --out tool_stream.bin
```

## Logique d'ensemble (du plus simple au plus sûr)

1. **Identifier le canal** : USB (`usb_dump.py --list`) ou Bluetooth (appairer → port COM).
2. **Écouter en passif** sur le port COM (`serial_dump.py --scan-baud`) en déclenchant une mesure.
3. **Si rien ne sort** : l'outil attend une commande d'amorçage → **sniffer le logiciel officiel**
   avec Wireshark, reconstituer le flux (`ftdi_extract.py`) et récupérer **la commande de
   déclenchement** (sens host→device) pour la **rejouer** ensuite avec `serial_dump.py`.

## Dépendances

- Python 3, `pyserial` (serial_dump), `pyusb` + `libusb` (usb_dump).
- Wireshark avec composant **USBPcap** (capture), `tshark` (export).
- Optionnel : **Zadig** (binding WinUSB/libusbK pour la voie pyusb).
