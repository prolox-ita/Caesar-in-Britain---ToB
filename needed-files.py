#!/usr/bin/env python3
"""
Needed Files Checker + Copier
──────────────────────────────
Legge i dati già calcolati da vmd-generate.py (embedded nel file HTML),
risolve le dipendenze per le variant in units_variants.txt e:

  1. Scrive needed_files.txt con PRESENTI e ASSENTI (ogni file una sola volta)
  2. Copia i file PRESENTI in CIB_DEST/variantmeshes/<percorso relativo>
     mantenendo la struttura gerarchica
  3. Aggiunge i file copiati ad added_files.txt
  4. Riscrive needed_files.txt lasciando solo ASSENTI e copia fallite

Usage:
  1. Genera prima il file HTML con vmd-generate.py
  2. Scrivi in units_variants.txt i nomi delle variant (uno per riga)
  3. Opzionalmente, scrivi in added_files.txt i file già presenti nel pack
  4. Esegui: python needed-files.py
"""

import json, re, shutil
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
# File HTML generato da vmd-generate.py
HTML_FILE = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.html"

# Cartella radice del mod (= CONFIG["models_roots"][0] in vmd-generate.py)
# I path relativi nei dati sono tutti calcolati a partire da questa cartella
MOD_ROOT = r"D:\Thrones of Britannia\modding\variantmeshes"

# Prefisso relativo della cartella delle variant destre rispetto a MOD_ROOT
# (= CONFIG["variants_root"] relativo a MOD_ROOT)
VARIANTS_PREFIX = "variantmeshdefinitions"

UNITS_VARIANTS_FILE = r"C:\Users\loren\Desktop\MK1212-website\units_variants.txt"
ADDED_FILES_FILE    = r"C:\Users\loren\Desktop\MK1212-website\added_files.txt"
OUTPUT_FILE         = r"C:\Users\loren\Desktop\MK1212-website\needed_files.txt"

# Cartella di destinazione per la copia
CIB_DEST = r"C:\Users\loren\Desktop\MK1212-website\cib\da aggiungere\variantmeshes"
# ═══════════════════════════════════════════════════════════════


# ── Lettura HTML ─────────────────────────────────────────────────

def extract_js_const(html: str, name: str):
    """Estrae il valore JSON di una costante JS dal file HTML."""
    m = re.search(rf'const {re.escape(name)}\s*=\s*', html)
    if not m:
        raise ValueError(f"Costante '{name}' non trovata nel file HTML")
    value, _ = json.JSONDecoder().raw_decode(html, m.end())
    return value


def load_html_data(html_path: str):
    """Legge il file HTML e restituisce i 4 dataset necessari."""
    html = Path(html_path).read_text(encoding="utf-8", errors="replace")
    textures_tree    = extract_js_const(html, "TEXTURES_TREE")
    model_to_textures = extract_js_const(html, "MODEL_TO_TEXTURES")
    center_vmds      = extract_js_const(html, "CENTER_VMDS")
    right_vmds       = extract_js_const(html, "RIGHT_VMDS")
    return textures_tree, model_to_textures, center_vmds, right_vmds


# ── Utilità ──────────────────────────────────────────────────────

