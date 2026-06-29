"""
Appelle directement LaserDisk_COM.dll pour accéder à la caméra FACOM.
Ferme SCANDIAG avant de lancer ce script.
"""
import ctypes, ctypes.wintypes as wt
import time, sys, struct
from pathlib import Path

DLL_PATH = r"C:\ProgramData\Facom\ScanDiag\Bin\LaserDisk_COM.dll"
MAC      = "00:07:80:87:34:1E"

# ── Charge la DLL ─────────────────────────────────────────────────────────────
print(f"Chargement de {DLL_PATH}...")
try:
    dll = ctypes.CDLL(DLL_PATH)
    print("[OK] DLL chargée.")
except Exception as e:
    print(f"[ERREUR] {e}")
    sys.exit(1)

# ── Liste et inspecte les exports connus ─────────────────────────────────────
exports = [
    "_DownloadImage",
    "_SetModeDownloadImager",
    "_sendEBTCommand",
    "_SetCamera",
    "_SetLaser",
    "_setCameraExposure",
]

print("\nFonctions disponibles :")
for name in exports:
    try:
        fn = getattr(dll, name)
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  [--] {name} : {e}")

# ── Essaie d'appeler _SetCamera(1) et _DownloadImage ─────────────────────────
print("\n--- Test _SetCamera ---")
try:
    # Essai signature (int) → int
    dll._SetCamera.restype  = ctypes.c_int
    dll._SetCamera.argtypes = [ctypes.c_int]
    ret = dll._SetCamera(1)
    print(f"  _SetCamera(1) → {ret}")
except Exception as e:
    print(f"  _SetCamera(1) [1 arg int] → {e}")

try:
    # Essai sans argument
    dll._SetCamera.argtypes = []
    ret = dll._SetCamera()
    print(f"  _SetCamera() → {ret}")
except Exception as e:
    print(f"  _SetCamera() [0 arg] → {e}")

print("\n--- Test _SetLaser(0) — désactive le laser ---")
try:
    dll._SetLaser.restype  = ctypes.c_int
    dll._SetLaser.argtypes = [ctypes.c_int]
    ret = dll._SetLaser(0)
    print(f"  _SetLaser(0) → {ret}")
except Exception as e:
    print(f"  _SetLaser(0) → {e}")

print("\n--- Test _DownloadImage ---")
try:
    # Alloue un buffer 1280×800 = 1 Mo
    buf  = (ctypes.c_ubyte * (1280 * 800))()
    w    = ctypes.c_int(0)
    h    = ctypes.c_int(0)
    dll._DownloadImage.restype  = ctypes.c_int
    dll._DownloadImage.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
    ]
    ret = dll._DownloadImage(buf, ctypes.byref(w), ctypes.byref(h))
    print(f"  _DownloadImage → {ret}  w={w.value}  h={h.value}")
    if w.value > 0 and h.value > 0:
        import numpy as np, cv2
        img = np.frombuffer(buf, dtype=np.uint8)[:w.value * h.value].reshape(h.value, w.value)
        out = Path(__file__).parent / "captures" / "full_frame.png"
        ok, enc = cv2.imencode(".png", img)
        if ok:
            out.write_bytes(enc.tobytes())
            print(f"  [SAUVEGARDE] {out}")
except Exception as e:
    print(f"  _DownloadImage → {e}")

print("\n--- Test _sendEBTCommand ---")
try:
    # Essai avec un buffer de commande brut
    cmd = (ctypes.c_ubyte * 7)(0x00, 0x00, 0x07, 0x10, 0x00, 0x01, 0x01)
    dll._sendEBTCommand.restype  = ctypes.c_int
    dll._sendEBTCommand.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
    ret = dll._sendEBTCommand(cmd, 7)
    print(f"  _sendEBTCommand(init_0x01) → {ret}")
except Exception as e:
    print(f"  _sendEBTCommand → {e}")

print("\nDone.")
