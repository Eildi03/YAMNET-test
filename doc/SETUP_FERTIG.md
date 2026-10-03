# ✅ API-System ist fertig!

## 🎯 Was wurde erstellt?

### Spektral-Vergleich System (Option B)
Ein System, das deine Audio-Vorlage mit neuen Dateien vergleicht:

1. **spektral_vergleich.py** - Kern-Bibliothek
   - Extrahiert Mel-Spektrogramme
   - Vergleicht mit DTW (Dynamic Time Warping) oder Cosine-Ähnlichkeit
   - Speichert Vorlagen als `.pkl`-Dateien
   - Erstellt Spektrogramm-Visualisierungen

2. **REST API Server** - Einfacher Zugriff
   - `api_server.py` - FastAPI Server mit 7 Endpoints
   - Läuft auf `http://localhost:8000`
   - Mit automatischer Dokumentation (Swagger UI)

3. **Python Client** - Einfach zu nutzen
   - `api_client.py` - Client-Bibliothek für Python
   - Alle API-Operationen als Python-Methoden
   - Mit Error-Handling

4. **Web-Frontend** - Browser-Interface
   - `static/index.html` - Modernes Web-UI
   - Keine Installation nötig
   - Läuft direkt im Browser

---

## 🚀 Quick Start

### 1. Server starten (läuft bereits!)
```bash
python api_server.py
```

### 2. Web-Frontend öffnen
Öffne im Browser: **http://localhost:8000**

### 3. Python-Code nutzen
```python
from api_client import AudioAnalysisClient

client = AudioAnalysisClient()
result = client.compare("path/to/audio.wav")
print(f"Ähnlichkeit: {result['similarity']:.1%}")
```

---

## 📡 API Endpoints

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/` | GET | Web-Frontend öffnen |
| `/health` | GET | Server-Status prüfen |
| `/template_status` | GET | Vorlage-Info anzeigen |
| `/upload_template` | POST | Neue Vorlage hochladen |
| `/compare` | POST | Einzelne Datei vergleichen |
| `/analyze` | POST | Hybrid-Analyse (YAMNet + Spektral) |
| `/batch_compare` | POST | Mehrere Dateien auf einmal |
| `/visualize` | GET | Spektrogramm herunterladen |
| `/config` | GET | Konfiguration zeigen |
| `/docs` | GET | Swagger-Dokumentation |

---

## 📂 Dateistruktur

```
YAMNet-test/
├── spektral_vergleich.py       ← Kern-Bibliothek
├── hybrid_analyse.py           ← YAMNet + Spektral kombiniert
├── api_server.py               ← REST API Server (läuft!)
├── api_client.py               ← Python Client
├── vergleich_testen.py         ← Test-Skript
├── static/
│   └── index.html              ← Web-Frontend
├── audio_template.pkl          ← Gespeicherte Vorlage
├── spektrogramme.png           ← Visualisierung
├── README_API.md               ← Quick Start Anleitung
├── API_DOKUMENTATION.md        ← Ausführliche Doku
└── SETUP_FERTIG.md             ← Diese Datei
```

---

## 🎯 Workflows

### Workflow 1: Web-Browser verwenden
```
1. http://localhost:8000 öffnen
2. Vorlage hochladen (optional, Voreinstellung ist schon geladen)
3. Audio-Datei zum Vergleichen hochladen
4. Ergebnis anschauen (% Ähnlichkeit, Match ja/nein)
```

### Workflow 2: Python-Skript
```python
from api_client import AudioAnalysisClient

client = AudioAnalysisClient("http://localhost:8000")

# Vorlage-Status
status = client.template_status()
print(status)

# Vergleiche Datei
result = client.compare("test.wav", method="dtw")
print(f"Match: {result['match']}")

# Hybrid-Analyse
analysis = client.analyze("test.wav")
print(f"YAMNet: {analysis['yamnet']['class']}")
print(f"Spektral: {analysis['spektral']['similarity']:.1%}")

# Batch-Vergleich
results = client.batch_compare(["file1.wav", "file2.wav"])
print(results['summary'])
```

### Workflow 3: cURL / Kommandozeile
```bash
# Health Check
curl http://localhost:8000/health

# Datei vergleichen
curl -X POST -F "file=@test.wav" \
  "http://localhost:8000/compare?method=dtw"

# Hybrid-Analyse
curl -X POST -F "file=@test.wav" \
  http://localhost:8000/analyze
