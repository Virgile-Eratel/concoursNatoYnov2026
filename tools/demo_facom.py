"""
FACOM DX.TSCANPB — Démonstration caméra laser
Affiche en temps réel le flux caméra depuis temp.raw
Pointe l'outil sur n'importe quelle surface et déclenche depuis SCANDIAG.

Commandes :
  ESPACE   → Capturer et sauvegarder la photo
  Q / ESC  → Quitter
"""

import cv2
import numpy as np
import time
from pathlib import Path
from datetime import datetime

RAW_FILE = Path(r"C:\ProgramData\Facom\ScanDiag\temp.raw")
SAVE_DIR = Path(__file__).parent / "captures"
SAVE_DIR.mkdir(exist_ok=True)

HEADER = 12
W, H   = 1280, 128
SCALE     = 4    # hauteur agrandie ×4 pour un rendu lisible
PROFILE_H = 200  # hauteur de la zone profil laser
WIN_W     = 1280
WIN_H     = H * SCALE + PROFILE_H + 60


def read_raw():
    """Lit temp.raw et retourne l'image numpy brute (H×W uint8) ou None."""
    try:
        data = RAW_FILE.read_bytes()
        payload = data[HEADER:]
        if len(payload) < W * H:
            return None
        return np.frombuffer(payload[:W * H], dtype=np.uint8).reshape(H, W)
    except Exception:
        return None


