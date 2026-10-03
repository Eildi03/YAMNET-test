"""
Dieses Skript lädt das YAMNet-Modell herunter und speichert es lokal
damit die tensorflow_hub ImportError vermieden wird
"""

import os
import urllib.request
import tempfile
import shutil

print("Versuche, YAMNet-Modell herunterzuladen...")

model_url = "https://tfhub.dev/google/yamnet/1?tf-hub-format=compressed"
model_dir = r'd:\OneDrive\EildiConsult\YAMNet-test\models'
model_path = os.path.join(model_dir, 'yamnet.tar.gz')

# Erstelle Modellverzeichnis
os.makedirs(model_dir, exist_ok=True)

try:
    print(f"Lade Modell herunter nach: {model_path}")
    urllib.request.urlretrieve(model_url, model_path)
    print("✓ Download erfolgreich!")

    # Extrahiere
    import tarfile
    extract_path = os.path.join(model_dir, 'yamnet')
    print(f"Extrahiere nach: {extract_path}")
    with tarfile.open(model_path, 'r:gz') as tar:
        tar.extractall(extract_path)
    print("✓ Extraktion erfolgreich!")
    print(f"\nModell-Pfad: {extract_path}")

except Exception as e:
    print(f"✗ Fehler: {e}")
    import traceback
    traceback.print_exc()
