#!/usr/bin/env python3
"""
Needed Files Checker + Copier
──────────────────────────────
Partendo da "units_variants.txt" (lista di right-variant VMD) risolve
ricorsivamente tutte le dipendenze (VMD → models → textures), deduplica
i file su base globale (ogni file una sola volta) e:

  1. Scrive needed_files.txt con PRESENTI e ASSENTI
  2. Copia i file PRESENTI in:
       <CIB_DEST>/variantmeshes/<percorso relativo>
     mantenendo la struttura gerarchica
  3. Aggiunge i file copiati ad added_files.txt
  4. Riscrive needed_files.txt lasciando solo gli ASSENTI
     (e gli eventuali file che non è stato possibile copiare)

Usage:
  1. Scrivi in units_variants.txt un nome di variant per riga
     (stem o con .variantmeshdefinition; righe che iniziano con # sono ignorate)
  2. Opzionalmente, scrivi in added_files.txt i file già presenti nel pack
  3. Esegui: python needed-files.py
"""

import importlib.util, shutil
from pathlib import Path
from collections import defaultdict

# ── Importa CONFIG e build_data da vmd-generate.py ──────────────
_spec = importlib.util.spec_from_file_location(
    "vmd_generate", Path(__file__).parent / "vmd-generate.py"
)
_vmd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vmd)

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
UNITS_VARIANTS_FILE = r"C:\Users\loren\Desktop\MK1212-website\units_variants.txt"
ADDED_FILES_FILE    = r"C:\Users\loren\Desktop\MK1212-website\added_files.txt"
OUTPUT_FILE         = r"C:\Users\loren\Desktop\MK1212-website\needed_files.txt"

# Cartella di destinazione per la copia dei file presenti.
# I file verranno copiati in:  CIB_DEST / <percorso relativo al mod root>
CIB_DEST = r"C:\Users\loren\Desktop\MK1212-website\cib\da aggiungere\variantmeshes"
# ═══════════════════════════════════════════════════════════════


