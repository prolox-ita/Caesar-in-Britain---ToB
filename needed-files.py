#!/usr/bin/env python3
"""
Needed Files Checker + Copier
──────────────────────────────
Legge vmd-viewer.txt per la catena variant → VMD → modelli,
MODEL_TO_TEXTURES dall'HTML per le texture, poi:

  1. Scrive needed_files.txt separando PRESENTI e ASSENTI
     (ogni file una sola volta; già in added_files.txt vengono rimossi)
  2. Copia i PRESENTI in CIB_DEST mantenendo la gerarchia
  3. Aggiunge i copiati ad added_files.txt
  4. Riscrive needed_files.txt con solo ASSENTI e copia fallite

Usage:
  1. Genera vmd-viewer.txt e vmd-viewer.html con vmd-generate.py
  2. Scrivi in units_variants.txt i nomi delle variant (uno per riga)
  3. Opzionalmente scrivi in added_files.txt i file già nel pack
  4. Esegui: python needed-files.py
"""

import json, re, shutil
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
TXT_FILE   = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.txt"
HTML_FILE  = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.html"

# Radice del mod: tutti i path relativi del txt partono da qui
MOD_ROOT = r"D:\Thrones of Britannia\modding\variantmeshes"

# Prefisso cartella variant destre (relativo a MOD_ROOT)
VARIANTS_PREFIX = "variantmeshdefinitions"

UNITS_VARIANTS_FILE = r"C:\Users\loren\Desktop\MK1212-website\units_variants.txt"
ADDED_FILES_FILE    = r"C:\Users\loren\Desktop\MK1212-website\added_files.txt"
OUTPUT_FILE         = r"C:\Users\loren\Desktop\MK1212-website\needed_files.txt"
CIB_DEST = r"C:\Users\loren\Desktop\MK1212-website\cib\da aggiungere\variantmeshes"
# ═══════════════════════════════════════════════════════════════


# ── Parsing di vmd-viewer.txt ────────────────────────────────────