def render(img_raw, label="", saved_path=None):
    """Affiche : image laser colorisée + profil en courbe + barre de statut."""
    pmax = img_raw.max()
    if pmax > 10:
        scaled = cv2.normalize(img_raw, None, 0, 255, cv2.NORM_MINMAX)
    else:
        scaled = np.clip(img_raw.astype(np.uint16) * 8, 0, 255).astype(np.uint8)

    # ── Zone 1 : image laser colorisée (1280×256) ─────────────────────
    tall    = cv2.resize(scaled, (W, H * SCALE), interpolation=cv2.INTER_LINEAR)
    colored = cv2.applyColorMap(tall, cv2.COLORMAP_INFERNO)

    # ── Zone 2 : profil laser = position verticale du max par colonne ─
    profile_area = np.zeros((PROFILE_H, W, 3), dtype=np.uint8)
    profile_area[:] = (15, 15, 15)
    # Grille horizontale
    for py in range(0, PROFILE_H, PROFILE_H // 4):
        cv2.line(profile_area, (0, py), (W, py), (40, 40, 40), 1)
    # Calcule la position du max par colonne (= position laser = profil 3D)
    col_max_val = img_raw.max(axis=0)          # intensité max par colonne
    col_max_row = img_raw.argmax(axis=0)       # ligne où est le max (0=haut=proche)
    # Normalise : row 0 → profil haut (proche), row H-1 → bas (loin)
    col_y = ((col_max_row / (H - 1)) * (PROFILE_H - 10)).astype(int) + 5
    # Dessine la courbe (seulement là où le signal est suffisant)
    threshold = max(pmax * 0.15, 5)
    pts = []
    for x in range(W):
        if col_max_val[x] >= threshold:
            pts.append((x, int(col_y[x])))
    if len(pts) > 1:
        for i in range(len(pts) - 1):
            if abs(pts[i+1][0] - pts[i][0]) <= 2:   # évite les sauts
                cv2.line(profile_area, pts[i], pts[i+1], (0, 255, 120), 2)
        for x, y in pts:
            cv2.circle(profile_area, (x, y), 1, (0, 255, 200), -1)
    cv2.putText(profile_area, "PROFIL LASER (proche=haut / loin=bas)",
                (10, PROFILE_H - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

    # ── Zone 3 : barre de statut ───────────────────────────────────────
    status = np.zeros((60, W, 3), dtype=np.uint8)
    status[:] = (30, 30, 30)
    bar_w = int(W * min(pmax / 255.0, 1.0))
    bar_color = (0, 220, 0) if pmax > 100 else (0, 165, 255) if pmax > 10 else (60, 60, 60)
    cv2.rectangle(status, (0, 0), (bar_w, 6), bar_color, -1)
    ts  = datetime.now().strftime("%H:%M:%S")
    sig = "LASER DETECTE" if pmax > 100 else "signal faible" if pmax > 10 else "en attente..."
    cv2.putText(status, f"{ts}  intensite={pmax}/255  [{sig}]",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 200), 1)
    info = f"SAUVEGARDE: {saved_path.name}" if saved_path else label
    color_info = (0, 200, 255) if saved_path else (120, 120, 120)
    cv2.putText(status, info, (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_info, 1)

    return np.vstack([colored, profile_area, status])


def _write_png(path: Path, img_bgr):
    """Écrit un PNG via imencode (gère les chemins avec accents)."""
    ok, buf = cv2.imencode(".png", img_bgr)
    if ok:
        path.write_bytes(buf.tobytes())
    return ok

def save_capture(img_raw):
    """Sauvegarde l'image brute en PNG colorisée + niveaux de gris."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = SAVE_DIR / f"facom_{ts}"

    pmax = img_raw.max()
    scaled = cv2.normalize(img_raw, None, 0, 255, cv2.NORM_MINMAX) if pmax > 10 \
             else np.clip(img_raw.astype(np.uint16) * 8, 0, 255).astype(np.uint8)

    big   = cv2.resize(scaled, (W, H * SCALE), interpolation=cv2.INTER_LINEAR)
    color = cv2.applyColorMap(big, cv2.COLORMAP_INFERNO)
    png   = Path(str(base) + ".png")
    _write_png(png, color)

    gray_big = cv2.resize(img_raw, (W, H * SCALE), interpolation=cv2.INTER_NEAREST)
    _write_png(Path(str(base) + "_gray.png"), gray_big)

    print(f"[CAPTURE] {png.name}  max={pmax}  → {png}")
    return png


def main():
    title = "FACOM DX.TSCANPB — Camera Laser  (ESPACE=capture  Q=quitter)"
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, WIN_W, WIN_H)

    last_mtime  = 0.0
    img_raw     = None
    saved_path  = None
    save_timer  = 0.0
    status_msg  = "Lance SCANDIAG, mets-toi en Fast Check, puis appuie sur le bouton de l'outil."
    frame_count = 0

    print("=" * 60)
    print("  FACOM — Flux caméra laser en direct")
    print("  ESPACE = capturer  |  Q = quitter")
    print("=" * 60)

    while True:
        # ── Vérifie si temp.raw a changé ──────────────────────────────
        try:
            mtime = RAW_FILE.stat().st_mtime
            if mtime != last_mtime:
                new_img = read_raw()
                if new_img is not None:
                    img_raw    = new_img
                    last_mtime = mtime
                    frame_count += 1
                    pmax = int(img_raw.max())
                    pmean = float(img_raw.mean())
                    sig = "LASER!" if pmax > 100 else "faible" if pmax > 10 else "bruit"
                    status_msg = f"Image #{frame_count} recue  max={pmax}  mean={pmean:.1f}  [{sig}]"
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status_msg}")
        except FileNotFoundError:
            status_msg = "SCANDIAG non lance — temp.raw introuvable"
        except Exception as e:
            status_msg = f"Erreur: {e}"

        # ── Expire la notification de sauvegarde après 3s ─────────────
        if saved_path and time.time() - save_timer > 3:
            saved_path = None

        # ── Affiche ───────────────────────────────────────────────────
        if img_raw is not None:
            frame = render(img_raw, status_msg, saved_path)
        else:
            # Écran d'attente
            frame = np.zeros((WIN_H, WIN_W, 3), dtype=np.uint8)
            frame[:] = (20, 20, 20)
            cv2.putText(frame, "FACOM DX.TSCANPB",
                        (WIN_W // 2 - 220, WIN_H // 2 - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 150, 200), 2)
            cv2.putText(frame, "En attente de SCANDIAG...",
                        (WIN_W // 2 - 220, WIN_H // 2 + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)
            cv2.putText(frame, "Lance SCANDIAG + Fast Check + bouton outil",
                        (WIN_W // 2 - 280, WIN_H // 2 + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

        cv2.imshow(title, frame)

        # ── Touches ───────────────────────────────────────────────────
        key = cv2.waitKey(150) & 0xFF

        if key in (ord('q'), 27):       # Q ou ESC = quitter
            break

        if key == ord(' '):             # ESPACE = capturer
            if img_raw is not None:
                saved_path = save_capture(img_raw)
                save_timer = time.time()
                status_msg = f"Photo sauvegardee : {saved_path.name}"
            else:
                status_msg = "Pas d'image a capturer."

        if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()
    print(f"\n[FIN] {frame_count} images recues. Captures dans : {SAVE_DIR}")


if __name__ == "__main__":
    main()
