#!/usr/bin/env python3
"""
Script per convertire colori hex in RGB in un file CSV.
La prima colonna viene mantenuta come primary key.
"""

import csv
import argparse
import sys
import os


def hex_to_rgb(hex_color):
    """
    Converte un colore hex in RGB.

    Args:
        hex_color: Stringa hex (es. '#FF5733' o 'FF5733')

    Returns:
        Tupla (r, g, b) con valori 0-255
    """
    # Rimuovi il # se presente
    hex_color = hex_color.lstrip('#')

    # Verifica che sia un valore hex valido
    if len(hex_color) != 6:
        raise ValueError(f"Colore hex non valido: {hex_color}")

    try:
        # Converti in RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        raise ValueError(f"Colore hex non valido: {hex_color}")


def convert_csv(input_file, output_file, hex_column, keep_hex=False):
    """
    Converte un CSV con colori hex in RGB.

    Args:
        input_file: Percorso del file CSV di input
        output_file: Percorso del file CSV di output
        hex_column: Nome o indice (1-based) della colonna con i colori hex
        keep_hex: Se True, mantiene anche la colonna hex originale
    """
    if not os.path.exists(input_file):
        print(f"Errore: File '{input_file}' non trovato.", file=sys.stderr)
        sys.exit(1)

    rows_converted = 0

    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile) if isinstance(hex_column, str) else csv.reader(infile)

        if isinstance(hex_column, str):
            # Modalità con header (usa nomi colonne)
            fieldnames = reader.fieldnames

            if hex_column not in fieldnames:
                print(f"Errore: Colonna '{hex_column}' non trovata nel CSV.", file=sys.stderr)
                print(f"Colonne disponibili: {', '.join(fieldnames)}", file=sys.stderr)
                sys.exit(1)

            # Crea nuovi fieldnames
            new_fieldnames = []
            for field in fieldnames:
                new_fieldnames.append(field)
                if field == hex_column:
                    if not keep_hex:
                        new_fieldnames.pop()  # Rimuovi la colonna hex
                    new_fieldnames.extend(['r', 'g', 'b'])

            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
                writer.writeheader()

                for row in reader:
                    try:
                        hex_value = row[hex_column]
                        r, g, b = hex_to_rgb(hex_value)

                        new_row = {}
                        for field in fieldnames:
                            if field == hex_column:
                                if keep_hex:
                                    new_row[field] = row[field]
                                new_row['r'] = r
                                new_row['g'] = g
                                new_row['b'] = b
                            else:
                                new_row[field] = row[field]

                        writer.writerow(new_row)
                        rows_converted += 1
                    except ValueError as e:
                        print(f"Avviso: {e} - Riga saltata", file=sys.stderr)
        else:
            # Modalità senza header (usa indici)
            hex_col_idx = hex_column - 1  # Converti da 1-based a 0-based

            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile)

                for row in reader:
                    if hex_col_idx >= len(row):
                        print(f"Errore: Indice colonna {hex_column} fuori range.", file=sys.stderr)
                        sys.exit(1)

                    try:
                        hex_value = row[hex_col_idx]
                        r, g, b = hex_to_rgb(hex_value)

                        new_row = []
                        for i, value in enumerate(row):
                            if i == hex_col_idx:
                                if keep_hex:
                                    new_row.append(value)
                                new_row.extend([r, g, b])
                            else:
                                new_row.append(value)

                        writer.writerow(new_row)
                        rows_converted += 1
                    except ValueError as e:
                        print(f"Avviso: {e} - Riga saltata", file=sys.stderr)

    print(f"Conversione completata! {rows_converted} righe convertite.")
    print(f"File salvato in: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Converte colori hex in RGB in un file CSV.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Con header, colonna chiamata 'color'
  python hex_to_rgb_converter.py input.csv -c color -o output.csv

  # Senza header, colonna 2
  python hex_to_rgb_converter.py input.csv -c 2 -o output.csv --no-header

  # Mantieni anche la colonna hex originale
  python hex_to_rgb_converter.py input.csv -c color -o output.csv --keep-hex
        """
    )

    parser.add_argument('input', help='File CSV di input')
    parser.add_argument('-c', '--column', required=True,
                        help='Nome o numero (1-based) della colonna con i colori hex')
    parser.add_argument('-o', '--output', required=True,
                        help='File CSV di output')
    parser.add_argument('--no-header', action='store_true',
                        help='Il CSV non ha header (usa indici numerici)')
    parser.add_argument('--keep-hex', action='store_true',
                        help='Mantieni anche la colonna hex originale')

    args = parser.parse_args()

    # Determina se la colonna è un nome o un indice
    if args.no_header:
        try:
            hex_column = int(args.column)
        except ValueError:
            print("Errore: Con --no-header, -c deve essere un numero.", file=sys.stderr)
            sys.exit(1)
    else:
        hex_column = args.column

    convert_csv(args.input, args.output, hex_column, args.keep_hex)


if __name__ == '__main__':
    main()
