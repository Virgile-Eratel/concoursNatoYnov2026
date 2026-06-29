"""
photo_facom.py — Prend une photo avec la caméra FACOM DX.TSCANPB
Lance SCANDIAG en arrière-plan, clique sur Fast Check, capture temp.raw.
"""

import ctypes
import ctypes.wintypes as wt
import time
import subprocess
import psutil
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime

SCANDIAG_EXE = r"C:\ProgramData\Facom\ScanDiag\Bin\LaserExaminerIDC5.exe"
RAW_FILE     = Path(r"C:\ProgramData\Facom\ScanDiag\temp.raw")
SAVE_DIR     = Path(__file__).parent / "captures"
HEADER, W, H = 12, 1280, 128

SAVE_DIR.mkdir(exist_ok=True)

user32          = ctypes.windll.user32
EnumChildProc   = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


# ── Helpers Win32 ──────────────────────────────────────────────────────────────

def _text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if not n:
        return ""
    b = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, b, n + 1)
    return b.value

def _cls(hwnd):
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, b, 256)
    return b.value

def _rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top

def _pid(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def _children(parent):
    result = []
    @EnumChildProc
    def cb(h, _):
        result.append(h)
        return True
    user32.EnumChildWindows(parent, cb, 0)
    return result

def _find_child(parent, text=None, cls_part=None, w_exact=None, h_exact=None):
    for h in _children(parent):
        if text     is not None and _text(h) != text:            continue
        if cls_part is not None and cls_part not in _cls(h):     continue
        if w_exact  is not None and _rect(h)[2] != w_exact:      continue
        if h_exact  is not None and _rect(h)[3] != h_exact:      continue
        return h
    return None

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.08)
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # MOUSEEVENTF_LEFTUP
    time.sleep(0.15)


# ── SCANDIAG ────────────────────────────────────────────────────────────────────

def scandiag_running():
    return any('laser' in p.info['name'].lower()
               for p in psutil.process_iter(['name']))

def start_scandiag():
    print("[INFO] Démarrage de SCANDIAG...")
    subprocess.Popen([SCANDIAG_EXE])
    for _ in range(20):
        time.sleep(1)
        if scandiag_running():
            print("[OK] SCANDIAG lancé.")
            time.sleep(3)   # laisse l'UI s'initialiser
            return True
    print("[ERREUR] SCANDIAG n'a pas démarré.")
    return False

def get_root():
    result = [None]
    @EnumWindowsProc
    def cb(h, _):
        if _text(h) == "Disc Tire Profiler":
            result[0] = h
            return False
        return True
    user32.EnumWindows(cb, 0)
    return result[0]


# ── Navigation SCANDIAG ────────────────────────────────────────────────────────

def is_on_main_menu(root):
    """Vrai si on est sur le menu principal (menu avec Disque de frein / Fast Check / Pneu)."""
    fw = _find_child(root, text='fourWheels1')
    if fw is None:
        return True    # pas de roues → menu principal
    x, _, _, _ = _rect(fw)
    return x < 0      # hors écran = caché

def navigate_fast_check(root):
    """Clique sur 'Fast Check' dans le menu principal si nécessaire."""
    if not is_on_main_menu(root):
        print("[OK] Déjà sur la page Fast Check.")
        return True

    # Cherche le label 'Fast Check' 192×96 (le 192, pas le 510)
    fc_label = None
    for h in _children(root):
        if _text(h) == 'Fast Check' and _cls(h).endswith('STATIC') and _rect(h)[2] == 192:
            fc_label = h
            break

    if fc_label is None:
        print("[ERREUR] Label 'Fast Check' introuvable dans le menu.")
        return False

    lx, ly, lw, lh = _rect(fc_label)
    # Le bouton cliquable est la fenêtre 192×192 positionnée juste AU-DESSUS du label
    cx = lx + lw // 2
    cy = ly - 96          # centre de la zone 192×192 au-dessus du label
    print(f"[CLICK] Fast Check menu → ({cx}, {cy})")
    user32.SetForegroundWindow(root)
    time.sleep(0.3)
    click(cx, cy)
    time.sleep(1.5)
    return True

WM_MOUSEMOVE     = 0x0200
WM_LBUTTONDOWN   = 0x0201
WM_LBUTTONUP     = 0x0202
MK_LBUTTON       = 0x0001

def _make_lparam(x, y):
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)

def _post_click(hwnd, local_x, local_y):
    """Envoie WM_LBUTTONDOWN/UP directement au contrôle (sans bouger la souris)."""
    lp = _make_lparam(int(local_x), int(local_y))
    user32.SendMessageW(hwnd, WM_MOUSEMOVE,   0,          lp)
    user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.08)
    user32.SendMessageW(hwnd, WM_LBUTTONUP,   0,          lp)

