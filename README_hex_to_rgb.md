# Convertitore Hex to RGB

Script Python per convertire colori hex in RGB in file CSV.

## Caratteristiche

- Converte colori hex (#FF5733) in tre colonne RGB separate (r, g, b)
- Mantiene la prima colonna come primary key
- Supporta CSV con o senza header
- Opzione per mantenere la colonna hex originale

## Requisiti

- Python 3.x
- Nessuna dipendenza esterna (usa solo librerie standard)

## Utilizzo

### Sintassi base

```bash
python3 hex_to_rgb_converter.py <file_input> -c <colonna> -o <file_output>
```

### Esempi

#### Con header (consigliato)

```bash
# Converti la colonna 'colore_hex' in RGB
python3 hex_to_rgb_converter.py input.csv -c colore_hex -o output.csv

# Mantieni anche la colonna hex originale
python3 hex_to_rgb_converter.py input.csv -c colore_hex -o output.csv --keep-hex
```

#### Senza header

```bash
# Converti la seconda colonna (1-based)
python3 hex_to_rgb_converter.py input.csv -c 2 -o output.csv --no-header
```

### Opzioni

- `-c, --column`: Nome della colonna (con header) o numero 1-based (senza header)
- `-o, --output`: File CSV di output
- `--no-header`: Il CSV non ha riga di intestazione
- `--keep-hex`: Mantieni anche la colonna hex originale

## Esempio di conversione

**Input (esempio_colori.csv):**
```csv
id,nome,colore_hex,descrizione
1,Rosso,#FF0000,Colore rosso puro
2,Verde,#00FF00,Colore verde puro
```

**Output (esempio_colori_rgb.csv):**
```csv
id,nome,r,g,b,descrizione
1,Rosso,255,0,0,Colore rosso puro
2,Verde,0,255,0,Colore verde puro
```

## Note

- I valori hex possono essere con o senza `#` (es. `#FF5733` o `FF5733`)
- I valori RGB sono nel range 0-255
- Le righe con colori hex non validi vengono saltate con un avviso
