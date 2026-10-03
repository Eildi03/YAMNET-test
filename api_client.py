"""
Python-Client für die Audio Analysis API
Einfache Nutzung der API von Python aus
"""

import requests
import json
import os
from pathlib import Path

class AudioAnalysisClient:
    """Client für die Audio Analysis API"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def health_check(self):
        """Prüft ob API verfügbar ist"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"error": str(e), "status": "offline"}

    def template_status(self):
        """Zeigt Status der Vorlage"""
        response = self.session.get(f"{self.base_url}/template_status")
        return response.json()

    def upload_template(self, file_path):
        """
        Lädt eine neue Vorlage hoch

        Args:
            file_path: Pfad zur Audio-Datei
        """
        if not os.path.exists(file_path):
            return {"error": f"Datei nicht gefunden: {file_path}"}

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/upload_template",
                files=files
            )

        return response.json()

    def compare(self, file_path, method="dtw"):
        """
        Vergleicht Audio-Datei mit Vorlage

        Args:
            file_path: Pfad zur Audio-Datei
            method: 'dtw' (spektral), 'cosine' (spektral), oder 'embedding' (semantisch)

        Returns:
            Dictionary mit Ergebnis
        """
        if not os.path.exists(file_path):
            return {"error": f"Datei nicht gefunden: {file_path}"}

        if method not in ["dtw", "cosine", "embedding"]:
            return {"error": f"Ungültige Methode: {method}. Muss 'dtw', 'cosine', oder 'embedding' sein"}

        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {'method': method}
            response = self.session.post(
                f"{self.base_url}/compare",
                files=files,
                params=params
            )

        return response.json()

    def analyze(self, file_path):
        """
        Führt Hybrid-Analyse durch (YAMNet + Spektral)

        Args:
            file_path: Pfad zur Audio-Datei

        Returns:
            Dictionary mit YAMNet und Spektral-Ergebnissen
        """
        if not os.path.exists(file_path):
            return {"error": f"Datei nicht gefunden: {file_path}"}

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}/analyze",
                files=files
            )

        return response.json()

    def batch_compare(self, file_paths):
        """
        Vergleicht mehrere Dateien gleichzeitig

        Args:
            file_paths: Liste von Dateipfaden oder Pattern

        Returns:
            Dictionary mit Batch-Ergebnissen
        """
        # Konvertiere Pattern zu Dateiliste
        if isinstance(file_paths, str):
            file_paths = list(Path('.').glob(file_paths))

        if not file_paths:
            return {"error": "Keine Dateien gefunden"}

        files = []
        for fp in file_paths:
            if os.path.exists(fp):
                files.append(('files', open(fp, 'rb')))

        try:
            response = self.session.post(
                f"{self.base_url}/batch_compare",
                files=files
            )
            return response.json()
        finally:
            # Schließe alle Dateien
            for _, f in files:
                f.close()

    def get_config(self):
        """Zeigt API-Konfiguration"""
        response = self.session.get(f"{self.base_url}/config")
        return response.json()

    def get_visualization(self, output_path="spektrogramme_api.png"):
        """Lädt die letzte Visualisierung herunter"""
        response = self.session.get(f"{self.base_url}/visualize")

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return {"success": True, "saved_to": output_path}
        else:
            return {"error": "Visualisierung nicht verfügbar"}


def demo():
    """Demo der API-Client-Nutzung"""

    print("\n" + "="*70)
    print("  Audio Analysis API - Client Demo")
    print("="*70)

    client = AudioAnalysisClient("http://localhost:8000")

    # 1. Health Check
    print("\n[1] Health Check...")
    health = client.health_check()
    print(json.dumps(health, indent=2))

    if health.get("status") == "offline":
        print("\n✗ API läuft nicht! Starte: python api_server.py")
        return

    # 2. Konfiguration
    print("\n[2] Konfiguration...")
    config = client.get_config()
    print(json.dumps(config, indent=2))

    # 3. Vorlage-Status
    print("\n[3] Vorlage-Status...")
    status = client.template_status()
    print(json.dumps(status, indent=2))

    # 4. Test-Datei
    test_file = r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav'

    if os.path.exists(test_file):
        # Vergleich - DTW
        print("\n[4a] Vergleiche Datei mit DTW (Spektral)...")
        result_dtw = client.compare(test_file, method="dtw")
        print(json.dumps(result_dtw, indent=2))

        # Vergleich - Embedding
        print("\n[4b] Vergleiche Datei mit Embedding (Semantisch)...")
        result_emb = client.compare(test_file, method="embedding")
        print(json.dumps(result_emb, indent=2))

        # Hybrid-Analyse
        print("\n[5] Hybrid-Analyse...")
        analysis = client.analyze(test_file)
        print(json.dumps(analysis, indent=2))

        # Visualisierung
        print("\n[6] Lade Visualisierung herunter...")
        viz = client.get_visualization()
        print(json.dumps(viz, indent=2))
    else:
        print(f"\n✗ Test-Datei nicht gefunden: {test_file}")

    print("\n" + "="*70)
    print("VERWENDUNGSBEISPIELE:")
    print("="*70)

    print("""
# Initialisiere Client
client = AudioAnalysisClient("http://localhost:8000")

# Vergleiche eine Datei
result = client.compare("path/to/audio.wav", method="dtw")
print(f"Ähnlichkeit: {result['similarity']:.1%}")

# Hybrid-Analyse
analysis = client.analyze("path/to/audio.wav")
if 'yamnet' in analysis:
    print(f"YAMNet: {analysis['yamnet']['class']}")
if 'spektral' in analysis:
    print(f"Spektral Match: {analysis['spektral']['match']}")

# Batch-Vergleich mehrerer Dateien
results = client.batch_compare("path/to/*.wav")
print(f"Matches: {results['summary']}")
    """)

    print("="*70 + "\n")


if __name__ == "__main__":
    demo()