def _foreground(hwnd):
    """Force le focus sur la fenêtre via AttachThreadInput."""
    kernel32 = ctypes.windll.kernel32
    cur_tid  = kernel32.GetCurrentThreadId()
    tgt_tid  = user32.GetWindowThreadProcessId(hwnd, None)
    user32.AttachThreadInput(cur_tid, tgt_tid, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(cur_tid, tgt_tid, False)
    time.sleep(0.3)

def trigger_wheel_scan(root, wheel='fl'):
    """
    Clique sur une roue dans fourWheels1 pour déclencher le scan disque.
    wheel : 'fl'=avant-gauche  'fr'=avant-droite  'rl'=arrière-gauche  'rr'=arrière-droite
    Essaie d'abord SendMessage direct, puis clic souris réel.
    """
    fw = _find_child(root, text='fourWheels1')
    if fw is None:
        print("[ERREUR] Diagramme fourWheels1 introuvable.")
        return False

    fx, fy, fw_w, fw_h = _rect(fw)
    print(f"[INFO] fourWheels1 à ({fx},{fy}) {fw_w}×{fw_h}")

    # Positions relatives (proportion x, proportion y) des 4 roues dans le diagramme
    wheel_positions = {
        'fl': [(0.20, 0.15), (0.25, 0.20), (0.15, 0.25)],
        'fr': [(0.80, 0.15), (0.75, 0.20), (0.85, 0.25)],
        'rl': [(0.20, 0.82), (0.25, 0.78), (0.15, 0.75)],
        'rr': [(0.80, 0.82), (0.75, 0.78), (0.85, 0.75)],
    }
    positions = wheel_positions.get(wheel, wheel_positions['fl'])

    for px, py in positions:
        lx = int(fw_w * px)
        ly = int(fw_h * py)
        sx = fx + lx
        sy = fy + ly

        # Méthode 1 : SendMessage direct au contrôle
        print(f"  [SEND] SendMessage WM_LBUTTONDOWN → local({lx},{ly})")
        _post_click(fw, lx, ly)
        time.sleep(0.3)

        # Méthode 2 : vrai clic souris au premier plan
        print(f"  [CLICK] Clic souris → écran({sx},{sy})")
        _foreground(root)
        click(sx, sy)
        time.sleep(0.5)

    return True


# ── Capture image ──────────────────────────────────────────────────────────────

def wait_and_capture(timeout=20):
    """Attend que temp.raw soit mis à jour et retourne l'image numpy."""
    if not RAW_FILE.exists():
        print("[ERREUR] temp.raw introuvable — SCANDIAG a-t-il écrit au moins une fois ?")
        return None

    old_mtime = RAW_FILE.stat().st_mtime
    print(f"[ATTENTE] Mesure laser en cours... (max {timeout}s)")

    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            mtime = RAW_FILE.stat().st_mtime
            if mtime != old_mtime:
                data    = RAW_FILE.read_bytes()
                payload = data[HEADER:]
                img     = np.frombuffer(payload[:W * H], dtype=np.uint8).reshape(H, W)
                pmax, pmean = int(img.max()), float(img.mean())
                signal = "LASER DETECTE" if pmax > 100 else ("signal faible" if pmax > 10 else "bruit de fond")
                print(f"[OK] Image capturée : max={pmax}  mean={pmean:.1f}  [{signal}]")
                return img
        except Exception:
            pass
        time.sleep(0.15)

    print(f"[TIMEOUT] temp.raw n'a pas changé en {timeout}s.")
    return None


# ── Affichage & sauvegarde ────────────────────────────────────────────────────

def process_image(img):
    """Mise à l'échelle + colormap INFERNO → image BGR affichable."""
    pmax = img.max()
    if pmax > 10:
        scaled = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    else:
        scaled = np.clip(img.astype(np.uint16) * 8, 0, 255).astype(np.uint8)
    big    = cv2.resize(scaled, (W * 2, H * 4), interpolation=cv2.INTER_LINEAR)
    return cv2.applyColorMap(big, cv2.COLORMAP_INFERNO)

def save_image(img_color, img_raw):
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SAVE_DIR / f"facom_{ts}.png"
    cv2.imwrite(str(path), img_color)
    print(f"[SAVE] {path}")
    return path

def show_image(img_color, path):
    win = f"FACOM — {path.name}  (Q pour quitter)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.imshow(win, img_color)
    print("Appuie sur Q / Echap pour fermer la fenêtre.")
    while True:
        k = cv2.waitKey(100) & 0xFF
        if k in (ord('q'), 27):
            break
        if cv2.getWindowProperty(win, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyAllWindows()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  FACOM DX.TSCANPB — Capture Photo")
    print("=" * 60)

    # 1. Démarrer SCANDIAG si nécessaire
    if not scandiag_running():
        if not start_scandiag():
            return
    else:
        print("[OK] SCANDIAG est déjà lancé.")

    # 2. Trouver la fenêtre principale
    root = get_root()
    if not root:
        print("[ERREUR] Fenêtre 'Disc Tire Profiler' introuvable.")
        return
    print(f"[OK] Fenêtre SCANDIAG trouvée (hwnd=0x{root:08X})")

    # 3. Naviguer vers Fast Check
    if not navigate_fast_check(root):
        return
    time.sleep(0.5)

    # 4. Déclencher le scan sur la roue avant-gauche
    if not trigger_wheel_scan(root, wheel='fl'):
        return

    # 5. Attendre et capturer l'image
    img = wait_and_capture(timeout=20)
    if img is None:
        print("[AIDE] Essaie d'appuyer sur le bouton physique de l'outil.")
        return

    # 6. Traiter, sauvegarder, afficher
    img_color = process_image(img)
    path      = save_image(img_color, img)
    show_image(img_color, path)
    print(f"\n[DONE] Photo sauvegardée dans : {path}")


if __name__ == "__main__":
    main()
