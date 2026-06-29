"""Inspecte la fenêtre SCANDIAG — affiche positions écran."""
import ctypes
import ctypes.wintypes as wt
import psutil

user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
EnumChildProc   = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

def get_text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if n == 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def get_pid(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value

def get_rect(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top  # x, y, w, h

# PID SCANDIAG
scandiag_pids = set()
for proc in psutil.process_iter(['pid', 'name']):
    if 'laser' in proc.info['name'].lower():
        scandiag_pids.add(proc.info['pid'])
        print(f"Processus: {proc.info['name']}  PID={proc.info['pid']}")

if not scandiag_pids:
    print("SCANDIAG n'est pas lancé.")
    raise SystemExit

# Top-level windows
top_windows = []

@EnumWindowsProc
def _top_cb(hwnd, _):
    if get_pid(hwnd) in scandiag_pids:
        top_windows.append(hwnd)
    return True

user32.EnumWindows(_top_cb, 0)

for root in top_windows:
    title = get_text(root)
    if 'Disc Tire' not in title:
        continue
    x, y, w, h = get_rect(root)
    print(f"\n=== '{title}'  pos=({x},{y})  taille={w}×{h} ===\n")
    print(f"  {'hwnd':12s}  {'classe':35s}  {'texte':40s}  {'x':6s}  {'y':6s}  {'w':6s}  {'h':6s}")
    print("  " + "-" * 120)

    children = []

    @EnumChildProc
    def _child_cb(hwnd, _):
        children.append(hwnd)
        return True

    user32.EnumChildWindows(root, _child_cb, 0)

    for hwnd in children:
        t  = get_text(hwnd)
        c  = get_class(hwnd)
        cx, cy, cw, ch = get_rect(hwnd)
        label = f"'{t}'" if t else ""
        print(f"  0x{hwnd:08X}  {c:35s}  {label:40s}  {cx:6d}  {cy:6d}  {cw:6d}  {ch:6d}")
