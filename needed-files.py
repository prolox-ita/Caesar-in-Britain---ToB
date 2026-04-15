#!/usr/bin/env python3
"""
Needed Files
─────────────
Legge units variants.txt, segue tutte le connessioni in vmd-viewer.txt
(vmd → sub-vmd → ... → v2 → tex) e scrive needed_files.txt.

Usage:
  1. Genera vmd-viewer.txt e vmd-viewer.html con vmd-generate.py
  2. Scrivi in "units variants.txt" i nomi delle variant (una per riga)
  3. Esegui: python needed-files.py
"""

import json, re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
TXT_FILE    = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.txt"
HTML_FILE   = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.html"
UNITS_FILE  = r"C:\Users\loren\Desktop\MK1212-website\units variants.txt"
ADDED_FILE  = r"C:\Users\loren\Desktop\MK1212-website\added_files.txt"
OUTPUT      = r"C:\Users\loren\Desktop\MK1212-website\needed_files.txt"
# ═══════════════════════════════════════════════════════════════


# ── Parsing vmd-viewer.txt ───────────────────────────────────────

def parse_txt(path):
    """
    Legge vmd-viewer.txt e restituisce 4 dizionari:
      tex_by_name    : filename.lower() → "folder/filename"   (col 1)
      model_by_name  : filename.lower() → "folder/filename"   (col 2)
      center_by_id   : stem.lower()     → { file, folder,     (col 3)
                                             models:[fname,…],
                                             sub_vmds:[id,…],
                                             missing:[ref,…] }
      variant_by_id  : stem.lower()     → { file,             (col 4)
                                             vmds:[id,…],
                                             models:[fname,…],
                                             missing_vmds:[…],
                                             missing_models:[…] }
    """
    tex_by_name   = {}
    model_by_name = {}
    center_by_id  = {}
    variant_by_id = {}

    col      = 0
    folder   = ""
    cur_vmd  = None
    cur_var  = None

    def strip_warn(s):
        return s[:-len(" ⚠parse")] if s.endswith(" ⚠parse") else s

    def csv(line, prefix):
        return [x.strip() for x in line[len(prefix):].strip().split(",") if x.strip()]

    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.rstrip()

        # sezione
        if   line.startswith("COLONNA 1"): col = 1; folder = ""; continue
        elif line.startswith("COLONNA 2"): col = 2; folder = ""; continue
        elif line.startswith("COLONNA 3"): col = 3; folder = ""; cur_vmd = None; continue
        elif line.startswith("COLONNA 4"): col = 4; cur_var = None; continue
        if col == 0: continue
        if not line.strip() or line.lstrip("═─").__len__() == 0: continue

        # col 1 e 2 ─ textures e modelli
        if col in (1, 2):
            if line.startswith("  [") and line.endswith("]"):
                folder = line.strip()[1:-1]
            elif line.startswith("    "):
                fname = line.strip()
                if col == 1: tex_by_name[fname.lower()]   = f"{folder}/{fname}"
                else:        model_by_name[fname.lower()] = f"{folder}/{fname}"

        # col 3 ─ VMD centrali
        elif col == 3:
            if line.startswith("  [") and line.endswith("]"):
                folder = line.strip()[1:-1]; cur_vmd = None
            elif line.startswith("    ") and not line.startswith("      "):
                fname = strip_warn(line.strip())
                if fname.lower().endswith(".variantmeshdefinition"):
                    cur_vmd = {"file": fname, "folder": folder,
                               "models": [], "sub_vmds": [], "missing": []}
                    center_by_id[Path(fname).stem.lower()] = cur_vmd
            elif line.startswith("      ") and cur_vmd is not None:
                c = line.strip()
                if   c.startswith("modelli    :"): cur_vmd["models"]   = csv(c, "modelli    :")
                elif c.startswith("sub-vmd    :"): cur_vmd["sub_vmds"] = csv(c, "sub-vmd    :")
                elif c.startswith("⚠ mancante :"): cur_vmd["missing"].append(c[len("⚠ mancante :"):].strip())

        # col 4 ─ varianti destre
        elif col == 4:
            if line.startswith("  ") and not line.startswith("    "):
                fname = strip_warn(line.strip())
                if fname.lower().endswith(".variantmeshdefinition"):
                    cur_var = {"file": fname, "vmds": [], "models": [],
                               "missing_vmds": [], "missing_models": []}
                    variant_by_id[Path(fname).stem.lower()] = cur_var
            elif line.startswith("    ") and cur_var is not None:
                c = line.strip()
                if   c.startswith("vmd         :"): cur_var["vmds"]           = csv(c, "vmd         :")
                elif c.startswith("modelli     :"): cur_var["models"]          = csv(c, "modelli     :")
                elif c.startswith("⚠ vmd mancante   :"): cur_var["missing_vmds"].append(c[len("⚠ vmd mancante   :"):].strip())
                elif c.startswith("⚠ model mancante :"): cur_var["missing_models"].append(c[len("⚠ model mancante :"):].strip())

    return tex_by_name, model_by_name, center_by_id, variant_by_id


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
        print(f"  ⚠  MODEL_TO_TEXTURES non leggibile: {e}")
        return {}


# ── Raccolta dipendenze ricorsiva ────────────────────────────────

