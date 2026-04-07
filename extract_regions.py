#!/usr/bin/env python3
"""
Estrae i bordi delle regioni dalla mappa lookup TGA
e genera il file cib_data.js per la mappa interattiva.
"""

import csv
from PIL import Image
import json

# Configurazione
LOOKUP_FILE = "vik_attila_lookup.tga"
LIST_FILE = "cib_list.txt"
OUTPUT_FILE = "cib_data.js"
SCALE_FACTOR = 0.5  # Scala l'immagine al 50% per dimensioni web

def hex_to_rgb(hex_color):
    """Converte colore hex in RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def load_region_colors(list_file):
    """Carica la mappatura region_key -> colore da cib_list.txt."""
    regions = {}
    with open(list_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            key = row['region key'].strip()
            is_sea = row['is sea?'].strip().lower() == 'true'
            hex_color = row['hex'].strip()
            rgb = hex_to_rgb(hex_color)
            regions[rgb] = {
                'key': key,
                'is_sea': is_sea,
                'hex': hex_color
            }
    return regions

def find_region_bounds(img, color):
    """Trova i limiti (bounding box) di una regione con un dato colore."""
    pixels = img.load()
    width, height = img.size

    min_x, min_y = width, height
    max_x, max_y = 0, 0
    found = False

    for y in range(height):
        for x in range(width):
            if pixels[x, y][:3] == color:
                found = True
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if not found:
        return None

    return (min_x, min_y, max_x, max_y)

def extract_border_points(img, color, bounds, simplify=5):
    """Estrae i punti del bordo di una regione."""
    if not bounds:
        return []

    pixels = img.load()
    min_x, min_y, max_x, max_y = bounds
    border_points = []

    # Scannerizza il bounding box per trovare i bordi
    for y in range(min_y, max_y + 1, simplify):
        for x in range(min_x, max_x + 1, simplify):
            if pixels[x, y][:3] == color:
                # Controlla se è un pixel di bordo (ha almeno un vicino diverso)
                is_border = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < img.size[0] and 0 <= ny < img.size[1]:
                            if pixels[nx, ny][:3] != color:
                                is_border = True
                                break
                    if is_border:
                        break

                if is_border:
                    border_points.append((x, y))

    return border_points

def main():
    print(f"Caricamento {LIST_FILE}...")
    region_colors = load_region_colors(LIST_FILE)
    print(f"Trovate {len(region_colors)} regioni")

    print(f"\nCaricamento {LOOKUP_FILE}...")
    img = Image.open(LOOKUP_FILE)

    # Converti in RGB se necessario
    if img.mode != 'RGB':
        img = img.convert('RGB')

    original_size = img.size
    print(f"Dimensioni originali: {original_size[0]}×{original_size[1]}")

    # Scala l'immagine se richiesto
    if SCALE_FACTOR != 1.0:
        new_size = (int(img.size[0] * SCALE_FACTOR), int(img.size[1] * SCALE_FACTOR))
        img = img.resize(new_size, Image.NEAREST)  # NEAREST per mantenere i colori esatti
        print(f"Dimensioni scalate: {img.size[0]}×{img.size[1]}")

    # Estrai le regioni
    regions_data = {}
    print("\nEstrazione regioni...")

    for i, (rgb, info) in enumerate(region_colors.items(), 1):
        key = info['key']
        print(f"[{i}/{len(region_colors)}] Processando {key}...", end=' ')

        # Trova i limiti della regione
        bounds = find_region_bounds(img, rgb)
        if not bounds:
            print("⚠️  Non trovata")
            continue

        # Estrai i punti del bordo (semplificati)
        border = extract_border_points(img, rgb, bounds, simplify=3)

        if border:
            regions_data[key] = {
                'color': f"#{info['hex']}",
                'isSea': info['is_sea'],
                'bounds': border,
                'center': [
                    (bounds[0] + bounds[2]) // 2,
                    (bounds[1] + bounds[3]) // 2
                ]
            }
            print(f"✓ {len(border)} punti")
        else:
            print("⚠️  Nessun bordo")

    # Genera il file JavaScript
    print(f"\nGenerazione {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("// Dati regioni CK3 - Generato automaticamente\n")
        f.write("// Dimensioni mappa: {}×{}\n".format(img.size[0], img.size[1]))
        f.write("\nconst CIB_REGIONS = ")
        json.dump(regions_data, f, indent=2)
        f.write(";\n")

    print(f"\n✅ Fatto! {len(regions_data)} regioni estratte")
    print(f"📁 Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