def read_lines(filepath):
    """Legge un file testo, salta righe vuote e commenti (#)."""
    p = Path(filepath)
    if not p.exists():
        return []
    return [
        line.strip()
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def resolve_deps(variant, center_by_id, right_by_id, model_to_textures, known_tex):
    """
    Risolve ricorsivamente le dipendenze di un right-variant VMD.
    Ritorna (present, absent) come set di path relative al mod root.
    """
    present = set()
    absent  = set()

    def add_node_files(node):
        for mp in node.get("models", []):
            present.add(mp)
            for tex in model_to_textures.get(mp, []):
                (present if tex in known_tex else absent).add(tex)
        for ref in node.get("missing_models", []):
            absent.add(ref)

    add_node_files(variant)
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
            add_node_files(node)
            for sub_id in node.get("sub_vmds", []):
                if sub_id.lower() not in visited:
                    queue.append(sub_id)
        else:
            node = right_by_id.get(vid)
            if node and node["id"].lower() != variant["id"].lower():
                add_node_files(node)
                for ref in node.get("missing_vmds", []):
                    absent.add(ref)
                for sub_id in node.get("vmds", []):
                    if sub_id.lower() not in visited:
                        queue.append(sub_id)
            else:
                absent.add(vid + ".variantmeshdefinition")

    return present, absent


def source_and_dest(rel_path_str, source_root, dest_root):
    """
    Dato un path relativo come salvato da scan_* (che usa il nome della
    root come prefisso per i file direttamente nella root), restituisce:
      src  – Path assoluto del file sorgente
      dst  – Path assoluto di destinazione sotto dest_root
    """
    root = Path(source_root)
    p = rel_path_str.replace("\\", "/")
    # Rimuovi eventuale prefisso "variantmeshes/" aggiunto per i file in root
    root_prefix = root.name.lower() + "/"
    stripped = p[len(root_prefix):] if p.lower().startswith(root_prefix) else p
    src = root / stripped
    dst = Path(dest_root) / stripped
    return src, dst


def sort_by_type(paths):
    vmds     = sorted(p for p in paths if p.lower().endswith(".variantmeshdefinition"))
    models   = sorted(p for p in paths if p.lower().endswith(".rigid_model_v2"))
    textures = sorted(p for p in paths if p.lower().endswith(".dds"))
    other    = sorted(p for p in paths
                      if not any(p.lower().endswith(e)
                                 for e in (".variantmeshdefinition", ".rigid_model_v2", ".dds")))
    return vmds + models + textures + other


def write_needed(output_path, present_map, absent_map, header_suffix=""):
    """Scrive needed_files.txt. present/absent_map: {path → [variant, ...]}"""
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


def main():
    print("\n── Scansione ──────────────────────────────")
    (models_tree, center_vmds, right_vmds,
     textures_tree, tex_to_models, model_to_textures) = _vmd.build_data()

    center_by_id  = {v["id"].lower(): v for v in center_vmds}
    right_by_id   = {v["id"].lower(): v for v in right_vmds}
    right_by_file = {v["file"].lower(): v for v in right_vmds}

    known_tex = {
        f"{folder}/{f}"
        for folder, files in textures_tree.items()
        for f in files
    }

    try:
        variants_prefix = str(
            Path(_vmd.CONFIG["variants_root"]).relative_to(
                Path(_vmd.CONFIG["models_roots"][0])
            )
        ).replace("\\", "/")
    except (ValueError, IndexError):
        variants_prefix = "variantmeshdefinitions"

    source_root = _vmd.CONFIG["models_roots"][0]

    # ── Input ────────────────────────────────────────────────────
    units     = read_lines(UNITS_VARIANTS_FILE)
    added_raw = read_lines(ADDED_FILES_FILE)
    added_names = {Path(a).name.lower() for a in added_raw}

    def is_added(path_str):
        return Path(path_str).name.lower() in added_names

    print(f"  →  Varianti da analizzare : {len(units)}")
    print(f"  →  File già aggiunti      : {len(added_raw)}\n")

    # ── Risolvi dipendenze con deduplicazione globale ────────────
    # path → set di variant names che lo richiedono
    all_present: dict[str, set] = defaultdict(set)
    all_absent:  dict[str, set] = defaultdict(set)

    for unit in units:
        stem = Path(unit).stem.lower()
        file = stem + ".variantmeshdefinition"

        variant = right_by_id.get(stem) or right_by_file.get(file)
        if variant is None:
            all_absent[f"variant non trovata: {unit}"].add(unit)
            continue

        present, absent = resolve_deps(
            variant, center_by_id, right_by_id, model_to_textures, known_tex
        )
        present.add(f"{variants_prefix}/{variant['file']}")

        for p in present:
            if not is_added(p):
                all_present[p].add(unit)
        for a in absent:
            if not is_added(a):
                all_absent[a].add(unit)

    # ── Scrivi needed_files.txt iniziale ────────────────────────
    write_needed(OUTPUT_FILE, all_present, all_absent)
    print(f"✓  needed_files.txt scritto  ({len(all_present)} presenti, {len(all_absent)} assenti)")

    # ── Copia i file PRESENTI in CIB_DEST ───────────────────────
    if not all_present:
        print("   Nessun file da copiare.\n")
        return

    print(f"\n── Copia file → {CIB_DEST}")
    copied  = []   # path copiati con successo
    failed  = []   # path con errore di copia

    for rel_path in sort_by_type(all_present):
        src, dst = source_and_dest(rel_path, source_root, CIB_DEST)
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
        existing_added = read_lines(ADDED_FILES_FILE)
        new_added = existing_added + copied
        Path(ADDED_FILES_FILE).write_text("\n".join(new_added) + "\n", encoding="utf-8")
        print(f"  ✓  added_files.txt aggiornato (+{len(copied)} file)")

    # ── Riscrive needed_files.txt: rimuovi i copiati ────────────
    copied_set = set(copied)
    present_remaining = {p: v for p, v in all_present.items() if p not in copied_set}
    write_needed(
        OUTPUT_FILE,
        present_remaining,
        all_absent,
        header_suffix=" — aggiornato dopo copia",
    )
    print(f"  ✓  needed_files.txt aggiornato")
    if present_remaining:
        print(f"     Presenti ancora da copiare : {len(present_remaining)}")
    print(f"     Assenti (non trovati)       : {len(all_absent)}\n")


if __name__ == "__main__":
    main()
