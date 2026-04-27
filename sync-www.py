#!/usr/bin/env python3
"""
Sincronizza i file HTML generati in www/ per l'APK Android.

Uso:
  1. Esegui needed-files.py  (genera missing-files.html e unit-report.html)
  2. Esegui questo script:   python sync-www.py
  3. Aggiorna l'APK:         npx cap sync android
  4. Apri Android Studio:    npx cap open android  (poi Build > Generate APK)
"""

import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
WWW  = ROOT / "www"
WWW.mkdir(exist_ok=True)

FILES = [
    (ROOT / "missing-files.html", WWW / "missing-files.html"),
    (ROOT / "unit-report.html",   WWW / "unit-report.html"),
]

print("\n── Sync www/ ──────────────────────────────")
ok = True
for src, dst in FILES:
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  ✓  {src.name}")
    else:
        print(f"  ⚠  Non trovato: {src.name}  (esegui prima needed-files.py)")
        ok = False

if not ok:
    print("\n  ⚠  Alcuni file mancano — controlla sopra.\n")
    sys.exit(1)

print("\n── Capacitor sync ─────────────────────────")
try:
    subprocess.run(["npx", "cap", "sync", "android"], check=True)
    print("\n✓  Fatto. Apri Android Studio con:  npx cap open android\n")
except FileNotFoundError:
    print("  ⚠  npx non trovato — installa Node.js, poi: npm install")
except subprocess.CalledProcessError:
    print("  ⚠  cap sync fallito — hai eseguito: npm install ?")