def collect(variant_stem, variant_by_id, center_by_id,
            model_by_name, tex_by_name, model_to_textures):
    """
    Raccoglie ricorsivamente tutti i file necessari per una variant.
    Ritorna:
      vmds    – set di path VMD  (folder/file.variantmeshdefinition)
      v2s     – set di path V2   (folder/file.rigid_model_v2)
      texs    – set di filename texture (.dds)
      missing – set di ref non trovate
    """
    vmds    = set()
    v2s     = set()
    texs    = set()
    missing = set()

    variant = variant_by_id.get(variant_stem)
    if variant is None:
        return None

    # Modelli diretti della variant
    _add_models(variant.get("models", []), model_by_name,
                model_to_textures, tex_by_name, v2s, texs)
    for r in variant.get("missing_models", []): missing.add(r)
    for r in variant.get("missing_vmds",   []): missing.add(r)

    # Percorri i VMD referenziati ricorsivamente
    visited = set()
    queue   = [v.lower() for v in variant.get("vmds", [])]

    while queue:
        vid = queue.pop(0)
        if vid in visited:
            continue
        visited.add(vid)

        node = center_by_id.get(vid)
        if node:
            vmds.add(f"{node['folder']}/{node['file']}")
            _add_models(node.get("models", []), model_by_name,
                        model_to_textures, tex_by_name, v2s, texs)
            for r in node.get("missing", []): missing.add(r)
            for sub in node.get("sub_vmds", []):
                if sub.lower() not in visited:
                    queue.append(sub.lower())
        else:
            # Ref intra-variante o non trovata
            other = variant_by_id.get(vid)
            if other:
                _add_models(other.get("models", []), model_by_name,
                            model_to_textures, tex_by_name, v2s, texs)
                for r in other.get("missing_models", []): missing.add(r)
                for sub in other.get("vmds", []):
                    if sub.lower() not in visited:
                        queue.append(sub.lower())
            else:
                missing.add(vid + ".variantmeshdefinition")

    return vmds, v2s, texs, missing


def _add_models(names, model_by_name, model_to_textures,
                tex_by_name, v2s, texs):
    for fname in names:
        # Il modello è presente nel mod (è nella lista "models" del vmd)
        full = model_by_name.get(fname.lower(), fname)
        v2s.add(full)
        # Texture associate
        for tex in model_to_textures.get(full, []):
            tname = Path(tex).name.lower()
            if tname in tex_by_name:
                texs.add(tex_by_name[tname])
            else:
                texs.add(Path(tex).name)   # path base-game: solo filename


# ── Utilità ──────────────────────────────────────────────────────

def read_lines(path):
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  File non trovato: {path}")
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def load_added(path):
    """Carica added_files.txt e restituisce un set di path normalizzati (lowercase, slash)."""
    p = Path(path)
    if not p.exists():
        return set()
    result = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            result.add(line.replace("\\", "/").lower())
    return result


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("\n── Lettura vmd-viewer.txt ─────────────────")
    tex_by_name, model_by_name, center_by_id, variant_by_id = parse_txt(TXT_FILE)
    print(f"  ✓  Textures   : {len(tex_by_name)}")
    print(f"  ✓  Modelli    : {len(model_by_name)}")
    print(f"  ✓  VMD centro : {len(center_by_id)}")
    print(f"  ✓  Varianti   : {len(variant_by_id)}")

    model_to_textures = load_model_to_textures(HTML_FILE)
    print(f"  ✓  Model→Tex  : {len(model_to_textures)} entries")

    units = read_lines(UNITS_FILE)
    if not units:
        print("\n  ⚠  units variants.txt vuoto o non trovato.\n")
        return
    print(f"\n  →  Varianti richieste: {len(units)}\n")

    added = load_added(ADDED_FILE)
    if added:
        print(f"  ✓  File già aggiunti (added_files.txt): {len(added)}\n")
    else:
        print(f"  ─  added_files.txt vuoto o non trovato — nessun filtro applicato\n")

    def already_added(path_str):
        return path_str.replace("\\", "/").lower() in added

    out = ["Needed Files", "═" * 62, ""]

    total_vmd = total_v2 = total_tex = total_miss = 0

    for unit in units:
        stem = Path(unit).stem.lower()
        result = collect(stem, variant_by_id, center_by_id,
                         model_by_name, tex_by_name, model_to_textures)

        out.append("─" * 62)
        out.append(f"VARIANT: {unit}")
        out.append("─" * 62)

        if result is None:
            out.append(f"  ⚠  Non trovata in vmd-viewer.txt (rigenerare con vmd-generate.py)")
            out.append("")
            print(f"  ⚠  [{unit}] non trovata")
            continue

        vmds, v2s, texs, missing = result

        # Filtra i file già presenti in added_files.txt (solo VMD, V2, TEX — non missing)
        vmds    = {f for f in vmds  if not already_added(f)}
        v2s     = {f for f in v2s   if not already_added(f)}
        texs    = {f for f in texs  if not already_added(f)}

        print(f"  ✓  [{unit}]  vmd={len(vmds)}  v2={len(v2s)}  tex={len(texs)}  missing={len(missing)}")

        if vmds:
            out.append(f"\n  VMD  ({len(vmds)})")
            for f in sorted(vmds): out.append(f"    {f}")

        if v2s:
            out.append(f"\n  V2   ({len(v2s)})")
            for f in sorted(v2s): out.append(f"    {f}")

        if texs:
            out.append(f"\n  TEX  ({len(texs)})")
            for f in sorted(texs): out.append(f"    {f}")

        if missing:
            out.append(f"\n  ⚠ NON TROVATI  ({len(missing)})")
            for f in sorted(missing): out.append(f"    {f}")

        out.append("")
        total_vmd  += len(vmds)
        total_v2   += len(v2s)
        total_tex  += len(texs)
        total_miss += len(missing)

    out += ["═" * 62,
            f"Totale VMD        : {total_vmd}",
            f"Totale V2         : {total_v2}",
            f"Totale TEX        : {total_tex}",
            f"Totale non trovati: {total_miss}"]

    Path(OUTPUT).write_text("\n".join(out), encoding="utf-8")
    print(f"\n✓  Scritto: {OUTPUT}\n")


if __name__ == "__main__":
    main()
