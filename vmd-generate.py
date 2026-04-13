#!/usr/bin/env python3
"""
VMD Viewer Generator
────────────────────
1. Modifica la sezione CONFIGURAZIONE con i tuoi percorsi
2. Esegui: python vmd-generate.py
3. Apri il file generato: vmd-viewer.html
"""

import json
from pathlib import Path
import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════════
#  CONFIGURAZIONE — modifica questi percorsi
# ═══════════════════════════════════════════════════════════════
CONFIG = {

    # Una o più cartelle che contengono i .rigid_model_v2.
    # Vengono scansionate ricorsivamente.
     "models_roots": [
        r"D:\Thrones of Britannia\modding\variantmeshes",
    ],

    # Cartella dei VMD centrali (.variantmeshdefinition delle unità).
    # Scansionata ricorsivamente.
    "vmds_root": r"D:\Thrones of Britannia\modding\variantmeshes",

    # Cartella delle varianti destra (una sola cartella specifica).
    "variants_root": r"D:\Thrones of Britannia\modding\VariantMeshDefinitions",

    # File HTML da generare
    "output": r"C:\Users\loren\Desktop\MK1212-website\vmd-viewer.html",
}
# ═══════════════════════════════════════════════════════════════


def scan_models(roots):
    tree = {}
    for root_str in roots:
        root_path = Path(root_str)
        if not root_path.exists():
            print(f"  ⚠  Non trovata: {root_str}")
            continue
        for f in sorted(root_path.rglob("*.rigid_model_v2")):
            rel = f.parent.relative_to(root_path)
            key = str(rel).replace("\\", "/") if str(rel) != "." else root_path.name
            tree.setdefault(key, []).append(f.name)
    return tree


def parse_vmd(filepath):
    refs_mesh, refs_vmd = [], []
    try:
        for elem in ET.parse(filepath).getroot().iter():
            for val in elem.attrib.values():
                lo = val.lower()
                if lo.endswith(".rigid_model_v2") or lo.endswith(".variantmesh"):
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
    models_tree = scan_models(CONFIG["models_roots"])
    center_vmds = scan_center_vmds(CONFIG["vmds_root"])
    right_vmds  = scan_right_vmds(CONFIG["variants_root"])

    # Mappa nome_file (lowercase) → path scansionato completo
    # Es. "fp_dc_leather_skullcap.rigid_model_v2" → "characters/heads/fp_dc_leather_skullcap.rigid_model_v2"
    model_by_name = {}
    for folder, files in models_tree.items():
        for f in files:
            model_by_name[f.lower()] = f"{folder}/{f}"

    # Risolvi i model refs dei VMD centrali usando il nome file come chiave
    unresolved_models = 0
    for vmd in center_vmds:
        resolved, missing = [], []
        for ref in vmd["models"]:
            name = Path(ref).name.lower()
            if name in model_by_name:
                resolved.append(model_by_name[name])
            else:
                missing.append(ref)
                unresolved_models += 1
        vmd["models"]         = resolved
        vmd["missing_models"] = missing

    if unresolved_models:
        print(f"  ⚠  Model ref non risolti : {unresolved_models} (file non trovati nella cartella models)")

    by_file = {v["file"]: v for v in center_vmds}
    by_stem = {v["id"]:   v for v in center_vmds}

    unresolved_vmds = 0
    for variant in right_vmds:
        missing_vmds = []
        for ref in variant["_raw_refs"]:
            matched = by_file.get(Path(ref).name) or by_stem.get(Path(ref).stem)
            if matched:
                variant["vmds"].append(matched["id"])
                if variant["id"] not in matched["in_variants"]:
                    matched["in_variants"].append(variant["id"])
            else:
                missing_vmds.append(ref)
                unresolved_vmds += 1
        variant["missing_vmds"] = missing_vmds
        del variant["_raw_refs"]

    if unresolved_vmds:
        print(f"  ⚠  VMD ref non risolti   : {unresolved_vmds} (vmd non trovati nella cartella center)")

    total_models = sum(len(v) for v in models_tree.values())
    print(f"  ✓  Model files   : {total_models}")
    print(f"  ✓  VMD centrali  : {len(center_vmds)}")
    print(f"  ✓  Varianti      : {len(right_vmds)}")
    print("───────────────────────────────────────────\n")

    return models_tree, center_vmds, right_vmds