def read_lines(filepath):
    p = Path(filepath)
    if not p.exists():
        return []
    return [
        line.strip()
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def sort_by_type(paths):
    exts = (".variantmeshdefinition", ".rigid_model_v2", ".dds")
    buckets = [sorted(p for p in paths if p.lower().endswith(e)) for e in exts]
    other   =  sorted(p for p in paths if not any(p.lower().endswith(e) for e in exts))
    return buckets[0] + buckets[1] + buckets[2] + other


def source_and_dest(rel_path_str: str):
    """
    Restituisce (src assoluto, dst assoluto) per un path relativo.
    I file direttamente nella root hanno il nome della cartella come prefisso
    (es. "variantmeshes/file.ext"); lo strip per calcolare il path corretto.
    """
    root = Path(MOD_ROOT)
    p = rel_path_str.replace("\\", "/")
    root_prefix = root.name.lower() + "/"
    stripped = p[len(root_prefix):] if p.lower().startswith(root_prefix) else p
    return root / stripped, Path(CIB_DEST) / stripped


# ── Risoluzione dipendenze ────────────────────────────────────────

def resolve_deps(variant, center_by_id, right_by_id, model_to_textures, known_tex):
    present = set()
    absent  = set()

    def add_node(node):
        for mp in node.get("models", []):
            present.add(mp)
            for tex in model_to_textures.get(mp, []):
                (present if tex in known_tex else absent).add(tex)
        for ref in node.get("missing_models", []):
            absent.add(ref)

    add_node(variant)
    for ref in variant.get("missing_vmds", []):
        absent.add(ref)

    visited = set()
    queue   = list(variant.get("vmds", []))

    while queue:
        vid = queue.pop(0).lower()
        if vid in visited:
            continue
        visited.add(vid)

        node = center_by_id.get(vid)
        if node:
            present.add(f"{node['folder']}/{node['file']}")
            add_node(node)
            for sub_id in node.get("sub_vmds", []):
                if sub_id.lower() not in visited:
                    queue.append(sub_id)
        else:
            node = right_by_id.get(vid)
            if node and node["id"].lower() != variant["id"].lower():
                add_node(node)
                for ref in node.get("missing_vmds", []):
                    absent.add(ref)
                for sub_id in node.get("vmds", []):
                    if sub_id.lower() not in visited:
                        queue.append(sub_id)
            else:
                absent.add(vid + ".variantmeshdefinition")

    return present, absent


# ── Output ────────────────────────────────────────────────────────

def write_needed(output_path, present_map, absent_map, header_suffix=""):
    SEP = "═" * 62
    lines = [f"Needed Files Report{header_suffix}", SEP, ""]

    if present_map:
        lines.append(f"PRESENTI - da aggiungere al pack  ({len(present_map)} file)")
        lines.append("─" * 62)
        for p in sort_by_type(present_map):
            variants_str = ", ".join(sorted(present_map[p]))
            lines.append(f"  {p}   [{variants_str}]")
        lines.append("")

    if absent_map:
        lines.append(f"ASSENTI - file non trovati nei folder mod  ({len(absent_map)} file)")
        lines.append("─" * 62)
        for a in sort_by_type(absent_map):
            variants_str = ", ".join(sorted(absent_map[a]))
            lines.append(f"  {a}   [{variants_str}]")
        lines.append("")

    lines += [SEP,
              f"Presenti da aggiungere : {len(present_map)}",
              f"Assenti (non trovati)  : {len(absent_map)}"]
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("\n── Lettura dati da HTML ───────────────────")
    textures_tree, model_to_textures, center_vmds, right_vmds = load_html_data(HTML_FILE)
    print(f"  ✓  Textures  : {sum(len(v) for v in textures_tree.values())}")
    print(f"  ✓  Center VMD: {len(center_vmds)}")
    print(f"  ✓  Varianti  : {len(right_vmds)}")

    center_by_id  = {v["id"].lower(): v for v in center_vmds}
    right_by_id   = {v["id"].lower(): v for v in right_vmds}
    right_by_file = {v["file"].lower(): v for v in right_vmds}

    known_tex = {
        f"{folder}/{f}"
        for folder, files in textures_tree.items()
        for f in files
    }

    units     = read_lines(UNITS_VARIANTS_FILE)
    added_raw = read_lines(ADDED_FILES_FILE)
    added_names = {Path(a).name.lower() for a in added_raw}

    def is_added(p):
        return Path(p).name.lower() in added_names

    print(f"\n  →  Varianti da analizzare : {len(units)}")
    print(f"  →  File già aggiunti      : {len(added_raw)}\n")

    # ── Risolvi con deduplicazione globale ───────────────────────
    all_present: dict[str, set] = defaultdict(set)
    all_absent:  dict[str, set] = defaultdict(set)

    for unit in units:
        stem = Path(unit).stem.lower()
        variant = right_by_id.get(stem) or right_by_file.get(stem + ".variantmeshdefinition")
        if variant is None:
            all_absent[f"variant non trovata: {unit}"].add(unit)
            continue

        present, absent = resolve_deps(
            variant, center_by_id, right_by_id, model_to_textures, known_tex
        )
        present.add(f"{VARIANTS_PREFIX}/{variant['file']}")

        for p in present:
            if not is_added(p):
                all_present[p].add(unit)
        for a in absent:
            if not is_added(a):
                all_absent[a].add(unit)

    # ── Scrivi needed_files.txt iniziale ────────────────────────
    write_needed(OUTPUT_FILE, all_present, all_absent)
    print(f"✓  needed_files.txt scritto  ({len(all_present)} presenti, {len(all_absent)} assenti)")

    if not all_present:
        print("   Nessun file da copiare.\n")
        return

    # ── Copia i PRESENTI in CIB_DEST ────────────────────────────
    print(f"\n── Copia file → {CIB_DEST}")
    copied = []
    failed = []

    for rel_path in sort_by_type(all_present):
        src, dst = source_and_dest(rel_path)
        if not src.exists():
            print(f"  ⚠  Non trovato su disco: {src}")
            failed.append(rel_path)
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel_path)
        except Exception as e:
            print(f"  ⚠  Errore copia {rel_path}: {e}")
            failed.append(rel_path)

    print(f"  ✓  Copiati  : {len(copied)}")
    if failed:
        print(f"  ⚠  Falliti  : {len(failed)}")

    # ── Aggiorna added_files.txt ─────────────────────────────────
    if copied:
        Path(ADDED_FILES_FILE).write_text(
            "\n".join(read_lines(ADDED_FILES_FILE) + copied) + "\n",
            encoding="utf-8",
        )
        print(f"  ✓  added_files.txt +{len(copied)} file")

    # ── Riscrive needed_files.txt: rimuovi i copiati ────────────
    copied_set = set(copied)
    present_remaining = {p: v for p, v in all_present.items() if p not in copied_set}
    write_needed(OUTPUT_FILE, present_remaining, all_absent,
                 header_suffix=" — aggiornato dopo copia")
    print(f"  ✓  needed_files.txt aggiornato  "
          f"({len(present_remaining)} presenti rimasti, {len(all_absent)} assenti)\n")


if __name__ == "__main__":
    main()
