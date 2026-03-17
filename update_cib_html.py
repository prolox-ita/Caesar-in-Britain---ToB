#!/usr/bin/env python3
"""
Aggiorna cib.html con i nuovi dati estratti dalla lookup map
e sostituisce l'immagine con la versione scalata.
"""

import json
import re

# Leggi cib_data.js
with open('cib_data.js', 'r', encoding='utf-8') as f:
    content = f.read()
    # Estrai il JSON dopo "const CIB_REGIONS = "
    json_str = content.split('const CIB_REGIONS = ')[1].rstrip(';\n')
    cib_regions = json.loads(json_str)

print(f"Caricati {len(cib_regions)} regioni da cib_data.js")

# Leggi cib.html
with open('cib.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Estrai l'array regions dal JavaScript
# Trova l'inizio dell'array regions
match = re.search(r'const regions = \[(.*?)\];', html_content, re.DOTALL)
if not match:
    print("❌ Non trovato array regions in cib.html")
    exit(1)

regions_str = match.group(1)
print("✓ Array regions trovato")

# Ora costruiamo il nuovo array regions combinando i dati esistenti con quelli nuovi
# Per ogni regione in cib_data.js, creiamo un nuovo oggetto region

new_regions = []

for region_key, region_data in cib_regions.items():
    # Converti bounds in formato SVG polygon string
    # bounds è un array di [x, y]
    if not region_data.get('bounds'):
        continue

    polygon_points = ' '.join([f"{pt[0]},{pt[1]}" for pt in region_data['bounds']])

    # Cerca se esiste già una regione con questo regionKey nell'HTML
    # e preleva il nome se esiste
    name_match = re.search(
        rf'name:\s*"([^"]*)",\s*regionKey:\s*"{region_key}"',
        regions_str
    )

    if name_match:
        region_name = name_match.group(1)
    else:
        # Usa regionKey come nome se non trovato
        region_name = region_key.replace('vik_reg_', '').replace('cib_reg_', '').replace('_', ' ').title()

    new_region = {
        'name': region_name,
        'regionKey': region_key,
        'color': region_data['color'],
        'sea': region_data['isSea'],
        'owner': None,
        'factionColor': None,
        'port': None,
        'numberOfSlots': None,
        'rebelFaction': None,
        'alternativeRebelFaction': None,
        'religion': None,
        'isCapital': None,
        'polygons': [polygon_points]
    }

    new_regions.append(new_region)

print(f"✓ Creati {len(new_regions)} oggetti region")

# Converte new_regions in stringa JavaScript
regions_js = "const regions = [\n"
for i, region in enumerate(new_regions):
    regions_js += "    {\n"
    regions_js += f"        name: \"{region['name']}\",\n"
    regions_js += f"        regionKey: \"{region['regionKey']}\",\n"
    regions_js += f"        color: \"{region['color']}\",\n"
    regions_js += f"        sea: {str(region['sea']).lower()},\n"
    regions_js += f"        owner: {region['owner']},\n"
    regions_js += f"        factionColor: {region['factionColor']},\n"
    regions_js += f"        port: {region['port']},\n"
    regions_js += f"        numberOfSlots: {region['numberOfSlots']},\n"
    regions_js += f"        rebelFaction: {region['rebelFaction']},\n"
    regions_js += f"        alternativeRebelFaction: {region['alternativeRebelFaction']},\n"
    regions_js += f"        religion: {region['religion']},\n"
    regions_js += f"        isCapital: {region['isCapital']},\n"
    regions_js += f"        polygons: [\n"
    regions_js += f"            \"{region['polygons'][0]}\",\n"
    regions_js += f"        ]\n"
    regions_js += "    }"
    if i < len(new_regions) - 1:
        regions_js += ","
    regions_js += "\n"

regions_js += "];"

# Sostituisci l'array regions nell'HTML
new_html = re.sub(
    r'const regions = \[.*?\];',
    regions_js,
    html_content,
    flags=re.DOTALL
)

# Sostituisci il riferimento all'immagine
new_html = new_html.replace(
    'src="background_cib.jpg"',
    'src="background_cib_scaled.jpg"'
)

# Salva il nuovo HTML
with open('cib_updated.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("\n✅ File aggiornato salvato come: cib_updated.html")
print(f"📊 {len(new_regions)} regioni con coordinate precise")
print(f"🖼️  Immagine: background_cib_scaled.jpg (954×1063)")
