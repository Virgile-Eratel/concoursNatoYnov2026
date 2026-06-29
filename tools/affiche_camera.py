"""
FACOM DX.TSCANPB — Affichage camera depuis temp.raw
SCANDIAG écrit l'image brute dans C:\ProgramData\Facom\ScanDiag\temp.raw
Header : 12 octets  |  Image : 163840 octets bruts (grayscale)
"""

import cv2
import numpy as np
import time
from pathlib import Path

RAW_FILE = Path(r"C:\ProgramData\Facom\ScanDiag\temp.raw")
HEADER   = 12

# Dimensions candidates pour 163840 octets
DIMS = [
    (1280, 128),   # WXGA largeur × bande laser
    (640,  256),
    (512,  320),
    (320,  512),
]


def read_frame():
    try:
        data = RAW_FILE.read_bytes()
        payload = data[HEADER:]
        return payload
    except Exception:
        return None


def find_best_dims(payload):
    """Essaie chaque dimension et retourne la meilleure."""
    size = len(payload)
    for w, h in DIMS:
        if w * h == size:
            return w, h
    # Fallback : cherche des dimensions carrées approchantes
    sq = int(size ** 0.5)
    return sq, size // sq


def main():
    print("FACOM — Visualiseur temp.raw")
    print(f"Fichier : {RAW_FILE}")

    payload = read_frame()
    if payload is None:
        print("[ERREUR] Fichier introuvable. Lance SCANDIAG d'abord.")
        return

    w, h = find_best_dims(payload)
    print(f"Taille payload : {len(payload)} octets  →  {w}×{h} pixels")

    window = "FACOM Camera — temp.raw (Q pour quitter)"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, max(w * 3, 800), max(h * 3, 300))

    last_mtime = 0
    frame      = None

    print("\n[OK] Lance un Fast Check dans SCANDIAG pour voir l'image se mettre à jour.")
    print("     Appuie sur Q pour quitter.\n")

    while True:
        # Recharge si le fichier a changé
        try:
            mtime = RAW_FILE.stat().st_mtime
            if mtime != last_mtime:
                payload = read_frame()
                if payload and len(payload) >= w * h:
                    img = np.frombuffer(payload[:w * h], dtype=np.uint8).reshape(h, w)
                    pmax = int(img.max())
                    pmean = float(img.mean())
                    # Mise à l'échelle linéaire min→max (pas d'égalisation qui amplifie le bruit)
                    if pmax > 10:
                        img_scaled = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                    else:
                        # Signal très faible : amplifie ×8 pour voir le bruit de fond
                        img_scaled = np.clip(img.astype(np.uint16) * 8, 0, 255).astype(np.uint8)
                    # Agrandit l'image pour la rendre lisible
                    img_big = cv2.resize(img_scaled, (w * 3, h * 3), interpolation=cv2.INTER_NEAREST)
                    # Colorise (laser en jaune sur fond noir)
                    img_color = cv2.applyColorMap(img_big, cv2.COLORMAP_INFERNO)
                    frame = img_color
                    last_mtime = mtime
                    ts = time.strftime("%H:%M:%S")
                    signal = "LASER?" if pmax > 100 else ("faible" if pmax > 10 else "bruit")
                    print(f"[{ts}] Image mise à jour — max={pmax}  mean={pmean:.1f}  [{signal}]")
        except Exception as e:
            pass

        if frame is not None:
            cv2.imshow(window, frame)
        else:
            # Affiche un écran d'attente
            blank = np.zeros((200, 800, 3), dtype=np.uint8)
            cv2.putText(blank, "En attente de SCANDIAG...", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 200), 2)
            cv2.imshow(window, blank)

        key = cv2.waitKey(200) & 0xFF
        if key == ord('q') or key == 27:
            break
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
