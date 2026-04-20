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
CSV_FILE     = r"C:\Users\loren\Desktop\MK1212-website\units_report.csv"
UNIT_REPORT  = r"C:\Users\loren\Desktop\MK1212-website\unit-report.html"

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


# ── MODEL_TO_TEXTURES dall'HTML (o per convenzione nome) ─────────

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


def build_model_to_textures_by_name(model_by_name, tex_by_name):
    """
    Associa textures ai modelli per convenzione nome Total War:
    model 'unit_body_lod0.variantmesh' → strip _lod\d+ → base 'unit_body'
    → textures il cui stem == base oppure inizia con base + '_'
    (es. 'unit_body_diffuse.dds', 'unit_body_normal.dds', ecc.)
    """
    tex_by_stem = {Path(fn).stem: fp for fn, fp in tex_by_name.items()}
    result = {}
    for fname, model_full in model_by_name.items():
        base = re.sub(r'_lod\d+$', '', Path(fname).stem, flags=re.IGNORECASE)
        matches = [fp for ts, fp in tex_by_stem.items()
                   if ts == base or ts.startswith(base + '_')]
        if matches:
            result[model_full] = matches
    return result


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

def build_relations(all_missing_lines, model_to_textures, model_by_name, center_by_id):
    """
    Da tutti i file mancanti + dati VMD globali, calcola:
      tex_items, v2_items, vmd_items  — liste di {id, name, folder, missing}
      links                           — {key: [key,...]} per evidenziare le connessioni
    Nei V2/VMD compare sia il file mancante che il file presente che lo contiene.
    """
    def parts(f):
        p = f.replace("\\", "/").split("/")
        return "/".join(p[:-1]) if len(p) > 1 else "(root)", p[-1]

    # Categorizza nomi mancanti (solo filename, lowercase)
    miss_tex = {f.replace("\\","/").split("/")[-1].lower()
                for f in all_missing_lines if f.lower().endswith(".dds")}
    miss_v2  = {f.replace("\\","/").split("/")[-1].lower()
                for f in all_missing_lines if f.lower().endswith(".rigid_model_v2")}
    miss_vmd = {f.replace("\\","/").split("/")[-1].lower()
                for f in all_missing_lines if f.lower().endswith(".variantmeshdefinition")}

    # ── TEX items ───────────────────────────────────────────────────
    tex_items = {}
    for f in all_missing_lines:
        if not f.lower().endswith(".dds"):
            continue
        folder, name = parts(f)
        tex_items[name.lower()] = {"id": name.lower(), "name": name,
                                   "folder": folder, "missing": True}

    # ── TEX → V2 (da model_to_textures) ────────────────────────────
    tex_to_v2s = {}
    for v2_path, tex_list in model_to_textures.items():
        for tex in tex_list:
            tname = Path(tex).name.lower()
            if tname in tex_items:
                tex_to_v2s.setdefault(tname, set()).add(v2_path)

    # ── V2 → VMD (da center_by_id) ─────────────────────────────────
    v2_to_vmds = {}
    for node in center_by_id.values():
        vmd_path = f"{node['folder']}/{node['file']}"
        for fname in node.get("models", []):
            v2_path = model_by_name.get(fname.lower(), fname)
            v2_to_vmds.setdefault(v2_path, set()).add(vmd_path)

    # indice aggiuntivo per nome file (utile per V2 mancanti senza path pieno)
    v2name_to_vmds = {}
    for v2p, vmds in v2_to_vmds.items():
        v2name_to_vmds.setdefault(v2p.replace("\\","/").split("/")[-1].lower(), set()).update(vmds)

    # ── V2 items ────────────────────────────────────────────────────
    v2_items = {}

    for v2s in tex_to_v2s.values():
        for v2 in v2s:
            folder, name = parts(v2)
            v2_items[v2] = {"id": v2, "name": name, "folder": folder,
                            "missing": name.lower() in miss_v2}

    for f in all_missing_lines:
        if not f.lower().endswith(".rigid_model_v2"):
            continue
        _, name = parts(f)
        v2_full = model_by_name.get(name.lower(), f)
        if v2_full not in v2_items:
            folder2, name2 = parts(v2_full)
            v2_items[v2_full] = {"id": v2_full, "name": name2,
                                 "folder": folder2, "missing": True}

    # ── VMD items ───────────────────────────────────────────────────
    vmd_items = {}

    for v2 in v2_items:
        v2name = v2.replace("\\","/").split("/")[-1].lower()
        for vmd in v2_to_vmds.get(v2, set()) | v2name_to_vmds.get(v2name, set()):
            folder, name = parts(vmd)
            vmd_items[vmd] = {"id": vmd, "name": name, "folder": folder,
                              "missing": name.lower() in miss_vmd}

    for f in all_missing_lines:
        if not f.lower().endswith(".variantmeshdefinition"):
            continue
        _, name = parts(f)
        stem = name[:-len(".variantmeshdefinition")].lower()
        node = center_by_id.get(stem)
        vmd_full = f"{node['folder']}/{node['file']}" if node else f
        if vmd_full not in vmd_items:
            folder2, name2 = parts(vmd_full)
            vmd_items[vmd_full] = {"id": vmd_full, "name": name2,
                                   "folder": folder2, "missing": True}

    # ── Links bidirezionali ─────────────────────────────────────────
    links = {}
    def lnk(a, b):
        links.setdefault(a, set()).add(b)
        links.setdefault(b, set()).add(a)

    for tname, v2s in tex_to_v2s.items():
        for v2 in v2s:
            if v2 in v2_items:
                lnk(f"tex:{tname}", f"v2:{v2}")

    for v2 in v2_items:
        v2name = v2.replace("\\","/").split("/")[-1].lower()
        for vmd in v2_to_vmds.get(v2, set()) | v2name_to_vmds.get(v2name, set()):
            if vmd in vmd_items:
                lnk(f"v2:{v2}", f"vmd:{vmd}")

    return (
        sorted(tex_items.values(),  key=lambda x: x["id"]),
        sorted(v2_items.values(),   key=lambda x: x["id"]),
        sorted(vmd_items.values(),  key=lambda x: x["id"]),
        {k: sorted(v) for k, v in links.items()},
    )