def generate_html(models_tree, center_vmds, right_vmds):
    data_js = (
        f"const MODELS_TREE = {json.dumps(models_tree, ensure_ascii=False, indent=2)};\n\n"
        f"const CENTER_VMDS = {json.dumps(center_vmds, ensure_ascii=False, indent=2)};\n\n"
        f"const RIGHT_VMDS  = {json.dumps(right_vmds,  ensure_ascii=False, indent=2)};"
    )

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VMD Viewer</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            background: #111; color: #bbb;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px; height: 100vh;
            display: flex; flex-direction: column; overflow: hidden;
        }}

        header {{
            padding: 7px 14px; background: #1a1a1a;
            border-bottom: 1px solid #C5B358;
            display: flex; align-items: center; gap: 14px; flex-shrink: 0;
        }}
        header h1 {{ font-size: 0.8rem; letter-spacing: 0.18em; color: #C5B358; font-weight: normal; }}
        .hint {{ font-size: 0.68rem; color: #4a4a4a; flex: 1; }}
        .col-count {{ color: #444; font-size: 0.6rem; }}

        .columns {{ display: flex; flex: 1; overflow: hidden; }}
        .col {{
            flex: 1; display: flex; flex-direction: column;
            border-right: 1px solid #222; min-width: 0;
        }}
        .col:last-child {{ border-right: none; }}

        .col-head {{ padding: 7px 12px; background: #161616; border-bottom: 1px solid #222; flex-shrink: 0; }}
        .col-head-title {{ font-size: 0.68rem; letter-spacing: 0.14em; color: #C5B358; text-transform: uppercase; }}
        .col-head-sub {{ font-size: 0.6rem; color: #444; margin-top: 2px; }}
        .cnt {{ float: right; color: #333; font-size: 0.6rem; margin-top: 1px; }}

        .col-body {{ flex: 1; overflow-y: auto; padding: 3px 0; }}
        .col-body::-webkit-scrollbar {{ width: 3px; }}
        .col-body::-webkit-scrollbar-track {{ background: #111; }}
        .col-body::-webkit-scrollbar-thumb {{ background: #2a2a2a; border-radius: 2px; }}

        .folder {{ user-select: none; }}
        .folder-label {{
            display: flex; align-items: center; gap: 5px;
            padding: 3px 10px; cursor: pointer; color: #666; white-space: nowrap;
        }}
        .folder-label:hover {{ background: rgba(255,255,255,0.03); }}
        .folder-arrow {{ font-size: 8px; color: #444; transition: transform 0.12s; flex-shrink: 0; width: 10px; }}
        .folder.open > .folder-label > .folder-arrow {{ transform: rotate(90deg); }}
        .folder-children {{ display: none; }}
        .folder.open > .folder-children {{ display: block; }}

        .item {{
            padding: 3px 10px; cursor: pointer;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            color: #999; border-left: 2px solid transparent; transition: background 0.08s;
        }}
        .item:hover {{ background: rgba(255,255,255,0.04); }}
        .item.unused {{ color: #555; }}
        .item.unused::after {{ content: ' ⊘'; color: #333; font-size: 10px; }}
        .item.broken::after {{ content: ' ⚠'; color: #a05000; font-size: 10px; }}
        .item.unused.broken::after {{ content: ' ⊘ ⚠'; color: #a05000; font-size: 10px; }}
        .item.selected {{ color: #fff; background: rgba(139,0,0,0.22); border-left-color: #8B0000; }}
        .item.selected.unused::after {{ color: rgba(255,255,255,0.2); }}
        .item.selected.broken::after {{ color: #d07020; }}
        .item.connected {{ color: #F5E6BE; background: rgba(197,179,88,0.1); border-left-color: #C5B358; }}

        /* ── Filtri ───────────────────────────────────────────── */
        .hidden-filter {{ display: none !important; }}

        #search {{
            padding: 4px 8px;
            background: #111;
            border: 1px solid #2a2a2a;
            color: #bbb;
            font-family: inherit;
            font-size: 0.72rem;
            width: 200px;
            outline: none;
            transition: border-color 0.15s;
        }}
        #search:focus {{ border-color: #C5B358; }}
        #search::placeholder {{ color: #3a3a3a; }}

        #btn-unused {{
            padding: 4px 10px;
            background: transparent;
            border: 1px solid #2a2a2a;
            color: #555;
            cursor: pointer;
            font-size: 0.68rem;
            font-family: inherit;
            white-space: nowrap;
            transition: all 0.15s;
        }}
        #btn-unused:hover {{ border-color: #555; color: #888; }}
        #btn-unused.active {{
            border-color: #C5B358;
            color: #C5B358;
            background: rgba(197,179,88,0.07);
        }}

        #btn-download {{
            padding: 4px 10px;
            background: transparent;
            border: 1px solid #2a2a2a;
            color: #555;
            cursor: pointer;
            font-size: 0.68rem;
            font-family: inherit;
            white-space: nowrap;
            transition: all 0.15s;
        }}
        #btn-download:hover {{ border-color: #555; color: #888; }}

        #svg-overlay {{
            position: fixed; top: 0; left: 0;
            width: 100vw; height: 100vh;
            pointer-events: none; z-index: 9999;
        }}
    </style>
</head>
<body>

<header>
    <h1>&#9876; VMD VIEWER</h1>
    <span class="hint">
        Click: seleziona &nbsp;·&nbsp; Ctrl+Click: aggiungi/rimuovi &nbsp;·&nbsp;
        Shift+Click: seleziona intervallo &nbsp;·&nbsp; &#8853; = non utilizzato
    </span>
    <input id="search" type="text" placeholder="Cerca…" oninput="applyFilters()">
    <button id="btn-unused" onclick="toggleUnused()">&#8853; Solo non assegnati</button>
    <button id="btn-download" onclick="downloadData()">&#8595; Scarica JSON</button>
</header>

<div class="columns">
    <div class="col">
        <div class="col-head">
            <span class="cnt" id="c-models"></span>
            <div class="col-head-title">Models</div>
            <div class="col-head-sub">.variantmesh</div>
        </div>
        <div class="col-body" id="col-models"></div>
    </div>
    <div class="col">
        <div class="col-head">
            <span class="cnt" id="c-vmds"></span>
            <div class="col-head-title">Definitions</div>
            <div class="col-head-sub">.variantmeshdefinition</div>
        </div>
        <div class="col-body" id="col-vmds"></div>
    </div>
    <div class="col">
        <div class="col-head">
            <span class="cnt" id="c-variants"></span>
            <div class="col-head-title">Variants</div>
            <div class="col-head-sub">.variantmeshdefinition</div>
        </div>
        <div class="col-body" id="col-variants"></div>
    </div>
</div>

<svg id="svg-overlay"></svg>

<script>
'use strict';

// ── Dati generati automaticamente ──────────────────────────────
{data_js}

// ── Pre-calcolo unused ─────────────────────────────────────────
const usedModelPaths = new Set(CENTER_VMDS.flatMap(v => v.models));
const usedVmdIds     = new Set(RIGHT_VMDS.flatMap(v => v.vmds));

// ── Mappe e liste per colonna ──────────────────────────────────
const modelMap   = new Map();
const vmdMap     = new Map();
const variantMap = new Map();
const colItems   = {{'col-models': [], 'col-vmds': [], 'col-variants': []}};

// ── Tree builder ───────────────────────────────────────────────
function buildTree(flat) {{
    const root = {{}};
    for (const [path, files] of Object.entries(flat)) {{
        const parts = path.split('/');
        let node = root;
        for (const p of parts) {{
            if (!node[p]) node[p] = {{files: [], sub: {{}}}};
            node = node[p].sub;
        }}
        let cur = root;
        for (let i = 0; i < parts.length; i++) {{
            if (i === parts.length - 1) cur[parts[i]].files = files;
            else cur = cur[parts[i]].sub;
        }}
    }}
    return root;
}}

function renderTree(node, parent, depth, pathSoFar) {{
    for (const [name, data] of Object.entries(node)) {{
        const fullPath = pathSoFar ? `${{pathSoFar}}/${{name}}` : name;
        const pf = 8 + depth * 14, pi = pf + 18;
        const fe = mk('div','folder open');
        const le = mk('div','folder-label');
        le.style.paddingLeft = pf + 'px';
        le.innerHTML = `<span class="folder-arrow">&#9654;</span><span style="opacity:.4;margin-right:3px">&#128193;</span>${{name}}/`;
        le.onclick = () => fe.classList.toggle('open');
        fe.appendChild(le);
        const ce = mk('div','folder-children');
        if (Object.keys(data.sub).length) renderTree(data.sub, ce, depth+1, fullPath);
        for (const file of data.files) {{
            const mp = `${{fullPath}}/${{file}}`;
            const unused = !usedModelPaths.has(mp);
            const el = mk('div','item'+(unused?' unused':''));
            el.style.paddingLeft = pi+'px';
            el.textContent = file;
            el.title = mp + (unused ? '\\n⊘ Non usato da nessun VMD' : '');
            el.dataset.mp  = mp;
            el.dataset.col = 'col-models';
            el.addEventListener('click', e => {{ e.stopPropagation(); handleClick(el,e); }});
            ce.appendChild(el);
            modelMap.set(mp, el);
            colItems['col-models'].push(el);
        }}
        fe.appendChild(ce);
        parent.appendChild(fe);
    }}
}}

function renderCenterVmds() {{
    const body = document.getElementById('col-vmds');
    const byFolder = {{}};
    for (const v of CENTER_VMDS) (byFolder[v.folder] ??= []).push(v);
    for (const [folder, vmds] of Object.entries(byFolder)) {{
        const fe = mk('div','folder open');
        const le = mk('div','folder-label');
        le.style.paddingLeft = '8px';
        le.innerHTML = `<span class="folder-arrow">&#9654;</span><span style="opacity:.4;margin-right:3px">&#128193;</span>${{folder}}/`;
        le.onclick = () => fe.classList.toggle('open');
        fe.appendChild(le);
        const ce = mk('div','folder-children');
        for (const vmd of vmds) {{
            const unused = !usedVmdIds.has(vmd.id);
            const broken = vmd.missing_models && vmd.missing_models.length > 0;
            let cls = 'item';
            if (unused) cls += ' unused';
            if (broken) cls += ' broken';
            const el = mk('div', cls);
            el.style.paddingLeft = '26px';
            el.textContent = vmd.file;
            let tip = `${{vmd.folder}}/${{vmd.file}}`;
            if (unused) tip += '\\n⊘ Non in nessuna variante';
            if (broken) tip += `\\n⚠ Ref. non trovati (${{vmd.missing_models.length}}):\\n` + vmd.missing_models.join('\\n');
            el.title = tip;
            el.dataset.vmdId = vmd.id;
            el.dataset.col   = 'col-vmds';
            el.addEventListener('click', e => {{ e.stopPropagation(); handleClick(el,e); }});
            ce.appendChild(el);
            vmdMap.set(vmd.id, el);
            colItems['col-vmds'].push(el);
        }}
        fe.appendChild(ce);
        body.appendChild(fe);
    }}
}}

function renderRightVmds() {{
    const body = document.getElementById('col-variants');
    for (const v of RIGHT_VMDS) {{
        const broken = v.missing_vmds && v.missing_vmds.length > 0;
        const el = mk('div', 'item' + (broken ? ' broken' : ''));
        el.style.paddingLeft = '12px';
        el.textContent = v.file;
        let tip = v.file;
        if (broken) tip += `\\n⚠ VMD ref. non trovati (${{v.missing_vmds.length}}):\\n` + v.missing_vmds.join('\\n');
        el.title = tip;
        el.dataset.variantId = v.id;
        el.dataset.col = 'col-variants';
        el.addEventListener('click', e => {{ e.stopPropagation(); handleClick(el,e); }});
        body.appendChild(el);
        variantMap.set(v.id, el);
        colItems['col-variants'].push(el);
    }}
}}

// ── Connessioni ────────────────────────────────────────────────
function getConnectionEls(el) {{
    const r = [];
    if (el.dataset.mp) {{
        CENTER_VMDS.filter(v => v.models.includes(el.dataset.mp))
            .forEach(v => {{ const e = vmdMap.get(v.id); if (e) r.push(e); }});
    }} else if (el.dataset.vmdId) {{
        const vmd = CENTER_VMDS.find(v => v.id === el.dataset.vmdId);
        if (vmd) {{
            vmd.models.forEach(mp => {{ const e = modelMap.get(mp); if (e) r.push(e); }});
            vmd.in_variants.forEach(id => {{ const e = variantMap.get(id); if (e) r.push(e); }});
        }}
    }} else if (el.dataset.variantId) {{
        const v = RIGHT_VMDS.find(v => v.id === el.dataset.variantId);
        if (v) v.vmds.forEach(id => {{ const e = vmdMap.get(id); if (e) r.push(e); }});
    }}
    return r;
}}

// ── Selezione ──────────────────────────────────────────────────
const selectedEls      = new Set();
const lastClickedInCol = new Map();

function handleClick(el, e) {{
    const col = el.dataset.col;
    if (e.shiftKey) {{
        const last = lastClickedInCol.get(col);
        if (last && last !== el) {{
            const vis = colItems[col].filter(i => i.getBoundingClientRect().height > 0);
            const i1 = vis.indexOf(last), i2 = vis.indexOf(el);
            if (i1 !== -1 && i2 !== -1)
                for (let i = Math.min(i1,i2); i <= Math.max(i1,i2); i++) selectedEls.add(vis[i]);
            else selectedEls.add(el);
        }} else {{ selectedEls.add(el); lastClickedInCol.set(col, el); }}
    }} else if (e.ctrlKey || e.metaKey) {{
        if (selectedEls.has(el)) selectedEls.delete(el); else selectedEls.add(el);
        lastClickedInCol.set(col, el);
    }} else {{
        if (selectedEls.size === 1 && selectedEls.has(el)) selectedEls.clear();
        else {{ selectedEls.clear(); selectedEls.add(el); }}
        lastClickedInCol.set(col, el);
    }}
    applySelection();
}}

function applySelection() {{
    document.querySelectorAll('.item.selected,.item.connected')
        .forEach(el => el.classList.remove('selected','connected'));
    document.getElementById('svg-overlay').innerHTML = '';
    if (!selectedEls.size) return;
    const conn = new Set();
    for (const sel of selectedEls) {{
        sel.classList.add('selected');
        getConnectionEls(sel).forEach(c => {{ if (!selectedEls.has(c)) conn.add(c); }});
    }}
    for (const el of conn) {{
        el.classList.add('connected');
        for (let p = el.parentElement; p; p = p.parentElement)
            if (p.classList.contains('folder')) p.classList.add('open');
        el.scrollIntoView({{block:'nearest'}});
    }}
    drawArrows(conn);
}}

// ── Frecce SVG ─────────────────────────────────────────────────
function drawArrows(conn) {{
    const svg = document.getElementById('svg-overlay');
    svg.innerHTML = `<defs><marker id="ah" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5" orient="auto"><polygon points="0 0,7 3.5,0 7" fill="#C5B358" fill-opacity=".7"/></marker></defs>`;
    for (const sel of selectedEls) {{
        const sr = sel.getBoundingClientRect();
        if (!sr.height) continue;
        const sy = (sr.top + sr.bottom) / 2;
        for (const cel of getConnectionEls(sel).filter(e => conn.has(e))) {{
            const cr = cel.getBoundingClientRect();
            if (!cr.height) continue;
            const cy = (cr.top + cr.bottom) / 2;
            const toR = cr.left > sr.right - 4, toL = cr.right < sr.left + 4;
            if (!toR && !toL) continue;
            const x1 = toR ? sr.right : sr.left, x2 = toR ? cr.left : cr.right;
            const mx = (x1 + x2) / 2;
            const path = document.createElementNS('http://www.w3.org/2000/svg','path');
            path.setAttribute('d', `M${{x1}},${{sy}} C${{mx}},${{sy}} ${{mx}},${{cy}} ${{x2}},${{cy}}`);
            path.setAttribute('stroke','#C5B358');
            path.setAttribute('stroke-width','1.2');
            path.setAttribute('stroke-opacity','.5');
            path.setAttribute('fill','none');
            path.setAttribute('marker-end','url(#ah)');
            svg.appendChild(path);
        }}
    }}
}}

function redraw() {{
    if (selectedEls.size) drawArrows(new Set(document.querySelectorAll('.item.connected')));
}}
['col-models','col-vmds','col-variants'].forEach(id =>
    document.getElementById(id).addEventListener('scroll', redraw, {{passive:true}}));
window.addEventListener('resize', redraw);
document.querySelector('.columns').addEventListener('click', e => {{
    if (!e.target.closest('.item')) {{
        selectedEls.clear(); lastClickedInCol.clear(); applySelection();
    }}
}});

// ── Filtri ─────────────────────────────────────────────────────
let onlyUnused = false;

function toggleUnused() {{
    onlyUnused = !onlyUnused;
    document.getElementById('btn-unused').classList.toggle('active', onlyUnused);
    applyFilters();
}}

function applyFilters() {{
    const query = document.getElementById('search').value.toLowerCase().trim();
    for (const col of ['col-models','col-vmds','col-variants']) {{
        for (const item of colItems[col]) {{
            const matchSearch = !query || item.textContent.toLowerCase().includes(query);
            const matchUnused = !onlyUnused || item.classList.contains('unused');
            item.classList.toggle('hidden-filter', !(matchSearch && matchUnused));
        }}
        updateFolderVisibility(document.getElementById(col));
    }}
}}

function updateFolderVisibility(container) {{
    for (const folder of [...container.querySelectorAll('.folder')].reverse()) {{
        const hasVisible = [...folder.querySelectorAll('.item')].some(i => !i.classList.contains('hidden-filter'));
        folder.classList.toggle('hidden-filter', !hasVisible);
        if (document.getElementById('search').value.trim() && hasVisible) folder.classList.add('open');
    }}
}}

function downloadData() {{
    const isFiltered = onlyUnused || document.getElementById('search').value.trim();

    const visibleModels = colItems['col-models']
        .filter(i => !i.classList.contains('hidden-filter'))
        .map(i => i.dataset.mp);

    const visibleVmdIds = new Set(
        colItems['col-vmds']
            .filter(i => !i.classList.contains('hidden-filter'))
            .map(i => i.dataset.vmdId)
    );

    const visibleVariantIds = new Set(
        colItems['col-variants']
            .filter(i => !i.classList.contains('hidden-filter'))
            .map(i => i.dataset.variantId)
    );

    const out = {{
        generated: new Date().toISOString(),
        filters: {{
            search: document.getElementById('search').value.trim() || null,
            onlyUnused: onlyUnused,
        }},
        models: visibleModels,
        vmds: CENTER_VMDS
            .filter(v => visibleVmdIds.has(v.id))
            .map(v => ({{ id: v.id, folder: v.folder, file: v.file, models: v.models, in_variants: v.in_variants }})),
        variants: RIGHT_VMDS
            .filter(v => visibleVariantIds.has(v.id))
            .map(v => ({{ id: v.id, file: v.file, vmds: v.vmds }})),
    }};

    const blob = new Blob([JSON.stringify(out, null, 2)], {{type: 'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = isFiltered ? 'vmd-export-filtered.json' : 'vmd-export.json';
    a.click();
    URL.revokeObjectURL(a.href);
}}

// ── Utils & Init ───────────────────────────────────────────────
function mk(tag, cls) {{
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    return el;
}}

renderTree(buildTree(MODELS_TREE), document.getElementById('col-models'), 0, '');
renderCenterVmds();
renderRightVmds();

const totalModels = Object.values(MODELS_TREE).reduce((s,a) => s+a.length, 0);
document.getElementById('c-models').textContent   = totalModels + ' models';
document.getElementById('c-vmds').textContent     = CENTER_VMDS.length + ' vmds';
document.getElementById('c-variants').textContent = RIGHT_VMDS.length + ' variants';
</script>
</body>
</html>"""


if __name__ == "__main__":
    models_tree, center_vmds, right_vmds = build_data()
    html = generate_html(models_tree, center_vmds, right_vmds)

    out = Path(CONFIG.get("output", "vmd-viewer.html"))
    out.write_text(html, encoding="utf-8")
    print(f"  ✓  Generato: {out.resolve()}")
    print(f"     Aprilo nel browser con doppio click.\n")
