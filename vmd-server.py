#!/usr/bin/env python3
"""
VMD Viewer Server
─────────────────
1. Modifica la sezione CONFIGURAZIONE con i tuoi percorsi
2. Avvia: python3 vmd-server.py
3. Apri:  http://localhost:8080/vmd-viewer.html

Premi il pulsante ↺ nel viewer per ricaricare i file dal disco.
"""

import os, json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE — modifica questi percorsi
# ═══════════════════════════════════════════════════════════════
CONFIG = {

    # Una o più cartelle radice che contengono i .variantmesh (modelli).
    # Vengono scansionate ricorsivamente.
    "models_roots": [
        r"C:\path\alla\tua\cartella\modelli",
    ],

    # Cartella dei VMD centrali (unità, .variantmeshdefinition).
    # Scansionata ricorsivamente.
    "vmds_root": r"C:\path\alla\tua\cartella\unit_vmds",

    # Cartella delle varianti destra (una sola cartella specifica).
    # Solo il primo livello.
    "variants_root": r"C:\path\alla\tua\cartella\variants",

    "port": 8080,
}
# ═══════════════════════════════════════════════════════════════


def scan_models(roots):
    """Scansiona le cartelle radice → { "percorso/relativo": ["file.variantmesh", ...] }"""
    tree = {}
    for root_str in roots:
        root_path = Path(root_str)
        if not root_path.exists():
            print(f"  ⚠  Non trovata: {root_str}")
            continue
        for f in sorted(root_path.rglob("*.variantmesh")):
            rel = f.parent.relative_to(root_path)
            key = str(rel).replace("\\", "/") if str(rel) != "." else root_path.name
            tree.setdefault(key, []).append(f.name)
    return tree


def parse_vmd(filepath):
    """
    Analizza un file .variantmeshdefinition XML e restituisce
    (list_of_variantmesh_refs, list_of_vmd_refs).
    Cerca in tutti gli attributi del documento.
    """
    refs_mesh, refs_vmd = [], []
    try:
        tree = ET.parse(filepath)
        for elem in tree.getroot().iter():
            for val in elem.attrib.values():
                lo = val.lower()
                if lo.endswith(".variantmesh"):
                    refs_mesh.append(val.replace("\\", "/"))
                elif lo.endswith(".variantmeshdefinition"):
                    refs_vmd.append(val.replace("\\", "/"))
    except ET.ParseError as e:
        print(f"  ⚠  XML malformato {filepath.name}: {e}")
    except Exception as e:
        print(f"  ⚠  {filepath.name}: {e}")
    return refs_mesh, refs_vmd


def scan_center_vmds(root_str):
    root_path = Path(root_str)
    if not root_path.exists():
        print(f"  ⚠  Non trovata (VMD): {root_str}")
        return []
    result = []
    for f in sorted(root_path.rglob("*.variantmeshdefinition")):
        rel = f.parent.relative_to(root_path)
        folder = str(rel).replace("\\", "/") if str(rel) != "." else root_path.name
        models, _ = parse_vmd(f)
        result.append({
            "id": f.stem,
            "folder": folder,
            "file": f.name,
            "models": models,
            "in_variants": [],
        })
    return result


def scan_right_vmds(root_str):
    root_path = Path(root_str)
    if not root_path.exists():
        print(f"  ⚠  Non trovata (Variants): {root_str}")
        return []
    result = []
    for f in sorted(root_path.glob("*.variantmeshdefinition")):
        _, vmd_refs = parse_vmd(f)
        result.append({
            "id": f.stem,
            "file": f.name,
            "_raw_refs": vmd_refs,
            "vmds": [],
        })
    return result


def build_data():
    print("\n── Scansione ──────────────────────────────")
    models_tree  = scan_models(CONFIG["models_roots"])
    center_vmds  = scan_center_vmds(CONFIG["vmds_root"])
    right_vmds   = scan_right_vmds(CONFIG["variants_root"])

    # Indici per risolvere le cross-reference
    by_stem = {v["id"]: v for v in center_vmds}   # stem (senza ext) → vmd
    by_file = {v["file"]: v for v in center_vmds}  # filename → vmd

    # Per ogni variante destra, risolvi i riferimenti ai VMD centrali
    for variant in right_vmds:
        for ref in variant["_raw_refs"]:
            fname = Path(ref).name
            matched = by_file.get(fname) or by_stem.get(Path(ref).stem)
            if matched:
                variant["vmds"].append(matched["id"])
                if variant["id"] not in matched["in_variants"]:
                    matched["in_variants"].append(variant["id"])
        del variant["_raw_refs"]

    print(f"  ✓  Cartelle modelli : {len(models_tree)}")
    print(f"  ✓  VMD centrali     : {len(center_vmds)}")
    print(f"  ✓  Varianti         : {len(right_vmds)}")
    print("───────────────────────────────────────────\n")

    return {
        "models_tree": models_tree,
        "center_vmds": center_vmds,
        "right_vmds":  right_vmds,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/api/data":
            data = build_data()
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Mostra solo le chiamate API, non i file statici
        if "/api/" in args[0]:
            print(f"  →  {args[0]}")


if __name__ == "__main__":
    port = CONFIG["port"]
    server = HTTPServer(("", port), Handler)
    print(f"\n VMD Viewer Server")
    print(f" http://localhost:{port}/vmd-viewer.html")
    print(f" Ctrl+C per fermare\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer fermato.")
