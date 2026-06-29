"""Surveille tout le disque C: pour détecter les nouveaux fichiers créés par SCANDIAG."""
import time, os
from pathlib import Path
from datetime import datetime

WATCH_ROOTS = [
    Path(r"C:\ProgramData\Facom"),
    Path(r"C:\Users\enzot\Documents"),
    Path(r"C:\Users\enzot\Pictures"),
    Path(r"C:\Users\enzot\AppData\Local\Temp"),
]

def snapshot(roots):
    files = {}
    for root in roots:
        try:
            for p in root.rglob("*"):
                try:
                    if p.is_file():
                        files[str(p)] = p.stat().st_mtime
                except Exception:
                    pass
        except Exception:
            pass
    return files

print("Prise du snapshot initial...")
before = snapshot(WATCH_ROOTS)
print(f"{len(before)} fichiers indexés.")
print("\n>>> Clique maintenant sur le bouton FOTO dans SCANDIAG <<<")
print("    (attente 30 secondes)\n")

time.sleep(30)

after = snapshot(WATCH_ROOTS)

new_files = {p: m for p, m in after.items() if p not in before}
mod_files = {p: m for p, m in after.items() if p in before and m != before[p]}

print(f"\n=== NOUVEAUX FICHIERS ({len(new_files)}) ===")
for p in sorted(new_files):
    size = Path(p).stat().st_size
    print(f"  {size:10d} o  {p}")

print(f"\n=== MODIFIES ({len(mod_files)}) ===")
for p in sorted(mod_files):
    size = Path(p).stat().st_size
    print(f"  {size:10d} o  {p}")
