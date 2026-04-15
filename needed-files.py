#!/usr/bin/env python3
"""
Needed Files Checker
────────────────────
Partendo da "units_variants.txt" (lista di right-variant VMD, quarta colonna),
risolve ricorsivamente tutte le dipendenze (VMD → models → textures)
e produce "needed_files.txt" con solo i file ancora da aggiungere.

Per ogni variant:
  [PRESENTI - da aggiungere]  = file trovati nel mod ma non ancora nel pack
  [ASSENTI  - non trovati]    = file referenziati ma non presenti nei folder scansionati

I file già elencati in "added_files.txt" vengono rimossi dall'output.

Usage:
  1. Scrivi in units_variants.txt un nome di variant per riga
     (stem oppure nome completo con .variantmeshdefinition)
  2. Scrivi in added_files.txt i file già aggiunti (uno per riga)
  3. Esegui: python needed-files.py
"""

import importlib.util
from pathlib import Path

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
# ═══════════════════════════════════════════════════════════════


def read_lines(filepath):
    """Legge un file testo, salta righe vuote e commenti (#)."""
    p = Path(filepath)
    if not p.exists():
        print(f"  ⚠  File non trovato: {filepath}")
        return []
    return [
        line.strip()
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def resolve_deps(variant, center_by_id, right_by_id, model_to_textures, known_tex):
    """
    Risolve ricorsivamente tutte le dipendenze di un right-variant VMD.

    Ritorna:
      present  – set di path trovate nel mod (relative a models_root/vmds_root)
      absent   – set di ref referenziate ma non trovate
    """
    present = set()
    absent  = set()

    def add_models_and_tex(node):
        for mp in node.get("models", []):
            present.add(mp)
            for tex in model_to_textures.get(mp, []):
                if tex in known_tex:
                    present.add(tex)
                else:
                    absent.add(tex)
        for ref in node.get("missing_models", []):
            absent.add(ref)

    # Modelli diretti e missing della variant stessa
    add_models_and_tex(variant)
    for ref in variant.get("missing_vmds", []):
        absent.add(ref)

    # Percorri ricorsivamente tutti i VMD referenziati
    visited = set()
    queue   = list(variant.get("vmds", []))

    while queue:
        vid = queue.pop(0).lower()
        if vid in visited:
            continue
        visited.add(vid)

        node = center_by_id.get(vid)
        if node:
            # VMD centrale trovato
            present.add(f"{node['folder']}/{node['file']}")
            add_models_and_tex(node)
            for sub_id in node.get("sub_vmds", []):
                if sub_id.lower() not in visited:
                    queue.append(sub_id)
        else:
            # Prova tra le right variants (ref intra-variante)
            node = right_by_id.get(vid)
            if node and node["id"].lower() != variant["id"].lower():
                add_models_and_tex(node)
                for ref in node.get("missing_vmds", []):
                    absent.add(ref)
                for sub_id in node.get("vmds", []):
                    if sub_id.lower() not in visited:
                        queue.append(sub_id)
            else:
                absent.add(vid + ".variantmeshdefinition")

    return present, absent


def main():
    # ── Scansione completa (riutilizza tutta la logica di vmd-generate) ──
    print("\n── Scansione ──────────────────────────────")
    (models_tree, center_vmds, right_vmds,
     textures_tree, tex_to_models, model_to_textures) = _vmd.build_data()

    center_by_id  = {v["id"].lower(): v for v in center_vmds}
    right_by_id   = {v["id"].lower(): v for v in right_vmds}
    right_by_file = {v["file"].lower(): v for v in right_vmds}

    # Set di tutti i path texture presenti nella cartella mod
    known_tex = {
        f"{folder}/{f}"
        for folder, files in textures_tree.items()
        for f in files
    }

    # Calcola il prefisso relativo della cartella variants
    # (per includere il file .variantmeshdefinition stesso nell'output)
    try:
        variants_prefix = str(
            Path(_vmd.CONFIG["variants_root"]).relative_to(
                Path(_vmd.CONFIG["models_roots"][0])
            )
        ).replace("\\", "/")
    except (ValueError, IndexError):
        variants_prefix = "variantmeshdefinitions"

    # ── Leggi file di input ──────────────────────────────────────
    units     = read_lines(UNITS_VARIANTS_FILE)
    added_raw = read_lines(ADDED_FILES_FILE)
    added_names = {Path(a).name.lower() for a in added_raw}

    def is_added(path_str):
        return Path(path_str).name.lower() in added_names

    print(f"  →  Varianti da analizzare : {len(units)}")
    print(f"  →  File già aggiunti      : {len(added_raw)}\n")

    # ── Risolvi dipendenze per ogni variant ─────────────────────
    results = []

    for unit in units:
        stem = Path(unit).stem.lower()
        file = stem + ".variantmeshdefinition"

        variant = right_by_id.get(stem) or right_by_file.get(file)
        if variant is None:
            results.append((unit, set(), {f"variant non trovata: {unit}"}))
            continue

        present, absent = resolve_deps(
            variant, center_by_id, right_by_id, model_to_textures, known_tex
        )

        # Aggiungi il file della variant stessa
        variant_file_path = f"{variants_prefix}/{variant['file']}"
        present.add(variant_file_path)

        # Rimuovi ciò che è già stato aggiunto
        present_needed = {p for p in present if not is_added(p)}
        absent_needed  = {a for a in absent  if not is_added(a)}

        results.append((unit, present_needed, absent_needed))

    # ── Scrivi needed_files.txt ──────────────────────────────────
    out = ["Needed Files Report", "=" * 62, ""]
    total_p = total_a = 0

    for variant_name, present_needed, absent_needed in results:
        out.append("─" * 62)
        out.append(f"VARIANT: {variant_name}")
        out.append("─" * 62)

        # Suddividi per tipo di file per leggibilità
        def split_by_type(paths):
            vmds    = sorted(p for p in paths if p.lower().endswith(".variantmeshdefinition"))
            models  = sorted(p for p in paths if p.lower().endswith(".rigid_model_v2"))
            textures = sorted(p for p in paths if p.lower().endswith(".dds"))
            other   = sorted(p for p in paths
                             if not any(p.lower().endswith(e)
                                        for e in (".variantmeshdefinition", ".rigid_model_v2", ".dds")))
            return vmds + models + textures + other

        if present_needed:
            out.append(f"\n  [PRESENTI - da aggiungere al pack]  ({len(present_needed)})")
            for p in split_by_type(present_needed):
                out.append(f"    {p}")
            total_p += len(present_needed)
        else:
            out.append("\n  [PRESENTI - nessuno da aggiungere]")

        if absent_needed:
            out.append(f"\n  [ASSENTI - file non trovati nei folder mod]  ({len(absent_needed)})")
            for a in split_by_type(absent_needed):
                out.append(f"    {a}")
            total_a += len(absent_needed)

        out.append("")

    out += [
        "=" * 62,
        f"TOTALE presenti da aggiungere : {total_p}",
        f"TOTALE assenti (non trovati)  : {total_a}",
    ]

    Path(OUTPUT_FILE).write_text("\n".join(out), encoding="utf-8")
    print(f"✓  Scritto: {OUTPUT_FILE}")
    print(f"   Presenti da aggiungere : {total_p}")
    print(f"   Assenti (non trovati)  : {total_a}\n")


if __name__ == "__main__":
    main()
