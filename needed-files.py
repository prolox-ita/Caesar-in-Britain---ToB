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

import json, re, shutil
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE
# ═══════════════════════════════════════════════════════════════
TXT_FILE     = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.txt"
HTML_FILE    = r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.html"
UNITS_FILE   = r"C:\Users\loren\Desktop\MK1212-website\units variants.txt"
ADDED_FILE   = r"C:\Users\loren\Desktop\MK1212-website\added_files.txt"
MISSING_FILE = r"C:\Users\loren\Desktop\MK1212-website\missing_files.txt"
MISSING_HTML = r"C:\Users\loren\Desktop\MK1212-website\missing-files.html"
OUTPUT       = r"C:\Users\loren\Desktop\MK1212-website\needed_files.txt"

# Cartella radice da cui copiare i file (es. dati estratti del gioco o della mod sorgente)
SOURCE_DIR   = r"D:\Thrones of Britannia\modding\variantmeshes"
# Destinazione copia — sottocartelle preservate
CIB_DIR      = r"D:\Thrones of Britannia\modding\cib\da aggiungere\variantmeshes"
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
                model_to_textures, tex_by_name, v2s, texs, missing)
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
                        model_to_textures, tex_by_name, v2s, texs, missing)
            for r in node.get("missing", []): missing.add(r)
            for sub in node.get("sub_vmds", []):
                if sub.lower() not in visited:
                    queue.append(sub.lower())
        else:
            # Ref intra-variante o non trovata
            other = variant_by_id.get(vid)
            if other:
                _add_models(other.get("models", []), model_by_name,
                            model_to_textures, tex_by_name, v2s, texs, missing)
                for r in other.get("missing_models", []): missing.add(r)
                for sub in other.get("vmds", []):
                    if sub.lower() not in visited:
                        queue.append(sub.lower())
            else:
                missing.add(vid + ".variantmeshdefinition")

    return vmds, v2s, texs, missing


def _add_models(names, model_by_name, model_to_textures,
                tex_by_name, v2s, texs, missing):
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
                missing.add(Path(tex).name)


# ── Utilità ──────────────────────────────────────────────────────

def read_lines(path):
    p = Path(path)
    if not p.exists():
        print(f"  ⚠  File non trovato: {path}")
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if l.strip() and not l.strip().startswith("#")]


def append_lines(path, lines):
    """Aggiunge righe al file (senza duplicati rispetto al contenuto esistente)."""
    p = Path(path)
    existing = set()
    if p.exists():
        existing = {l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
                    if l.strip() and not l.strip().startswith("#")}
    new_lines = [l for l in sorted(lines) if l not in existing]
    if new_lines:
        with p.open("a", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
    return len(new_lines)


def copy_files(present_files):
    """
    Copia i file da SOURCE_DIR/path → CIB_DIR/path preservando le sottocartelle.

    SOURCE_DIR punta a variantmeshes\. I file nella root di quella cartella
    vengono salvati con il prefisso "variantmeshes/" (es. "variantmeshes/foo.vmd"):
    in quel caso strippiamo quel prefisso per costruire il path sorgente corretto,
    mantenendolo però nel percorso di destinazione.

    Restituisce (copiati, non_trovati).
    """
    copied    = []
    not_found = []
    src_root  = Path(SOURCE_DIR)
    dst_root  = Path(CIB_DIR)
    src_name  = src_root.name.lower()   # "variantmeshes"

    for rel_path in sorted(present_files):
        norm  = rel_path.replace("\\", "/")
        parts = norm.split("/")

        # I file nella root di variantmeshes hanno folder="variantmeshes":
        # strippiamo quel prefisso solo per il percorso sorgente.
        if parts[0].lower() == src_name and len(parts) > 1:
            src_rel = "/".join(parts[1:])
        else:
            src_rel = norm

        src = src_root / src_rel.replace("/", "\\")
        dst = dst_root / norm.replace("/", "\\")

        if not src.exists():
            not_found.append(rel_path)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel_path)

    return copied, not_found


def norm_path(s):
    """Normalizza un path: lowercase, slash, rimuove prefisso variantmeshes/ se presente."""
    p = s.strip().replace("\\", "/").lower()
    if p.startswith("variantmeshes/"):
        p = p[len("variantmeshes/"):]
    return p


def load_added(path):
    """Carica added_files.txt e restituisce un set di path normalizzati."""
    p = Path(path)
    if not p.exists():
        return set()
    result = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            result.add(norm_path(line))
    return result