_HTML_TMPL = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Missing Files</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#111;color:#bbb;font-family:'Consolas','Courier New',monospace;font-size:12px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{padding:7px 14px;background:#1a1a1a;border-bottom:1px solid #8B0000;display:flex;align-items:center;gap:14px;flex-shrink:0}
header h1{font-size:.8rem;letter-spacing:.18em;color:#cc4444;font-weight:normal}
.hint{font-size:.68rem;color:#4a4a4a;flex:1}
.ts{font-size:.65rem;color:#3a5a3a;flex-shrink:0;white-space:nowrap}
.toolbar{padding:5px 14px;background:#161616;border-bottom:1px solid #1e1e1e;display:flex;gap:8px;flex-shrink:0;align-items:center}
#search{flex:1;background:#0d0d0d;border:1px solid #2a2a2a;color:#bbb;padding:4px 9px;font-family:inherit;font-size:11px;outline:none;border-radius:2px}
#search:focus{border-color:#444}
#search::placeholder{color:#333}
.tb-btn{padding:4px 11px;background:transparent;border:1px solid #2a2a2a;color:#666;cursor:pointer;font-family:inherit;font-size:.7rem;letter-spacing:.08em;border-radius:2px;transition:all .15s;white-space:nowrap}
.tb-btn:hover{border-color:#C5B358;color:#C5B358}
.tb-btn.active{background:rgba(197,179,88,.12);border-color:#C5B358;color:#C5B358}
.columns{display:flex;flex:1;overflow:hidden}
.col{flex:1;display:flex;flex-direction:column;border-right:1px solid #222;min-width:0}
.col:last-child{border-right:none}
.col-head{padding:7px 12px;background:#161616;border-bottom:1px solid #222;flex-shrink:0}
.col-head-title{font-size:.68rem;letter-spacing:.14em;color:#cc4444;text-transform:uppercase}
.col-head-sub{font-size:.6rem;color:#444;margin-top:2px}
.col-count{float:right;font-size:.6rem;margin-top:1px}
.n-miss{color:#cc4444}.n-par{color:#555}
.col-body{flex:1;overflow-y:auto;padding:3px 0}
.col-body::-webkit-scrollbar{width:3px}
.col-body::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:2px}
.folder{user-select:none}
.folder-label{display:flex;align-items:center;gap:5px;padding:3px 10px;cursor:pointer;color:#555;white-space:nowrap}
.folder-label:hover{background:rgba(255,255,255,.03)}
.folder-arrow{font-size:8px;color:#444;transition:transform .12s;flex-shrink:0;width:10px}
.folder.open>.folder-label>.folder-arrow{transform:rotate(90deg)}
.folder-children{display:none}
.folder.open>.folder-children{display:block}
.item{padding:3px 10px 3px 36px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-left:2px solid transparent;cursor:pointer;transition:background .08s}
.item:hover{background:rgba(255,255,255,.04)}
.item.missing{color:#cc6666}
.item.parent{color:#8a7830}
.item.selected{background:rgba(255,255,255,.1);border-left-color:#ddd;color:#fff!important}
.item.connected{background:rgba(197,179,88,.1);border-left-color:#C5B358;color:#F5E6BE!important}
.empty{padding:12px;color:#3a3a3a;font-style:italic;font-size:.75rem}
#svg-overlay{position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:9999}
</style>
</head>
<body>
<header>
  <h1>&#9888; MISSING FILES</h1>
  <span class="hint">&#9632; <span style="color:#cc6666">mancante</span> &nbsp;&#9632; <span style="color:#8a7830">presente con dipendenze mancanti</span></span>
  <span class="ts">__TS__</span>
</header>
<div class="toolbar">
  <input id="search" type="text" placeholder="Cerca…" oninput="onSearch(this.value)">
  <button class="tb-btn" id="btn-filter" onclick="toggleFilter()">&#9672; Solo selezionati</button>
  <button class="tb-btn" onclick="clearAll()">&#10005; Deseleziona</button>
</div>
<div class="columns">
  <div class="col">
    <div class="col-head">
      <span class="col-count"><span class="n-miss" id="cm-tex"></span><span class="n-par" id="cp-tex"></span></span>
      <div class="col-head-title">Textures</div><div class="col-head-sub">.dds</div>
    </div>
    <div class="col-body" id="col-tex"></div>
  </div>
  <div class="col">
    <div class="col-head">
      <span class="col-count"><span class="n-miss" id="cm-v2"></span><span class="n-par" id="cp-v2"></span></span>
      <div class="col-head-title">Models</div><div class="col-head-sub">.rigid_model_v2</div>
    </div>
    <div class="col-body" id="col-v2"></div>
  </div>
  <div class="col">
    <div class="col-head">
      <span class="col-count"><span class="n-miss" id="cm-vmd"></span><span class="n-par" id="cp-vmd"></span></span>
      <div class="col-head-title">Definitions</div><div class="col-head-sub">.variantmeshdefinition</div>
    </div>
    <div class="col-body" id="col-vmd"></div>
  </div>
</div>
<svg id="svg-overlay"></svg>
<script>
'use strict';
const DATA=__DATA__;
const elMap={};
let lastKey=null;
let filterActive=false;

function mk(t,c){const e=document.createElement(t);if(c)e.className=c;return e;}

function render(items,colId,cmId,cpId,pfx){
  const col=document.getElementById(colId);
  let nm=0,np=0;
  const gr={};
  for(const it of items)(gr[it.folder]||(gr[it.folder]=[])).push(it);
  for(const [folder,fitems] of Object.entries(gr).sort()){
    const fe=mk('div','folder open');
    const le=mk('div','folder-label');
    le.innerHTML='<span class="folder-arrow">&#9654;</span><span style="opacity:.4;margin-right:3px">&#128193;</span>'+folder+'/';
    le.onclick=()=>fe.classList.toggle('open');
    fe.appendChild(le);
    const ce=mk('div','folder-children');
    for(const it of fitems){
      const el=mk('div','item '+(it.missing?'missing':'parent'));
      el.textContent=it.name;
      el.title=it.id+(it.missing?'\n\u26a0 File mancante':'\n\u25cb Presente \u2014 ha dipendenze mancanti');
      const key=pfx+':'+it.id;
      el.dataset.key=key;
      el.addEventListener('click',e=>{e.stopPropagation();handleClick(key);});
      elMap[key]=el;
      ce.appendChild(el);
      it.missing?nm++:np++;
    }
    fe.appendChild(ce);col.appendChild(fe);
  }
  if(!items.length){const e=mk('div','empty');e.textContent='Nessun file';col.appendChild(e);}
  document.getElementById(cmId).textContent=nm?nm+' miss':'';
  document.getElementById(cpId).textContent=np?(nm?' \u00b7 ':'')+np+' par':'';
}

/* ── selezione & frecce ─────────────────────────────── */
function clearAll(){
  for(const el of Object.values(elMap))el.classList.remove('selected','connected');
  document.getElementById('svg-overlay').innerHTML='';
  lastKey=null;
  if(filterActive){filterActive=false;document.getElementById('btn-filter').classList.remove('active');applyFilter();}
}

function handleClick(key){
  if(lastKey===key){clearAll();return;}
  for(const el of Object.values(elMap))el.classList.remove('selected','connected');
  document.getElementById('svg-overlay').innerHTML='';
  lastKey=key;
  const selEl=elMap[key];
  if(selEl)selEl.classList.add('selected');
  const connEls=new Set();
  for(const lk of(DATA.links[key]||[])){
    const le=elMap[lk];
    if(!le)continue;
    le.classList.add('connected');
    for(let p=le.parentElement;p;p=p.parentElement)
      if(p.classList.contains('folder'))p.classList.add('open');
    le.scrollIntoView({block:'nearest'});
    connEls.add(le);
  }
  drawArrows(selEl,connEls);
  if(filterActive)applyFilter();
}

function drawArrows(selEl,connEls){
  const svg=document.getElementById('svg-overlay');
  svg.innerHTML='<defs><marker id="ah" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5" orient="auto"><polygon points="0 0,7 3.5,0 7" fill="#C5B358" fill-opacity=".7"/></marker></defs>';
  if(!selEl)return;
  const sr=selEl.getBoundingClientRect();
  if(!sr.height)return;
  const sy=(sr.top+sr.bottom)/2;
  for(const cel of connEls){
    const cr=cel.getBoundingClientRect();
    if(!cr.height)continue;
    const cy=(cr.top+cr.bottom)/2;
    const goRight=cr.left>sr.right-4;
    const goLeft=cr.right<sr.left+4;
    if(!goRight&&!goLeft)continue;
    const x1=goRight?sr.right:sr.left;
    const x2=goRight?cr.left:cr.right;
    const mx=(x1+x2)/2;
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d',`M${x1},${sy} C${mx},${sy} ${mx},${cy} ${x2},${cy}`);
    path.setAttribute('stroke','#C5B358');
    path.setAttribute('stroke-width','1.2');
    path.setAttribute('stroke-opacity','.55');
    path.setAttribute('fill','none');
    path.setAttribute('marker-end','url(#ah)');
    svg.appendChild(path);
  }
}

function redrawArrows(){
  if(!lastKey)return;
  drawArrows(elMap[lastKey],new Set(document.querySelectorAll('.item.connected')));
}

/* ── ricerca ────────────────────────────────────────── */
function onSearch(val){
  const q=val.toLowerCase();
  for(const colId of['col-tex','col-v2','col-vmd']){
    for(const fe of document.getElementById(colId).querySelectorAll('.folder')){
      let any=false;
      for(const it of fe.querySelectorAll('.item')){
        const m=!q||it.textContent.toLowerCase().includes(q);
        it.style.display=m?'':'none';
        if(m)any=true;
      }
      fe.style.display=any?'':'none';
    }
  }
}

/* ── filtro selezionati ─────────────────────────────── */
function toggleFilter(){
  filterActive=!filterActive;
  document.getElementById('btn-filter').classList.toggle('active',filterActive);
  applyFilter();
}

function applyFilter(){
  for(const el of Object.values(elMap)){
    el.style.display=(!filterActive||el.classList.contains('selected')||el.classList.contains('connected'))?'':'none';
  }
  for(const colId of['col-tex','col-v2','col-vmd']){
    for(const fe of document.getElementById(colId).querySelectorAll('.folder')){
      const any=[...fe.querySelectorAll('.item')].some(it=>it.style.display!=='none');
      fe.style.display=any?'':'none';
    }
  }
}

/* ── scroll / resize ────────────────────────────────── */
['col-tex','col-v2','col-vmd'].forEach(id=>
  document.getElementById(id).addEventListener('scroll',redrawArrows,{passive:true}));
window.addEventListener('resize',redrawArrows);

document.querySelector('.columns').addEventListener('click',e=>{
  if(!e.target.closest('.item'))clearAll();
});

render(DATA.tex,'col-tex','cm-tex','cp-tex','tex');
render(DATA.v2,'col-v2','cm-v2','cp-v2','v2');
render(DATA.vmd,'col-vmd','cm-vmd','cp-vmd','vmd');
</script>
</body>
</html>"""


def generate_missing_html(tex_items, v2_items, vmd_items, links, html_path):
    import datetime
    data = {"tex": tex_items, "v2": v2_items, "vmd": vmd_items, "links": links}
    n_miss = sum(1 for it in tex_items + v2_items + vmd_items if it["missing"])
    n_par  = len(tex_items) + len(v2_items) + len(vmd_items) - n_miss
    html = _HTML_TMPL \
        .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(',', ':'))) \
        .replace("__TS__",   datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    Path(html_path).write_text(html, encoding="utf-8")
    print(f"  ✓  missing-files.html  ({n_miss} mancanti + {n_par} genitori)")


# ── Genera unit-report.html ──────────────────────────────────────

_REPORT_TMPL = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Unit Report</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#111;color:#bbb;font-family:'Consolas','Courier New',monospace;font-size:12px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{padding:7px 14px;background:#1a1a1a;border-bottom:1px solid #C5B358;display:flex;align-items:center;gap:14px;flex-shrink:0}
header h1{font-size:.8rem;letter-spacing:.18em;color:#C5B358;font-weight:normal}
.hint{font-size:.68rem;color:#4a4a4a;flex:1}
.ts{font-size:.65rem;color:#3a5a3a;flex-shrink:0}
.toolbar{padding:5px 14px;background:#161616;border-bottom:1px solid #1e1e1e;display:flex;gap:10px;align-items:center;flex-shrink:0}
#search{flex:1;max-width:320px;background:#0d0d0d;border:1px solid #2a2a2a;color:#bbb;padding:4px 9px;font-family:inherit;font-size:11px;outline:none;border-radius:2px}
#search:focus{border-color:#444}
#search::placeholder{color:#333}
.sort-btn{padding:3px 9px;background:transparent;border:1px solid #2a2a2a;color:#555;cursor:pointer;font-family:inherit;font-size:.7rem;border-radius:2px;transition:all .15s}
.sort-btn:hover,.sort-btn.active{border-color:#C5B358;color:#C5B358}
.summary{font-size:.68rem;color:#444;margin-left:auto}
.wrap{flex:1;overflow:auto}
table{border-collapse:collapse;width:100%;min-width:900px}
thead th{position:sticky;top:0;z-index:10;padding:6px 10px;background:#161616;border-bottom:2px solid #222;font-size:.68rem;letter-spacing:.12em;color:#C5B358;text-transform:uppercase;text-align:left;white-space:nowrap}
tbody tr{border-bottom:1px solid #1a1a1a;transition:background .08s}
tbody tr:hover{background:#161616}
tbody tr.hidden{display:none}
td{padding:6px 10px;vertical-align:top}
td.unit-cell{min-width:180px;max-width:220px}
td.def-cell{min-width:200px;max-width:260px;color:#888;font-size:11px;word-break:break-all}
td.files-cell{min-width:180px;max-width:280px}
.unit-name{color:#ddd;font-weight:bold;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.prog-wrap{height:4px;background:#1e1e1e;border-radius:2px;margin-bottom:3px}
.prog-fill{height:100%;border-radius:2px;transition:width .3s}
.stats{font-size:.68rem}
.error-note{font-size:.68rem;color:#cc4444;margin-top:3px}
.file-list{max-height:120px;overflow-y:auto}
.file-list::-webkit-scrollbar{width:2px}
.file-list::-webkit-scrollbar-thumb{background:#2a2a2a}
.file{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:1px 0;font-size:11px;cursor:default}
.file.ok{color:#4a8a4a}
.file.miss{color:#cc4444}
.empty-cell{color:#2a2a2a;font-style:italic}
</style>
</head>
<body>
<header>
  <h1>&#9776; UNIT REPORT</h1>
  <span class="hint">Completezza file per unità &mdash; da units_report.csv</span>
  <span class="ts">__TS__</span>
</header>
<div class="toolbar">
  <input id="search" type="text" placeholder="Cerca unità…" oninput="onSearch(this.value)">
  <button class="sort-btn" onclick="sortBy('name')">&#8597; Nome</button>
  <button class="sort-btn" onclick="sortBy('pct')">&#8597; %</button>
  <button class="sort-btn" onclick="sortBy('miss')">&#8597; Mancanti</button>
  <span class="summary" id="summary"></span>
</div>
<div class="wrap">
<table>
  <thead>
    <tr>
      <th>Unità</th>
      <th>Variant Definition</th>
      <th>VMDs</th>
      <th>Models (.v2)</th>
      <th>Textures (.dds)</th>
    </tr>
  </thead>
  <tbody id="tbody"></tbody>
</table>
</div>
<script>
'use strict';
const DATA=__DATA__;
let sortKey='name',sortDir=1;

function pctColor(p){return p===100?'#4a8a4a':p>=70?'#C5B358':'#cc4444';}

function fileList(ok,miss){
  if(!ok.length&&!miss.length)return '<span class="empty-cell">\u2014</span>';
  return '<div class="file-list">'
    +ok.map(f=>`<div class="file ok" title="${f}">\u2713 ${f.split('/').pop()}</div>`).join('')
    +miss.map(f=>`<div class="file miss" title="${f}">\u2717 ${f.split('/').pop()}</div>`).join('')
    +'</div>';
}

function buildRow(u){
  const tr=document.createElement('tr');
  tr.dataset.name=u.name.toLowerCase();
  tr.dataset.pct=u.error?-1:u.pct;
  tr.dataset.miss=u.error?9999:(u.miss_vmds.length+u.miss_v2s.length+u.miss_texs.length+u.miss_other.length);
  if(u.error){
    tr.innerHTML=`<td class="unit-cell"><div class="unit-name">${u.name}</div><div class="error-note">\u26a0 Non trovata</div></td>`
      +`<td class="def-cell">${u.variant_file}</td><td colspan="3" class="empty-cell" style="padding:8px 10px">Unità non trovata in vmd-viewer.txt — rigenerare con vmd-generate.py</td>`;
  } else {
    const c=pctColor(u.pct);
    tr.innerHTML=`<td class="unit-cell">`
      +`<div class="unit-name" title="${u.name}">${u.name}</div>`
      +`<div class="prog-wrap"><div class="prog-fill" style="width:${u.pct}%;background:${c}"></div></div>`
      +`<div class="stats" style="color:${c}">${u.present}/${u.total} &nbsp;(${u.pct}%)</div>`
      +`</td>`
      +`<td class="def-cell" title="${u.variant_file}">${u.variant_file}</td>`
      +`<td class="files-cell">${fileList(u.vmds_ok,u.miss_vmds)}</td>`
      +`<td class="files-cell">${fileList(u.v2s_ok,u.miss_v2s)}</td>`
      +`<td class="files-cell">${fileList(u.texs_ok,u.miss_texs)}</td>`;
  }
  return tr;
}

function render(){
  const tbody=document.getElementById('tbody');
  tbody.innerHTML='';
  const sorted=[...DATA].sort((a,b)=>{
    let va,vb;
    if(sortKey==='name'){va=a.name.toLowerCase();vb=b.name.toLowerCase();return va<vb?-sortDir:va>vb?sortDir:0;}
    if(sortKey==='pct'){va=a.error?-1:a.pct;vb=b.error?-1:b.pct;return (va-vb)*sortDir;}
    if(sortKey==='miss'){
      va=a.error?9999:(a.miss_vmds.length+a.miss_v2s.length+a.miss_texs.length+(a.miss_other||[]).length);
      vb=b.error?9999:(b.miss_vmds.length+b.miss_v2s.length+b.miss_texs.length+(b.miss_other||[]).length);
      return (va-vb)*sortDir;
    }
    return 0;
  });
  sorted.forEach(u=>tbody.appendChild(buildRow(u)));
  updateSummary();
}

function sortBy(k){
  if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=k==='name'?1:-1;}
  document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('active'));
  render();
}

function onSearch(val){
  const q=val.toLowerCase();
  for(const tr of document.getElementById('tbody').rows)
    tr.classList.toggle('hidden',!!q&&!tr.dataset.name.includes(q));
  updateSummary();
}

function updateSummary(){
  const rows=[...document.getElementById('tbody').rows].filter(r=>!r.classList.contains('hidden'));
  const tot=rows.length;
  const complete=rows.filter(r=>r.dataset.pct==='100').length;
  document.getElementById('summary').textContent=`${tot} unità \u2022 ${complete} complete`;
}

render();
</script>
</body>
</html>"""


def parse_csv(path):
    """Legge units_report.csv → [(display_name, variant_stem), ...]"""
    import csv as _csv
    result = []
    p = Path(path)
    if not p.exists():
        print(f"  ─  {path} non trovato — salto unit-report")
        return result
    with open(p, encoding="utf-8-sig", errors="replace") as f:
        for row in _csv.reader(f):
            row = [c.strip() for c in row]
            if len(row) >= 2 and row[0] and not row[0].startswith("#"):
                stem = Path(row[1]).stem.lower()
                result.append((row[0], stem))
    return result


def generate_unit_report(csv_rows, variant_by_id, center_by_id,
                         model_by_name, tex_by_name, model_to_textures,
                         added_set, html_path):
    import datetime
    units = []
    for unit_name, variant_stem in csv_rows:
        result = collect(variant_stem, variant_by_id, center_by_id,
                         model_by_name, tex_by_name, model_to_textures)
        if result is None:
            units.append({"name": unit_name,
                          "variant_file": variant_stem + ".variantmeshdefinition",
                          "error": True,
                          "present": 0, "total": 0, "pct": 0,
                          "vmds_ok": [], "v2s_ok": [], "texs_ok": [],
                          "miss_vmds": [], "miss_v2s": [], "miss_texs": [], "miss_other": []})
            continue

        vmds, v2s, texs, missing = result
        variant = variant_by_id.get(variant_stem)
        variant_file = variant["file"] if variant else (variant_stem + ".variantmeshdefinition")

        def split(files):
            ok   = sorted(f for f in files if norm_path(f) in added_set)
            todo = sorted(f for f in files if norm_path(f) not in added_set)
            return ok, todo

        def by_ext(ext):
            return sorted(f for f in missing if f.lower().endswith(ext))

        vmds_ok, vmds_todo = split(vmds)
        v2s_ok,  v2s_todo  = split(v2s)
        texs_ok, texs_todo = split(texs)

        _MODEL_EXTS = (".variantmesh", ".rigid_model_v2")
        miss_vmds  = vmds_todo + by_ext(".variantmeshdefinition")
        miss_v2s   = v2s_todo  + by_ext(".variantmesh") + by_ext(".rigid_model_v2")
        miss_texs  = texs_todo + by_ext(".dds")
        miss_other = sorted(f for f in missing
                            if not any(f.lower().endswith(e)
                                       for e in (".variantmeshdefinition", ".variantmesh",
                                                 ".rigid_model_v2", ".dds")))

        present = len(vmds_ok) + len(v2s_ok) + len(texs_ok)
        total   = len(vmds) + len(v2s) + len(texs) + len(missing)
        pct     = round(present / total * 100) if total else 100

        units.append({
            "name": unit_name, "variant_file": variant_file, "error": False,
            "present": present, "total": total, "pct": pct,
            "vmds_ok": vmds_ok, "v2s_ok": v2s_ok, "texs_ok": texs_ok,
            "miss_vmds": miss_vmds, "miss_v2s": miss_v2s,
            "miss_texs": miss_texs, "miss_other": miss_other,
        })

    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    html = _REPORT_TMPL \
        .replace("__DATA__", json.dumps(units, ensure_ascii=False, separators=(',', ':'))) \
        .replace("__TS__", ts)
    Path(html_path).write_text(html, encoding="utf-8")
    n_ok = sum(1 for u in units if not u["error"] and u["pct"] == 100)
    print(f"  ✓  unit-report.html  ({len(units)} unità, {n_ok} complete)")


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("\n── Lettura vmd-viewer.txt ─────────────────")
    tex_by_name, model_by_name, center_by_id, variant_by_id = parse_txt(TXT_FILE)
    print(f"  ✓  Textures   : {len(tex_by_name)}")
    print(f"  ✓  Modelli    : {len(model_by_name)}")
    print(f"  ✓  VMD centro : {len(center_by_id)}")
    print(f"  ✓  Varianti   : {len(variant_by_id)}")

    model_to_textures = load_model_to_textures(HTML_FILE)
    if not model_to_textures:
        model_to_textures = build_model_to_textures_by_name(model_by_name, tex_by_name)
        print(f"  ✓  Model→Tex  : {len(model_to_textures)} entries (naming convention)")
    else:
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
    all_miss_lines = read_lines(MISSING_FILE)
    tex_it, v2_it, vmd_it, links = build_relations(
        all_miss_lines, model_to_textures, model_by_name, center_by_id)
    generate_missing_html(tex_it, v2_it, vmd_it, links, MISSING_HTML)

    # ── 6. Genera unit-report.html ──────────────────────────────────
    csv_rows = parse_csv(CSV_FILE)
    if csv_rows:
        generate_unit_report(csv_rows, variant_by_id, center_by_id,
                             model_by_name, tex_by_name, model_to_textures,
                             load_added(ADDED_FILE), UNIT_REPORT)


if __name__ == "__main__":
    main()