```

---

## ⚙️ Konfiguration anpassen

### Schwelle ändern
In `spektral_vergleich.py`:
```python
SIMILARITY_THRESHOLD = 0.7  # 0-1, höher = strenger
```

### Vergleichsmethode wählen
- **DTW** (Standard): Flexibel, aber langsamer (~100-200ms)
  - Gut bei zeitlichen Unterschieden
- **Cosine**: Schneller (~20-50ms)
  - Direkter Spektral-Vergleich

```python
result = client.compare("audio.wav", method="dtw")   # oder "cosine"
```

### Mel-Spektrogramm-Parameter
In `spektral_vergleich.py`:
```python
vergleicher = SpektralVergleicher(
    n_mels=128,      # Mel-Frequenzen
    n_fft=2048,      # FFT-Größe
    hop_length=512   # Fenster-Versatz
)
```

---

## 📊 Ausgabe-Format

### Compare
```json
{
  "success": true,
  "filename": "test.wav",
  "similarity": 0.85,      // 0-1, höher = ähnlicher
  "match": true,           // Über Schwelle?
  "threshold": 0.7,
  "method": "dtw"
}
```

### Analyze (Hybrid)
```json
{
  "success": true,
  "filename": "audio.wav",
  "yamnet": {
    "class": "Whistling",
    "confidence": 0.18
  },
  "spektral": {
    "similarity": 1.0,
    "match": true
  }
}
```

---

## 🆘 Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Connection refused" | Server starten: `python api_server.py` |
| Browser zeigt 404 | Warte 2-3 Sekunden nach Server-Start |
| "Vorlage nicht geladen" | Mit `/upload_template` hochladen |
| Datei kann nicht gelesen werden | Nur Audio-Dateien: WAV, MP3, FLAC, OGG |
| Langsame Responses | Wechsel zu `method=cosine` |
| Import-Fehler | Dependencies: `pip install -r requirements.txt` |

---

## 📚 Weitere Ressourcen

- **Quick Start**: `README_API.md`
- **Detaillierte Docs**: `API_DOKUMENTATION.md`
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Spektral-Vergleich Code**: `spektral_vergleich.py`
- **Server Code**: `api_server.py`
- **Client Code**: `api_client.py`

---

## ✨ Features

✅ **Spektral-Vergleich**
- DTW und Cosine-Ähnlichkeit
- Flexible Schwelle einstellbar
- Mel-Spektrogramm-Visualisierung

✅ **REST API**
- 7 praktische Endpoints
- CORS aktiviert (Browser-Kompatibilität)
- Automatische Dokumentation (Swagger)

✅ **Python Client**
- Einfach zu nutzen
- Alle API-Funktionen verfügbar
- Mit Error-Handling

✅ **Web-Frontend**
- Modernes Design
- Echtzeit-Ergebnisse
- Batch-Verarbeitung

✅ **Hybrid-Analyse**
- YAMNet-Klassifikation
- Spektral-Vergleich kombiniert
- Umfassende Audio-Analyse

---

## 🎓 Use Cases

### 1. Anomalieerkennung
```python
analysis = client.analyze("recording.wav")
if not analysis['spektral']['match']:
    print("⚠️ Unerwartetes Geräusch!")
```

### 2. Sound-Matching
```python
results = client.batch_compare(file_list)
similar = [r for r in results['results'] if r['match']]
print(f"✓ {len(similar)} ähnliche Dateien")
```

### 3. Echtzeit-Klassifikation
```python
for audio_file in stream:
    analysis = client.analyze(audio_file)
    print(f"Klasse: {analysis['yamnet']['class']}")
```

---

## 🚀 Nächste Schritte

### Option A: Web-Frontend nutzen
1. http://localhost:8000 öffnen
2. Dateien testen

### Option B: Python-Integration
```python
from api_client import AudioAnalysisClient
client = AudioAnalysisClient()
# Deine Code hier...
```

### Option C: cURL / Kommandozeile
```bash
curl -X POST -F "file=@audio.wav" http://localhost:8000/compare
```

---

## 📝 Support

Alle Komponenten sind vollständig dokumentiert:
- **Code-Kommentare**: In den `.py` Dateien
- **API-Docs**: `/docs` Endpoint (Swagger)
- **README**: `README_API.md` und `API_DOKUMENTATION.md`
- **Beispiele**: In jedem Datei vorhanden

---

**Status:** ✅ **FERTIG UND LÄUFT!**

Server läuft auf: http://localhost:8000
