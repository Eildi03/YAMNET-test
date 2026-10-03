# 🎙️ YAMNet Audio Analysis API - Quick Start

## Was ist das?

Ein **REST API System** zur Audio-Analyse, das kombiniert:
- **YAMNet**: Vordefinierte Audio-Klassifikation (erkennt Geräuschtypen)
- **Spektral-Vergleich**: Vergleicht neue Audios mit einer Vorlage

---

## 🚀 Schnellstart (3 Schritte)

### 1. Server starten
```bash
cd d:\OneDrive\EildiConsult\YAMNet-test
python api_server.py
```

**Output:**
```
======================================================================
  YAMNet Audio Analysis API
======================================================================

📡 Server läuft auf: http://localhost:8000

📚 API Dokumentation:
   Swagger UI: http://localhost:8000/docs
   ReDoc:      http://localhost:8000/redoc
```

### 2. API testen (Python)
```python
from api_client import AudioAnalysisClient

client = AudioAnalysisClient()

# Vergleiche Datei
result = client.compare("path/to/audio.wav")
print(f"Ähnlichkeit: {result['similarity']:.1%}")
print(f"Match: {result['match']}")
```

### 3. oder mit cURL
```bash
# Health Check
curl http://localhost:8000/health

# Vergleiche Datei
curl -X POST -F "file=@path/to/audio.wav" http://localhost:8000/compare
```

---

## 📚 Verfügbare Endpoints

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/health` | GET | Server-Status |
| `/template_status` | GET | Vorlage-Info |
| `/upload_template` | POST | Neue Vorlage hochladen |
| `/compare` | POST | Datei vergleichen |
| `/analyze` | POST | Hybrid-Analyse (YAMNet + Spektral) |
| `/batch_compare` | POST | Mehrere Dateien vergleichen |
| `/visualize` | GET | Spektrogramm herunterladen |
| `/config` | GET | Konfiguration |
| `/docs` | GET | Swagger-Dokumentation |

---

## 💻 Python-Beispiele

### Beispiel 1: Einfacher Vergleich
```python
from api_client import AudioAnalysisClient

client = AudioAnalysisClient("http://localhost:8000")

# Vergleiche gegen Vorlage
result = client.compare("test.wav", method="dtw")

if result['match']:
    print(f"✓ Match gefunden! Ähnlichkeit: {result['similarity']:.1%}")
else:
    print(f"✗ Kein Match. Ähnlichkeit: {result['similarity']:.1%}")
```

### Beispiel 2: Hybrid-Analyse
```python
# Kombiniert YAMNet + Spektral
analysis = client.analyze("audio.wav")

print(f"YAMNet erkannte: {analysis['yamnet']['class']}")
print(f"Spektral Match: {analysis['spektral']['match']}")
```

### Beispiel 3: Batch-Vergleich
```python
# Vergleiche mehrere Dateien auf einmal
results = client.batch_compare([
    "file1.wav",
    "file2.wav", 
    "file3.wav"
])

print(f"Ergebnis: {results['summary']}")
for r in results['results']:
    print(f"  {r['filename']}: {r['similarity']:.1%}")
```

### Beispiel 4: Neue Vorlage hochladen
```python
# Setze neue Referenzdatei
result = client.upload_template("new_reference.wav")

if result['success']:
    print(f"✓ Neue Vorlage: {result['template']['filename']}")
```

---

## 🔧 Konfiguration

### Schwelle anpassen
In `spektral_vergleich.py`:
```python
SIMILARITY_THRESHOLD = 0.7  # 0-1, höher = strikte
```

### Methode wechseln
- **DTW** (Standard): Flexibel, aber langsamer (~100-200ms)
  - Gut bei zeitlichen Abweichungen
- **Cosine**: Schneller (~20-50ms)
  - Direkter Spektral-Vergleich

```python
# DTW verwenden
result = client.compare("audio.wav", method="dtw")

# Cosine verwenden
result = client.compare("audio.wav", method="cosine")
```

---

## 🎯 Use Cases

### 1. Anomalieerkennung
```python
# Erkenne unerwartete Geräusche
analysis = client.analyze("recording.wav")

if not analysis['spektral']['match']:
    print("⚠️ Unbekanntes Geräusch erkannt!")
    print(f"   YAMNet klassifiziert als: {analysis['yamnet']['class']}")
```

### 2. Sound-Matching
```python
# Finde ähnliche Geräusche in Batch
results = client.batch_compare(file_list)

similar = [r for r in results['results'] if r['match']]
print(f"✓ {len(similar)} ähnliche Dateien gefunden")
```

### 3. Audio-Klassifikation
```python
# Identifiziere Geräuschtyp
analysis = client.analyze("sound.wav")

sound_class = analysis['yamnet']['class']
confidence = analysis['yamnet']['confidence']

print(f"Geräusch: {sound_class} ({confidence:.1%})")
```

---

## 🚨 Fehlerbehandlung

```python
from api_client import AudioAnalysisClient
import json

client = AudioAnalysisClient()

try:
    result = client.compare("audio.wav")
    
    if 'error' in result:
        print(f"✗ Fehler: {result['error']}")
    elif result['success']:
        print(f"✓ Ähnlichkeit: {result['similarity']:.1%}")
        
except ConnectionError:
    print("✗ API nicht erreichbar. Starte: python api_server.py")
except Exception as e:
    print(f"✗ Fehler: {e}")
```

---

## 📊 Ausgabe-Format

### Compare Response
```json
{
  "success": true,
  "filename": "test.wav",
  "similarity": 0.85,           // 0-1, höher = ähnlicher
  "match": true,                // Über Schwelle?
  "threshold": 0.7,             // Eingestellte Schwelle
  "method": "dtw"               // Verwendete Methode
}
```

### Analyze Response
```json
{
  "success": true,
  "filename": "audio.wav",
  "yamnet": {
    "class": "Whistling",        // Erkannte Klasse
    "confidence": 0.18,          // Vertrauen (0-1)
    "method": "Fallback (Spektralanalyse)"
  },
  "spektral": {
    "similarity": 1.0,           // Ähnlichkeit zur Vorlage
    "match": true,               // Über Schwelle?
    "threshold": 0.7
  }
}
```

---

## 🔗 Weitere Ressourcen

- **API Dokumentation**: `API_DOKUMENTATION.md`
- **Swagger UI**: http://localhost:8000/docs
- **Spektral-Vergleich**: `spektral_vergleich.py`
- **Client Code**: `api_client.py`

---

## ⚙️ Installation & Setup

### Abhängigkeiten
```bash
pip install fastapi uvicorn python-multipart librosa dtaidistance scipy soundfile tensorflow
```

### Server starten
```bash
python api_server.py
```

### Tests durchführen
```bash
python api_client.py
```

---

## 🆘 Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Connection refused" | Server nicht laufend: `python api_server.py` |
| "Vorlage nicht geladen" | Upload: `/upload_template` Endpoint |
| "Module not found" | Dependencies: `pip install -r requirements.txt` |
| Langsame Responses | Wechsel zu `method=cosine` statt `dtw` |

---

## 📝 Lizenz & Attribution

YAMNet: Google TensorFlow Hub
Spektral-Vergleich: Dieses Projekt
