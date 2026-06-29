"""
FACOM DX.TSCANPB — Sniffer port série COM9
Capture les données brutes envoyées par l'outil pour comprendre le protocole.
Ferme SCANDIAG avant de lancer ce script.
"""

import serial
import time
import sys
from pathlib import Path

PORT      = "COM15"
BAUDRATES = [115200, 57600, 38400, 19200, 9600]
TIMEOUT   = 3
DUMP_FILE = Path(__file__).parent / "capture_com9.bin"

JPEG_SOI  = bytes([0xFF, 0xD8])   # début JPEG
JPEG_EOI  = bytes([0xFF, 0xD9])   # fin JPEG


def try_baudrate(baud):
    try:
        ser = serial.Serial(PORT, baudrate=baud, timeout=TIMEOUT,
                            bytesize=8, parity='N', stopbits=1)
        print(f"  [{baud}] Port ouvert.")
        time.sleep(0.5)

        # Envoie un octet nul pour "réveiller" l'outil
        ser.write(b'\x00')
        time.sleep(0.3)

        data = ser.read(256)
        if data:
            print(f"  [{baud}] {len(data)} octets reçus → baud rate probable !")
            ser.close()
            return baud, data
        else:
            print(f"  [{baud}] Aucune réponse.")
        ser.close()
    except serial.SerialException as e:
        print(f"  [{baud}] Erreur : {e}")
    return None, None


def listen(baud, duration=30):
    """Écoute pendant `duration` secondes et sauvegarde tout."""
    print(f"\n[ÉCOUTE] COM9 @ {baud} baud pendant {duration}s…")
    print("  → Appuie sur le bouton de l'outil pour déclencher une mesure !\n")

    ser = serial.Serial(PORT, baudrate=baud, timeout=0.1,
                        bytesize=8, parity='N', stopbits=1)
    all_data = bytearray()
    jpeg_count = 0
    t0 = time.time()

    try:
        while time.time() - t0 < duration:
            chunk = ser.read(4096)
            if chunk:
                all_data.extend(chunk)
                # Cherche des images JPEG
                pos = 0
                while True:
                    start = all_data.find(JPEG_SOI, pos)
                    if start == -1:
                        break
                    end = all_data.find(JPEG_EOI, start + 2)
                    if end != -1:
                        jpeg_data = all_data[start:end + 2]
                        jpeg_count += 1
                        fname = Path(__file__).parent / f"frame_{jpeg_count:04d}.jpg"
                        fname.write_bytes(jpeg_data)
                        print(f"  [IMAGE] JPEG #{jpeg_count} trouvé ({len(jpeg_data)} octets) → {fname.name}")
                        pos = end + 2
                    else:
                        break

                # Affiche les premiers octets en hex pour analyse
                if len(all_data) % 1024 < len(chunk):
                    elapsed = time.time() - t0
                    preview = chunk[:16].hex(' ').upper()
                    print(f"  [{elapsed:5.1f}s] {len(all_data):6d} octets reçus | hex: {preview}…")
    except KeyboardInterrupt:
        print("\n[STOP] Interruption clavier.")
    finally:
        ser.close()

    # Sauvegarde le dump complet
    if all_data:
        DUMP_FILE.write_bytes(all_data)
        print(f"\n[DUMP] {len(all_data)} octets sauvegardés dans {DUMP_FILE.name}")
        if jpeg_count:
            print(f"[OK]   {jpeg_count} image(s) JPEG extraite(s) !")
        else:
            print("[INFO] Aucun JPEG trouvé — le protocole est peut-être encodé.")
            print("       Analyse hex des 64 premiers octets :")
            print("      ", all_data[:64].hex(' ').upper())
    else:
        print("[WARN] Aucune donnée reçue. Vérifie que SCANDIAG est bien fermé.")

    return all_data


def main():
    print("=" * 60)
    print("  FACOM DX.TSCANPB — Sniffer COM9")
    print("  ⚠  Ferme SCANDIAG avant de continuer !")
    print("=" * 60)
    input("\nAppuie sur Entrée quand SCANDIAG est fermé et l'outil allumé…")

    # Détecte le bon baud rate
    print("\n[1] Détection du baud rate…")
    found_baud = None
    for baud in BAUDRATES:
        b, data = try_baudrate(baud)
        if b:
            found_baud = b
            break

    if not found_baud:
        print("\n[INFO] Pas de réponse spontanée — on essaie avec 115200 par défaut.")
        found_baud = 115200

    # Écoute et capture
    data = listen(found_baud, duration=60)
    return len(data) > 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