def parse_txt(txt_path):
    """
    Legge vmd-viewer.txt e restituisce 4 indici:
      tex_by_name     : filename.lower() → "folder/filename"
      model_by_name   : filename.lower() → "folder/filename"
      center_by_id    : stem.lower()     → dict con file/folder/models/sub_vmds/missing
      variant_by_id   : stem.lower()     → dict con file/vmds/models/missing_vmds/missing_models
    """
    tex_by_name    = {}
    model_by_name  = {}
    center_by_id   = {}
    variant_by_id  = {}

    col = 0          # 1=tex 2=models 3=center 4=variants
    folder   = ""
    cur_vmd  = None
    cur_var  = None

    def _strip_parse_warn(s):
        return s[:-len(" ⚠parse")] if s.endswith(" ⚠parse") else s

    for raw in Path(txt_path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip()

        # ── Rilevamento sezione ──────────────────────────────────
        if   line.startswith("COLONNA 1"): col = 1; folder = ""; continue
        elif line.startswith("COLONNA 2"): col = 2; folder = ""; continue
        elif line.startswith("COLONNA 3"): col = 3; folder = ""; cur_vmd = None; continue
        elif line.startswith("COLONNA 4"): col = 4; cur_var = None; continue
        if col == 0: continue
        if line.startswith("═") or line.startswith("─") or not line.strip(): continue

        # ── Col 1 e 2: textures e modelli ────────────────────────
        if col in (1, 2):
            if line.startswith("  [") and line.endswith("]"):
                folder = line.strip()[1:-1]
            elif line.startswith("    "):
                fname = line.strip()
                path  = f"{folder}/{fname}"
                if col == 1: tex_by_name[fname.lower()]   = path
                else:        model_by_name[fname.lower()]  = path

        # ── Col 3: VMD centrali ──────────────────────────────────
        elif col == 3:
            if line.startswith("  [") and line.endswith("]"):
                folder  = line.strip()[1:-1]
                cur_vmd = None
            elif line.startswith("    ") and not line.startswith("      "):
                fname = _strip_parse_warn(line.strip())
                if fname.lower().endswith(".variantmeshdefinition"):
                    cur_vmd = {"file": fname, "folder": folder,
                               "models": [], "sub_vmds": [], "missing": []}
                    center_by_id[Path(fname).stem.lower()] = cur_vmd
            elif line.startswith("      ") and cur_vmd is not None:
                content = line.strip()
                if content.startswith("modelli    :"):
                    cur_vmd["models"]   = _csv(content, "modelli    :")
                elif content.startswith("sub-vmd    :"):
                    cur_vmd["sub_vmds"] = _csv(content, "sub-vmd    :")
                elif content.startswith("⚠ mancante :"):
                    cur_vmd["missing"].append(content[len("⚠ mancante :"):].strip())

        # ── Col 4: varianti destre ───────────────────────────────
        elif col == 4:
            if line.startswith("  ") and not line.startswith("    "):
                fname = _strip_parse_warn(line.strip())
                if fname.lower().endswith(".variantmeshdefinition"):
                    cur_var = {"file": fname, "vmds": [], "models": [],
                               "missing_vmds": [], "missing_models": []}
                    variant_by_id[Path(fname).stem.lower()] = cur_var
            elif line.startswith("    ") and cur_var is not None:
                content = line.strip()
                if content.startswith("vmd         :"):
                    cur_var["vmds"]           = _csv(content, "vmd         :")
                elif content.startswith("modelli     :"):
                    cur_var["models"]          = _csv(content, "modelli     :")
                elif content.startswith("⚠ vmd mancante   :"):
                    cur_var["missing_vmds"].append(content[len("⚠ vmd mancante   :"):].strip())
                elif content.startswith("⚠ model mancante :"):
                    cur_var["missing_models"].append(content[len("⚠ model mancante :"):].strip())

    return tex_by_name, model_by_name, center_by_id, variant_by_id


def _csv(line, prefix):
    """Estrae lista CSV dopo un prefisso."""
    rest = line[len(prefix):].strip()
    return [x.strip() for x in rest.split(",") if x.strip()]


# ── MODEL_TO_TEXTURES dall'HTML ──────────────────────────────────

def load_model_to_textures(html_path):
    try:
        html = Path(html_path).read_text(encoding="utf-8", errors="replace")
        m = re.search(r'const MODEL_TO_TEXTURES\s*=\s*', html)
        if not m:
            return {}
        val, _ = json.JSONDecoder().raw_decode(html, m.end())
        return val
    except Exception as e:
        print(f"  ⚠  Impossibile leggere MODEL_TO_TEXTURES dall'HTML: {e}")
        return {}


# ── Risoluzione dipendenze ────────────────────────────────────────

def resolve(unit_stem, variant_by_id, center_by_id,
            model_by_name, tex_by_name, model_to_textures):
    """
    Risolve tutte le dipendenze di una variante.
    Ritorna (present, absent) — set di path (o ref) univoche.
    """
    present = set()   # path relativa trovata nel mod
    absent  = set()   # ref non trovata

    variant = variant_by_id.get(unit_stem)
    if variant is None:
        return present, absent

    # Il file della variante stessa
    present.add(f"{VARIANTS_PREFIX}/{variant['file']}")

    # Modelli diretti nella variante
    _add_models(variant.get("models", []), model_by_name,
                model_to_textures, tex_by_name, present, absent)
    for ref in variant.get("missing_vmds", []):
        absent.add(ref)
    for ref in variant.get("missing_models", []):
        absent.add(ref)

    # VMD centrali referenziati (ricorsivo via sub_vmds)
    visited = set()
    queue   = [v.lower() for v in variant.get("vmds", [])]

    while queue:
        vid = queue.pop(0)
        if vid in visited:
            continue
        visited.add(vid)

        vmd = center_by_id.get(vid)
        if vmd:
            present.add(f"{vmd['folder']}/{vmd['file']}")
            _add_models(vmd.get("models", []), model_by_name,
                        model_to_textures, tex_by_name, present, absent)
            for ref in vmd.get("missing", []):
                absent.add(ref)
            for sub in vmd.get("sub_vmds", []):
                if sub.lower() not in visited:
                    queue.append(sub.lower())
        else:
            # Potrebbe essere un'altra right variant
            if vid in variant_by_id:
                other = variant_by_id[vid]
                _add_models(other.get("models", []), model_by_name,
                            model_to_textures, tex_by_name, present, absent)
                for ref in other.get("missing_models", []):
                    absent.add(ref)
                for sub in other.get("vmds", []):
                    if sub.lower() not in visited:
                        queue.append(sub.lower())
            else:
                absent.add(vid + ".variantmeshdefinition")

    return present, absent


def _add_models(model_names, model_by_name, model_to_textures,
                tex_by_name, present, absent):
    for fname in model_names:
        full = model_by_name.get(fname.lower())
        if full:
            present.add(full)
            for tex in model_to_textures.get(full, []):
                tname = Path(tex).name.lower()
                if tname in tex_by_name:
                    present.add(tex_by_name[tname])
                else:
                    absent.add(tex)
        else:
            absent.add(fname)


# ── Utilità ──────────────────────────────────────────────────────

def read_lines(path):
    p = Path(path)
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def sort_by_type(paths):
    ext_order = (".variantmeshdefinition", ".rigid_model_v2", ".dds")
    out = []
    for e in ext_order:
        out += sorted(p for p in paths if p.lower().endswith(e))
    out += sorted(p for p in paths if not any(p.lower().endswith(e) for e in ext_order))
    return out


def source_dest(rel_path):
    root   = Path(MOD_ROOT)
    p      = rel_path.replace("\\", "/")
    prefix = root.name.lower() + "/"
    stripped = p[len(prefix):] if p.lower().startswith(prefix) else p
    return root / stripped, Path(CIB_DEST) / stripped


def write_needed(path, present_map, absent_map, suffix=""):
    SEP = "═" * 62
    lines = [f"Needed Files Report{suffix}", SEP, ""]
    if present_map:
        lines += [f"PRESENTI - da aggiungere  ({len(present_map)} file)", "─" * 62]
        for f in sort_by_type(present_map):
            lines.append(f"  {f}   [{', '.join(sorted(present_map[f]))}]")
        lines.append("")
    if absent_map:
        lines += [f"ASSENTI - non trovati nei folder mod  ({len(absent_map)} file)", "─" * 62]
        for f in sort_by_type(absent_map):
            lines.append(f"  {f}   [{', '.join(sorted(absent_map[f]))}]")
        lines.append("")
    lines += [SEP,
              f"Presenti da aggiungere : {len(present_map)}",
              f"Assenti (non trovati)  : {len(absent_map)}"]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("\n── Lettura vmd-viewer.txt ─────────────────")
    tex_by_name, model_by_name, center_by_id, variant_by_id = parse_txt(TXT_FILE)
    print(f"  ✓  Textures   : {len(tex_by_name)}")
    print(f"  ✓  Modelli    : {len(model_by_name)}")
    print(f"  ✓  VMD centro : {len(center_by_id)}")
    print(f"  ✓  Varianti   : {len(variant_by_id)}")

    model_to_textures = load_model_to_textures(HTML_FILE)
    print(f"  ✓  MODEL_TO_TEXTURES: {len(model_to_textures)} entries")

    units     = read_lines(UNITS_VARIANTS_FILE)
    added_raw = read_lines(ADDED_FILES_FILE)
    added_names = {Path(a).name.lower() for a in added_raw}

    def is_added(p): return Path(p).name.lower() in added_names

    print(f"\n  →  Varianti : {len(units)}   già aggiunti : {len(added_raw)}\n")

    # ── Risolvi ──────────────────────────────────────────────────
    all_present: dict = defaultdict(set)
    all_absent:  dict = defaultdict(set)

    for unit in units:
        stem = Path(unit).stem.lower()
        if stem not in variant_by_id:
            print(f"  ⚠  [{unit}] non trovata nel txt (rigenerare vmd-viewer con vmd-generate.py)")
            all_absent[f"variant non trovata: {unit}"].add(unit)
            continue

        v = variant_by_id[stem]
        present, absent = resolve(stem, variant_by_id, center_by_id,
                                  model_by_name, tex_by_name, model_to_textures)

        n_filtered = sum(1 for p in present if is_added(p))
        print(f"  ✓  [{unit}]  vmds={len(v['vmds'])} models={len(v['models'])} "
              f"→ {len(present)} presenti, {len(absent)} assenti"
              + (f"  ({n_filtered} già in added_files)" if n_filtered else ""))

        for p in present:
            if not is_added(p): all_present[p].add(unit)
        for a in absent:
            if not is_added(a): all_absent[a].add(unit)

    # ── Scrivi needed_files.txt ──────────────────────────────────
    write_needed(OUTPUT_FILE, all_present, all_absent)
    print(f"\n✓  needed_files.txt  ({len(all_present)} presenti, {len(all_absent)} assenti)")

    if not all_present:
        print("   Nessun file presente da copiare.\n")
        return

    # ── Copia PRESENTI → CIB_DEST ────────────────────────────────
    print(f"\n── Copia → {CIB_DEST}")
    copied, failed = [], []

    for rel in sort_by_type(all_present):
        src, dst = source_dest(rel)
        if not src.exists():
            print(f"  ⚠  Non su disco: {src}")
            failed.append(rel)
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
        except Exception as e:
            print(f"  ⚠  Errore: {rel}: {e}")
            failed.append(rel)

    print(f"  ✓  Copiati : {len(copied)}" + (f"   Falliti : {len(failed)}" if failed else ""))

    # ── Aggiorna added_files.txt ─────────────────────────────────
    if copied:
        Path(ADDED_FILES_FILE).write_text(
            "\n".join(read_lines(ADDED_FILES_FILE) + copied) + "\n", encoding="utf-8")
        print(f"  ✓  added_files.txt +{len(copied)}")

    # ── Riscrive needed_files.txt finale ─────────────────────────
    remaining = {p: v for p, v in all_present.items() if p not in set(copied)}
    write_needed(OUTPUT_FILE, remaining, all_absent, suffix=" — post copia")
    print(f"  ✓  needed_files.txt aggiornato  "
          f"(rimasti: {len(remaining)} presenti, {len(all_absent)} assenti)\n")


if __name__ == "__main__":
    main()
