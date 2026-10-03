# Audio Analysis API - Dokumentation

## Übersicht

REST API für Audio-Klassifikation mit YAMNet und Spektral-Vergleich.

**Base URL:** `http://localhost:8000`

**Dokumentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Server starten

```bash
python api_server.py
```

Der Server läuft dann auf `http://localhost:8000`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Prüft ob API läuft und ob Vorlage geladen ist.

**Curl/PowerShell:**
```bash
# Bash/Git Bash
curl http://localhost:8000/health

# PowerShell
curl.exe http://localhost:8000/health
# oder
Invoke-WebRequest -Uri http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "template_loaded": true,
  "service": "Audio Analysis Service"
}
```

---

### 2. Vorlage-Status

**GET** `/template_status`

Zeigt Informationen zur geladenen Audio-Vorlage.

**Curl:**
```bash
curl http://localhost:8000/template_status
```

**Response:**
```json
{
  "template_loaded": true,
  "filename": "AUDIO-2026-09-29-02-04-15.wav",
  "shape": [128, 2400],
  "message": "✓ Vorlage bereit zum Vergleichen"
}
```

---

### 3. Vorlage hochladen

**POST** `/upload_template`

Lädt eine neue Audio-Datei als Vorlage hoch (ersetzt die alte).

**Parameter:**
- `file` (multipart/form-data): Audio-Datei (WAV, MP3, FLAC, OGG)

**Curl/PowerShell:**
```bash
# Bash
curl -X POST -F "file=@path/to/audio.wav" http://localhost:8000/upload_template

# PowerShell
$file = Get-Item "path/to/audio.wav"
$form = @{ file = $file }
Invoke-WebRequest -Uri "http://localhost:8000/upload_template" `
    -Method POST -Form $form
```

**Response:**
```json
{
  "success": true,
  "message": "✓ Vorlage erfolgreich erstellt",
  "template": {
    "filename": "audio.wav",
    "shape": [128, 2400]
  }
}
```

---

### 4. Audio vergleichen

**POST** `/compare`

Vergleicht eine hochgeladene Audio-Datei mit der Vorlage.

**Parameter:**
- `file` (multipart/form-data): Audio-Datei
- `method` (query, optional): `dtw` (Standard) oder `cosine`

**Curl/PowerShell:**
```bash
# Bash - Mit DTW
curl -X POST -F "file=@path/to/test.wav" http://localhost:8000/compare?method=dtw

# PowerShell
$file = Get-Item "path/to/test.wav"
$form = @{ file = $file }
Invoke-WebRequest -Uri "http://localhost:8000/compare?method=dtw" `
    -Method POST -Form $form
```

**Response:**
```json
{
  "success": true,
  "filename": "test.wav",
  "similarity": 0.85,
  "match": true,
  "threshold": 0.7,
  "method": "dtw",
  "message": "✓ Vergleich erfolgreich"
}
```

**Erklärung:**
- `similarity`: Ähnlichkeit (0-1), höher = ähnlicher
- `match`: Ob über der Schwelle (`threshold`)
- `threshold`: Eingestellte Schwelle (70%)

---

### 5. Hybrid-Analyse

**POST** `/analyze`

Führt vollständige Analyse durch: YAMNet-Klassifikation + Spektral-Vergleich

**Parameter:**
- `file` (multipart/form-data): Audio-Datei

**Curl/PowerShell:**
```bash
# Bash
curl -X POST -F "file=@path/to/audio.wav" http://localhost:8000/analyze

# PowerShell
$file = Get-Item "path/to/audio.wav"
$form = @{ file = $file }
Invoke-WebRequest -Uri "http://localhost:8000/analyze" `
    -Method POST -Form $form
```

**Response:**
```json
{
  "success": true,
  "filename": "audio.wav",
  "message": "✓ Analyse erfolgreich",
  "yamnet": {
    "class": "Whistling",
    "confidence": 0.18,
    "method": "Fallback (Spektralanalyse)"
  },
  "spektral": {
    "similarity": 1.0,
    "match": true,
    "threshold": 0.7
  }
}
```

**Erklärung:**
- `yamnet.class`: Erkannte Geräuschklasse
- `yamnet.confidence`: Konfidenz der Klassifikation (0-1)
- `spektral.similarity`: Ähnlichkeit zur Vorlage
- `spektral.match`: Ob oberhalb der Schwelle

---

### 6. Batch-Vergleich

**POST** `/batch_compare`

Vergleicht mehrere Audio-Dateien gleichzeitig mit der Vorlage.

**Parameter:**
- `files` (multipart/form-data, multiple): Mehrere Audio-Dateien

**Curl/PowerShell:**
```bash
# Bash
curl -X POST \
  -F "files=@file1.wav" \
  -F "files=@file2.wav" \
  -F "files=@file3.wav" \
  http://localhost:8000/batch_compare

# PowerShell
$files = @(
    Get-Item "file1.wav",
    Get-Item "file2.wav",
    Get-Item "file3.wav"
)
$form = @{
    files = $files
}
Invoke-WebRequest -Uri "http://localhost:8000/batch_compare" `
    -Method POST -Form $form
```

