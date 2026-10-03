"""
REST API für Spektral-Vergleich und Hybrid-Analyse
Starte mit: python api_server.py
API Dokumentation unter: http://localhost:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
import tempfile
import os
from spektral_vergleich import SpektralVergleicher
from embedding_vergleich import EmbeddingVergleicher
from hybrid_analyse import analyze_audio
import logging
import json

class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(
    title="YAMNet Audio Analysis API",
    description="Kombiniert YAMNet mit Spektral-Vergleich für Audio-Analyse",
    version="1.0.0"
)

# CORS aktivieren (für Frontend-Zugriff)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files (Web-Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Globale Instanzen
vergleicher = SpektralVergleicher()
try:
    embedding_vergleicher = EmbeddingVergleicher()
except Exception as e:
    logger.error(f"Embedding init error: {e}")
    embedding_vergleicher = None

template_loaded = False
embedding_template_loaded = False

# Beim Start: Versuche Vorlagen zu laden
@app.on_event("startup")
async def startup_event():
    global template_loaded, embedding_template_loaded
    try:
        if vergleicher.load_template():
            template_loaded = True
            logger.info("[OK] Spektral-Vorlage geladen")
        else:
            logger.warning("[ERROR] Spektral-Vorlage konnte nicht geladen werden")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Spektral-Vorlage: {e}")

    try:
        if embedding_vergleicher is not None and embedding_vergleicher.load_template():
            embedding_template_loaded = True
            logger.info("[OK] Embedding-Vorlage geladen")
        else:
            logger.warning("[ERROR] Embedding-Vorlage konnte nicht geladen werden")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Embedding-Vorlage: {e}")


# === ENDPOINTS ===

@app.get("/")
async def root():
    """Root endpoint - Redirect zum Frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

