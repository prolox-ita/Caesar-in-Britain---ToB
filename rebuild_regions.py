#!/usr/bin/env python3
"""
Ricostruisce il file regions_data.js partendo da regioni_mappa.json
e scalando le coordinate da 2400x1702 a 4800x3404.
"""

import json
import re

# Dimensioni originali e target
ORIGINAL_WIDTH = 2400
ORIGINAL_HEIGHT = 1702
TARGET_WIDTH = 4800
TARGET_HEIGHT = 3404

# Fattore di scala
SCALE_X = TARGET_WIDTH / ORIGINAL_WIDTH
SCALE_Y = TARGET_HEIGHT / ORIGINAL_HEIGHT

def load_region_metadata():
    """Carica i metadati delle regioni dal file regions_data.js esistente."""
    metadata = {}

    try:
        with open('regions_data.js', 'r', encoding='utf-8') as f:
            content = f.read()

        # Estrai tutti i blocchi di regioni usando regex
        # Cerca pattern come: name: "Erzurum", ... color: "#000030"
        pattern = r'\{\s*name:\s*"([^"]+)"[^}]*?color:\s*"([^"]+)"[^}]*?(?:sea:\s*(true|false))[^}]*?(?:port:\s*(true|false))[^}]*?(?:owner:\s*"([^"]*)")?[^}]*?(?:factionColor:\s*"([^"]*)")?[^}]*?(?:numberOfSlots:\s*(\d+|null))?[^}]*?(?:rebelFaction:\s*"([^"]*)")?[^}]*?(?:alternativeRebelFaction:\s*"([^"]*)")?[^}]*?(?:religion:\s*"([^"]*)")?[^}]*?(?:isCapital:\s*(true|false|null))?[^}]*?(?:regionKey:\s*"([^"]*)")?'

        # Pattern semplificato per estrarre i dati essenziali
        region_pattern = r'\{\s*name:\s*"([^"]+)"[^}]+?regionKey:\s*"([^"]+)"[^}]+?color:\s*"([^"]+)"'

        matches = re.finditer(region_pattern, content, re.DOTALL)

        for match in matches:
            name = match.group(1)
            region_key = match.group(2)
            color = match.group(3)

            # Cerca i metadati nel blocco completo
            block_start = match.start()
            block_end = content.find('}', match.end())
            if block_end != -1:
                block = content[block_start:block_end+1]

                # Estrai tutti i metadati
                metadata[color] = {
                    'name': name,
                    'regionKey': region_key,
                    'color': color,
                    'sea': 'true' in re.search(r'sea:\s*(true|false)', block).group(0) if re.search(r'sea:\s*(true|false)', block) else False,
                    'port': 'true' in re.search(r'port:\s*(true|false)', block).group(0) if re.search(r'port:\s*(true|false)', block) else False,
                    'owner': re.search(r'owner:\s*"([^"]*)"', block).group(1) if re.search(r'owner:\s*"([^"]*)"', block) else None,
                    'factionColor': re.search(r'factionColor:\s*"([^"]*)"', block).group(1) if re.search(r'factionColor:\s*"([^"]*)"', block) else None,
                    'numberOfSlots': None,
                    'rebelFaction': None,
                    'alternativeRebelFaction': None,
                    'religion': None,
                    'isCapital': None
                }

        print(f"Caricati metadati per {len(metadata)} regioni")

    except Exception as e:
        print(f"Errore nel caricamento dei metadati: {e}")

    return metadata

def scale_coordinates(coords):
    """Scala le coordinate dal sistema originale a quello target."""
    scaled = []
    for coord in coords:
        x, y = coord
        scaled_x = int(x * SCALE_X)
        scaled_y = int(y * SCALE_Y)
        scaled.append([scaled_x, scaled_y])
    return scaled

def coords_to_string(coords):
    """Converte una lista di coordinate in una stringa per il formato polygon."""
    return " ".join([f"{x},{y}" for x, y in coords])

def format_value(value):
    """Formatta un valore per JavaScript."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        return str(value)

def main():
    print("Caricamento dei metadati dal file regions_data.js...")
    metadata = load_region_metadata()

    print("\nLettura del file regioni_mappa.json...")
    with open('regioni_mappa.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Trovate {data['num_regioni']} regioni")
    print(f"Dimensioni originali: {data['larghezza']}x{data['altezza']}")

    print(f"\nConversione alla scala {TARGET_WIDTH}x{TARGET_HEIGHT}...")

    # Inizia a costruire il file JavaScript
    js_output = "const regions = [\n"

    for i, region in enumerate(data['regioni']):
        color = region['colore_hex']

        # Scala le coordinate
        scaled_coords = scale_coordinates(region['coordinate'])
        coords_str = coords_to_string(scaled_coords)

        # Ottieni i metadati se disponibili
        meta = metadata.get(color, {})

        # Se non ci sono metadati, usa valori di default
        name = meta.get('name', f"Region_{i}")
        region_key = meta.get('regionKey', f"mk_reg_{i}")
        sea = meta.get('sea', False)
        port = meta.get('port', False)
        owner = meta.get('owner', None)
        faction_color = meta.get('factionColor', None)

        js_output += f"""    {{
        name: {format_value(name)},
        regionKey: {format_value(region_key)},
        color: "{color}",
        sea: {format_value(sea)},
        port: {format_value(port)},
        owner: {format_value(owner)},
        factionColor: {format_value(faction_color)},
        numberOfSlots: null,
        rebelFaction: null,
        alternativeRebelFaction: null,
        religion: null,
        isCapital: null,
        polygons: [
            "{coords_str}"
        ]
    }}"""

        if i < len(data['regioni']) - 1:
            js_output += ","

        js_output += "\n"

    js_output += "];\n"

    # Salva il file
    print("\nSalvataggio del file regions_data.js...")
    with open('regions_data.js', 'w', encoding='utf-8') as f:
        f.write(js_output)

    print(f"\n✓ File regions_data.js ricostruito con successo!")
    print(f"  - {len(data['regioni'])} regioni")
    print(f"  - Coordinate scalate da {data['larghezza']}x{data['altezza']} a {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"  - Metadati applicati a {len(metadata)} regioni")

if __name__ == "__main__":
    main()