**Response:**
```json
{
  "success": true,
  "total_files": 3,
  "matches": 2,
  "no_matches": 1,
  "results": [
    {
      "filename": "file1.wav",
      "similarity": 0.92,
      "match": true,
      "threshold": 0.7
    },
    {
      "filename": "file2.wav",
      "similarity": 0.65,
      "match": false,
      "threshold": 0.7
    },
    {
      "filename": "file3.wav",
      "similarity": 0.88,
      "match": true,
      "threshold": 0.7
    }
  ],
  "summary": "2/3 Matches gefunden"
}
```

---

### 7. Visualisierung abrufen

**GET** `/visualize`

Lädt die Spektrogramm-Visualisierung (PNG) herunter.

**Curl/PowerShell:**
```bash
# Bash
curl -X GET http://localhost:8000/visualize -o spektrogramme.png

# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/visualize" `
    -OutFile "spektrogramme.png"
```

**Response:** PNG-Bild

---

### 8. Konfiguration

**GET** `/config`

Zeigt aktuelle API-Konfiguration.

**Curl:**
```bash
curl http://localhost:8000/config
```

**Response:**
```json
{
  "similarity_threshold": 0.7,
  "mel_bins": 128,
  "n_fft": 2048,
  "hop_length": 512,
  "sample_rate": 16000,
  "methods_available": ["dtw", "cosine"]
}
```

---

## Python-Client verwenden

### Installation
```bash
pip install requests
```

### Beispiele

```python
from api_client import AudioAnalysisClient

# Client initialisieren
client = AudioAnalysisClient("http://localhost:8000")

# 1. Health Check
health = client.health_check()
print(health)

# 2. Neue Vorlage hochladen
result = client.upload_template("path/to/reference.wav")
print(result)

# 3. Datei vergleichen
result = client.compare("path/to/test.wav", method="dtw")
print(f"Ähnlichkeit: {result['similarity']:.1%}")
print(f"Match: {result['match']}")

# 4. Hybrid-Analyse
analysis = client.analyze("path/to/audio.wav")
if 'yamnet' in analysis:
    print(f"YAMNet: {analysis['yamnet']['class']}")
if 'spektral' in analysis:
    print(f"Spektral Match: {analysis['spektral']['match']}")

# 5. Mehrere Dateien auf einmal
results = client.batch_compare([
    "path/to/file1.wav",
    "path/to/file2.wav",
    "path/to/file3.wav"
])
print(results['summary'])

# 6. Visualisierung herunterladen
viz = client.get_visualization("output.png")
```

---

## Fehlerbehandlung

### Beispiel-Fehler

**Vorlage nicht geladen:**
```json
{
  "detail": "Vorlage nicht geladen - nutze /upload_template zuerst"
}
```

**Ungültige Datei:**
```json
{
  "detail": "Nur Audio-Dateien erlaubt (WAV, MP3, FLAC, OGG)"
}
```

**Server-Fehler:**
```json
{
  "detail": "Fehler beim Verarbeiten: [Error message]"
}
```

---

## Workflow-Beispiel

### Szenario: Neue Vorlage + Vergleich mehrerer Dateien

```python
from api_client import AudioAnalysisClient

client = AudioAnalysisClient("http://localhost:8000")

# 1. Neue Referenz-Datei hochladen
print("Lade Vorlage...")
template_result = client.upload_template("path/to/reference_sound.wav")
print(template_result)

# 2. Vergleiche mehrere Test-Dateien
print("\nVergleiche Dateien...")
test_files = [
    "path/to/test1.wav",
    "path/to/test2.wav",
    "path/to/test3.wav"
]

for file in test_files:
    result = client.compare(file)
    status = "✓ MATCH" if result['match'] else "✗ KEIN MATCH"
    print(f"{file}: {result['similarity']:.1%} {status}")

# 3. Batch-Vergleich für Übersicht
print("\nBatch-Vergleich...")
batch = client.batch_compare(test_files)
print(f"Gesamt: {batch['summary']}")
```

---

## Performance-Tipps

1. **DTW vs. Cosine:**
   - **DTW**: Flexibler, aber langsamer (~100-200ms pro Datei)
   - **Cosine**: Schneller (~20-50ms), aber weniger flexibel

2. **Batch-Vergleich:**
   - Nutze `/batch_compare` statt einzelner Anfragen
   - Schneller und effizienter

3. **Vorlage:**
   - Wird beim Start geladen
   - Kann jederzeit mit `/upload_template` gewechselt werden

---

## Troubleshooting

### "Connection refused"
→ Server läuft nicht. Starte mit `python api_server.py`

### "Vorlage nicht geladen"
→ Lade mit `/upload_template` eine Datei hoch oder starte Server neu

### "Module not found"
→ Installiere Dependencies: `pip install fastapi uvicorn python-multipart librosa dtaidistance`

---

## Weiterführende Links

- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [Uvicorn Dokumentation](https://www.uvicorn.org/)
- [Requests Library](https://requests.readthedocs.io/)