@app.get("/index.html", response_class=HTMLResponse)
async def index():
    """Web-Frontend HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return "<h1>Frontend nicht gefunden</h1>"


@app.get("/health")
async def health_check():
    """Prüft ob API läuft und ob Vorlage geladen ist"""
    return {
        "status": "healthy",
        "template_loaded": template_loaded,
        "service": "Audio Analysis Service"
    }


@app.get("/template_status")
async def template_status():
    """Zeigt Status beider Audio-Vorlagen"""
    response = {
        "filename": None,
        "methods": [],
        "spektral": {
            "loaded": template_loaded,
            "shape": None
        },
        "embedding": {
            "loaded": embedding_template_loaded,
            "shape": None
        }
    }

    if template_loaded:
        response["filename"] = vergleicher.template_filename
        response["spektral"]["shape"] = list(vergleicher.template_mel_spec.shape)
        response["methods"].append("dtw")
        response["methods"].append("cosine")

    if embedding_template_loaded:
        response["filename"] = embedding_vergleicher.template_filename
        response["embedding"]["shape"] = list(embedding_vergleicher.template_embedding.shape)
        response["methods"].append("embedding")

    if not template_loaded and not embedding_template_loaded:
        response["message"] = "[ERROR] Keine Vorlagen geladen - nutze /upload_template"
    else:
        response["message"] = f"[OK] {len(response['methods'])} Methoden verfügbar"

    return response


@app.post("/upload_template")
async def upload_template(file: UploadFile = File(...)):
    """
    Uploaded eine neue Audio-Datei als Vorlage für BEIDE Methoden

    **Parameter:**
    - file: Audio-Datei (WAV, MP3, etc.)

    **Erstellt:**
    - Spektral-Template (Option B: DTW/Cosine)
    - Embedding-Template (Option C: Semantisch)
    """
    global template_loaded, embedding_template_loaded

    if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.ogg')):
        raise HTTPException(status_code=400, detail="Nur Audio-Dateien erlaubt (WAV, MP3, FLAC, OGG)")

    try:
        # Speichere Datei temporär
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Erstelle BEIDE Templates
        spektral_ok = vergleicher.create_template(tmp_path)
        embedding_ok = embedding_vergleicher.create_template(tmp_path) if embedding_vergleicher is not None else False
        os.unlink(tmp_path)

        if spektral_ok:
            template_loaded = True
            embedding_template_loaded = bool(embedding_ok)

            return JSONResponse({
                "success": True,
                "message": "[OK] Beide Vorlagen erfolgreich erstellt",
                "template": {
                    "filename": vergleicher.template_filename,
                    "spektral_shape": list(vergleicher.template_mel_spec.shape),
                    "embedding_shape": list(embedding_vergleicher.template_embedding.shape) if embedding_ok else None,
                    "methods": ["dtw", "cosine"] + (["embedding"] if embedding_ok else [])
                }
            }, status_code=201)
        else:
            raise HTTPException(status_code=400, detail="Fehler bei: Spektral-Template")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Upload der Vorlage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
async def compare_audio(
    file: UploadFile = File(...),
    method: str = Query("dtw", description="Vergleichsmethode: 'dtw', 'cosine', oder 'embedding'")
):
    """
    Vergleicht eine hochgeladene Audio-Datei mit der Vorlage

    **Parameter:**
    - file: Audio-Datei zum Vergleichen
    - method:
      - 'dtw' (flexibel, Option B)
      - 'cosine' (schnell, Option B)
      - 'embedding' (semantisch, Option C)

    **Returns:**
    - similarity: Ähnlichkeit (0-1)
    - match: Ob es oberhalb der Schwelle ist
    - method: Verwendete Methode
    """

    if method == "embedding":
        if not embedding_template_loaded or embedding_vergleicher is None:
            raise HTTPException(
                status_code=503,
                detail="Embedding-Vorlage nicht geladen - nutze /upload_template zuerst"
            )
    else:
        if not template_loaded:
            raise HTTPException(
                status_code=503,
                detail="Vorlage nicht geladen - nutze /upload_template zuerst"
            )

    if method not in ["dtw", "cosine", "embedding"]:
        raise HTTPException(status_code=400, detail="Methode muss 'dtw', 'cosine', oder 'embedding' sein")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Vergleiche je nach Methode
        if method == "embedding":
            result = embedding_vergleicher.compare_audio(tmp_path)
        else:
            result = vergleicher.compare_audio(tmp_path, method=method)

        os.unlink(tmp_path)

        if result:
            return {
                "success": True,
                "filename": str(result['filename']),
                "similarity": float(result['similarity']),
                "match": bool(result['match']),
                "threshold": float(result['threshold']),
                "method": str(result['method']),
                "message": "OK - Vergleich erfolgreich"
            }
        else:
            raise HTTPException(status_code=400, detail="Vergleich fehlgeschlagen")

    except Exception as e:
        logger.error(f"Fehler beim Vergleich: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return error as plain text to avoid JSON serialization issues
        error_msg = f"{type(e).__name__}: {str(e)[:100]}"
        return JSONResponse(
            {"error": error_msg, "success": False},
            status_code=500
        )


@app.post("/analyze")
async def analyze_audio_hybrid(file: UploadFile = File(...)):
    """
    Führt vollständige Hybrid-Analyse durch (YAMNet + Spektral)

    **Parameter:**
    - file: Audio-Datei

    **Returns:**
    - yamnet: YAMNet-Klassifikation
    - spektral: Spektral-Vergleich (falls Vorlage geladen)
    """

    try:
        # Speichere Datei temporär
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Analysiere
        result = analyze_audio(tmp_path)
        os.unlink(tmp_path)

        if result:
            response = {
                "success": True,
                "filename": file.filename,
                "message": "[OK] Analyse erfolgreich"
            }

            # Füge YAMNet-Ergebnisse hinzu
            if 'yamnet' in result:
                yamnet = result['yamnet']
                response['yamnet'] = {
                    "class": yamnet['class'],
                    "confidence": float(yamnet['confidence']),
                    "method": yamnet['method']
                }

            # Füge Spektral-Ergebnisse hinzu
            if 'spektral' in result:
                spektral = result['spektral']
                response['spektral'] = {
                    "similarity": float(spektral['similarity']),
                    "match": bool(spektral['match']),
                    "threshold": float(spektral['threshold'])
                }

            return JSONResponse(response)
        else:
            raise HTTPException(status_code=400, detail="Analyse fehlgeschlagen")

    except Exception as e:
        logger.error(f"Fehler bei Hybrid-Analyse: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_compare")
async def batch_compare(files: list[UploadFile] = File(...)):
    """
    Vergleicht mehrere Audio-Dateien gleichzeitig mit der Vorlage

    **Parameter:**
    - files: Liste von Audio-Dateien

    **Returns:**
    - results: Array mit Vergleichsergebnissen
    - summary: Zusammenfassung (Matches, Total)
    """

    if not template_loaded:
        raise HTTPException(
            status_code=503,
            detail="Vorlage nicht geladen - nutze /upload_template zuerst"
        )

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="Mindestens eine Datei erforderlich")

    results = []

    try:
        for file in files:
            try:
                # Speichere Datei temporär
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name

                # Vergleiche
                result = vergleicher.compare_audio(tmp_path, method='dtw')
                os.unlink(tmp_path)

                if result:
                    results.append({
                        "filename": result['filename'],
                        "similarity": float(result['similarity']),
                        "match": bool(result['match']),
                        "threshold": float(result['threshold'])
                    })
            except Exception as e:
                logger.error(f"Fehler bei {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        # Berechne Zusammenfassung
        matches = sum(1 for r in results if r.get('match', False))

        return JSONResponse({
            "success": True,
            "total_files": len(files),
            "matches": matches,
            "no_matches": len(files) - matches,
            "results": results,
            "summary": f"{matches}/{len(files)} Matches gefunden"
        })

    except Exception as e:
        logger.error(f"Fehler bei Batch-Vergleich: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize")
async def get_visualization():
    """
    Gibt die zuletzt generierte Visualisierung zurück
    """
    viz_path = r'd:\OneDrive\EildiConsult\YAMNet-test\spektrogramme.png'

    if not os.path.exists(viz_path):
        raise HTTPException(status_code=404, detail="Visualisierung nicht gefunden")

    return FileResponse(viz_path, media_type="image/png")


@app.get("/config")
async def get_config():
    """
    Zeigt aktuelle Konfiguration
    """
    return {
        "methods_available": ["dtw", "cosine", "embedding"],
        "spektral": {
            "similarity_threshold": 0.7,
            "mel_bins": vergleicher.n_mels,
            "n_fft": vergleicher.n_fft,
            "hop_length": vergleicher.hop_length,
            "description": "Option B - Mel-Spektrogramm basiert"
        },
        "embedding": {
            "similarity_threshold": 0.65,
            "embedding_dim": 1024,
            "model": "YAMNet",
            "description": "Option C - Semantische Embedding-Ähnlichkeit"
        },
        "sample_rate": 16000
    }


# === MAIN ===
if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*70)
    print("  YAMNet Audio Analysis API")
    print("="*70)
    print("\n[*] Server laeuft auf: http://localhost:8000")
    print("\n[API] Dokumentation:")
    print("   Swagger UI: http://localhost:8000/docs")
    print("   ReDoc:      http://localhost:8000/redoc")
    print("\n[*] Schnellstart:")
    print("   1. POST /upload_template - Vorlage hochladen")
    print("   2. POST /compare - Audio vergleichen")
    print("   3. POST /analyze - Hybrid-Analyse")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
