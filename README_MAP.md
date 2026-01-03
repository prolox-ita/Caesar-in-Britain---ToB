# Come Testare la Mappa Interattiva

## Problema CORS Risolto
Ho aggiunto l'attributo `crossOrigin="anonymous"` alle immagini per risolvere l'errore CORS.

## IMPORTANTE: Devi usare un Web Server Locale

**NON** aprire il file direttamente nel browser (file://...) - questo causerà errori CORS.

### Opzione 1: Python (Raccomandato)
```bash
cd /path/to/MK1212-website
python3 -m http.server 8000
```
Poi apri nel browser: `http://localhost:8000/map.html`

### Opzione 2: Node.js (npx http-server)
```bash
cd /path/to/MK1212-website
npx http-server -p 8000
```
Poi apri nel browser: `http://localhost:8000/map.html`

### Opzione 3: VS Code Live Server
1. Installa l'estensione "Live Server" in VS Code
2. Click destro su `map.html`
3. Seleziona "Open with Live Server"

## Debug
Apri la Console JavaScript (F12 → Console) per vedere i log:
- "Started loading images..."
- "Image loaded: 1/2"
- "Image loaded: 2/2"
- "Initializing map..."
- "Canvas dimensions: 4800x3404"
- "Drawing background map..."
- "Drawing region reference..."
- "Starting region analysis..."
- "Found X regions"
- "Map initialized successfully!"

Se vedi errori, copia il messaggio completo dalla console.