# ── Genera missing-files.html ────────────────────────────────────

def build_grouped(missing_path):
    """Legge missing_files.txt e restituisce {tex:{folder:[files]}, v2:{...}, vmd:{...}}."""
    cats = {"tex": {}, "v2": {}, "vmd": {}}
    p = Path(missing_path)
    if not p.exists():
        return cats
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        norm   = line.replace("\\", "/")
        name   = norm.split("/")[-1]
        folder = norm[: len(norm) - len(name) - 1] if "/" in norm else "(root)"
        if name.endswith(".dds"):
            cat = "tex"
        elif name.endswith(".rigid_model_v2"):
            cat = "v2"
        elif name.endswith(".variantmeshdefinition"):
            cat = "vmd"
        else:
            continue
        cats[cat].setdefault(folder, []).append(name)
    for cat in cats:
        for folder in cats[cat]:
            cats[cat][folder].sort()
    return cats


def generate_missing_html(missing_path, html_path):
    grouped = build_grouped(missing_path)
    total   = sum(len(f) for cat in grouped.values() for f in cat.values())
    data_js = json.dumps(grouped, ensure_ascii=False, indent=None)

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Missing Files</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#111;color:#bbb;font-family:'Consolas','Courier New',monospace;font-size:12px;height:100vh;display:flex;flex-direction:column;overflow:hidden}}
header{{padding:7px 14px;background:#1a1a1a;border-bottom:1px solid #8B0000;display:flex;align-items:center;gap:14px;flex-shrink:0}}
header h1{{font-size:.8rem;letter-spacing:.18em;color:#cc4444;font-weight:normal}}
.hint{{font-size:.68rem;color:#4a4a4a;flex:1}}
.ts{{font-size:.65rem;color:#3a5a3a;flex-shrink:0;white-space:nowrap}}
.columns{{display:flex;flex:1;overflow:hidden}}
.col{{flex:1;display:flex;flex-direction:column;border-right:1px solid #222;min-width:0}}
.col:last-child{{border-right:none}}
.col-head{{padding:7px 12px;background:#161616;border-bottom:1px solid #222;flex-shrink:0}}
.col-head-title{{font-size:.68rem;letter-spacing:.14em;color:#cc4444;text-transform:uppercase}}
.col-head-sub{{font-size:.6rem;color:#444;margin-top:2px}}
.col-count{{float:right;color:#555;font-size:.6rem;margin-top:1px}}
.col-body{{flex:1;overflow-y:auto;padding:3px 0}}
.col-body::-webkit-scrollbar{{width:3px}}
.col-body::-webkit-scrollbar-thumb{{background:#2a2a2a;border-radius:2px}}
.folder{{user-select:none}}
.folder-label{{display:flex;align-items:center;gap:5px;padding:3px 10px;cursor:pointer;color:#666;white-space:nowrap}}
.folder-label:hover{{background:rgba(255,255,255,.03)}}
.folder-arrow{{font-size:8px;color:#444;transition:transform .12s;flex-shrink:0;width:10px}}
.folder.open>.folder-label>.folder-arrow{{transform:rotate(90deg)}}
.folder-children{{display:none}}
.folder.open>.folder-children{{display:block}}
.item{{padding:3px 10px 3px 36px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#cc6666}}
.empty{{padding:12px;color:#3a3a3a;font-style:italic;font-size:.75rem}}
</style>
</head>
<body>
<header>
  <h1>&#9888; MISSING FILES</h1>
  <span class="hint">File referenziati ma non trovati &mdash; {total} totali</span>
  <span class="ts">Generato: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
</header>
<div class="columns">
  <div class="col">
    <div class="col-head"><span class="col-count" id="cnt-tex"></span>
      <div class="col-head-title">Textures</div><div class="col-head-sub">.dds</div></div>
    <div class="col-body" id="col-tex"></div>
  </div>
  <div class="col">
    <div class="col-head"><span class="col-count" id="cnt-v2"></span>
      <div class="col-head-title">Models</div><div class="col-head-sub">.rigid_model_v2</div></div>
    <div class="col-body" id="col-v2"></div>
  </div>
  <div class="col">
    <div class="col-head"><span class="col-count" id="cnt-vmd"></span>
      <div class="col-head-title">Definitions</div><div class="col-head-sub">.variantmeshdefinition</div></div>
    <div class="col-body" id="col-vmd"></div>
  </div>
</div>
<script>
'use strict';
const DATA = {data_js};
function mk(t,c){{const e=document.createElement(t);if(c)e.className=c;return e;}}
function render(cat, colId, cntId){{
  const grouped=DATA[cat]||{{}};
  const col=document.getElementById(colId);
  const cnt=document.getElementById(cntId);
  let total=0;
  for(const files of Object.values(grouped)) total+=files.length;
  cnt.textContent=total;
  if(total===0){{const e=mk('div','empty');e.textContent='Nessun file mancante';col.appendChild(e);return;}}
  for(const [folder,files] of Object.entries(grouped).sort()){{
    const fe=mk('div','folder open');
    const le=mk('div','folder-label');
    le.innerHTML=`<span class="folder-arrow">&#9654;</span><span style="opacity:.4;margin-right:3px">&#128193;</span>`+folder+'/';
    le.onclick=()=>fe.classList.toggle('open');
    fe.appendChild(le);
    const ce=mk('div','folder-children');
    for(const f of files){{
      const it=mk('div','item');
      it.textContent=f;
      it.title=folder!=='(root)'?folder+'/'+f:f;
      ce.appendChild(it);
    }}
    fe.appendChild(ce);
    col.appendChild(fe);
  }}
}}
render('tex','col-tex','cnt-tex');
render('v2','col-v2','cnt-v2');
render('vmd','col-vmd','cnt-vmd');
</script>
</body>
</html>"""

    Path(html_path).write_text(html, encoding="utf-8")
    print(f"  ✓  missing-files.html  ({total} file mancanti)")


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
        return norm_path(path_str) in added

    out = ["Needed Files", "═" * 62, ""]

    total_vmd = total_v2 = total_tex = total_miss = 0
    all_present = set()   # tutti i file trovati (VMD + V2 + TEX), da copiare
    all_missing = set()   # tutti i NON TROVATI, da loggare in missing_files.txt

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
        all_present.update(vmds, v2s, texs)
        all_missing.update(missing)

    out += ["═" * 62,
            f"Totale VMD        : {total_vmd}",
            f"Totale V2         : {total_v2}",
            f"Totale TEX        : {total_tex}",
            f"Totale non trovati: {total_miss}"]

    Path(OUTPUT).write_text("\n".join(out), encoding="utf-8")
    print(f"\n✓  Scritto: {OUTPUT}\n")

    # ── 1. NON TROVATI → missing_files.txt ──────────────────────────
    if all_missing:
        n = append_lines(MISSING_FILE, all_missing)
        print(f"  ✓  missing_files.txt  (+{n} nuovi, {len(all_missing)} totali questa run)")
    else:
        print(f"  ─  Nessun file mancante da registrare")

    # ── 2. Copia file presenti → cib/da aggiungere ──────────────────
    print(f"\n── Copia file ({len(all_present)}) → {CIB_DIR}")
    copied, not_found_on_disk = copy_files(all_present)
    print(f"  ✓  Copiati    : {len(copied)}")
    if not_found_on_disk:
        print(f"  ⚠  Non trovati su disco ({len(not_found_on_disk)}):")
        for f in not_found_on_disk:
            print(f"       {f}")

    # ── 3. File copiati → added_files.txt ───────────────────────────
    if copied:
        n = append_lines(ADDED_FILE, copied)
        print(f"\n  ✓  added_files.txt  (+{n} nuovi aggiunti)\n")
    else:
        print(f"\n  ─  Nessun file da aggiungere ad added_files.txt\n")

    # ── 4. Rimuovi da missing_files.txt i file ora in added_files.txt ─
    mp = Path(MISSING_FILE)
    if mp.exists():
        current_added = load_added(ADDED_FILE)
        lines_before  = [l for l in mp.read_text(encoding="utf-8", errors="replace").splitlines()
                         if l.strip()]
        lines_after   = [l for l in lines_before
                         if l.strip().startswith("#")
                         or norm_path(l.strip()) not in current_added]
        removed = len(lines_before) - len(lines_after)
        if removed:
            mp.write_text("\n".join(lines_after) + ("\n" if lines_after else ""), encoding="utf-8")
            print(f"  ✓  missing_files.txt  (-{removed} rimossi perché ora in added_files.txt)\n")
        else:
            print(f"  ─  missing_files.txt invariato\n")

    # ── 5. Genera missing-files.html ────────────────────────────────
    generate_missing_html(MISSING_FILE, MISSING_HTML)


if __name__ == "__main__":
    main()
