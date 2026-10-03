"""
Vereinfachtes Testskript für YAMNet Audio-Klassifizierung
Dieses Skript umgeht das pkg_resources Problem mit einer direkten Implementierung
"""

import numpy as np
import soundfile as sf
import os
import sys

print("=" * 60)
print("YAMNet Audio-Klassifizierung - Vereinfachter Test")
print("=" * 60)

file_path = r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav'

# 1. Prüfe ob Audiodatei existiert
print(f"\n1. Prüfe Audiodatei: {file_path}")
if os.path.exists(file_path):
    print("   ✓ Datei gefunden!")
else:
    print(f"   ✗ Datei nicht gefunden!")
    sys.exit(1)

# 2. Lade Audiodatei
print("\n2. Lade Audiodatei...")
try:
    data, sample_rate = sf.read(file_path, dtype="float32")
    print(f"   ✓ Datei geladen!")
    print(f"     Sample-Rate: {sample_rate} Hz")
    print(f"     Dauer: {len(data) / sample_rate:.2f} Sekunden")
    print(f"     Kanäle: {len(data.shape)} (", end="")
    if len(data.shape) > 1:
        print("Stereo)")
        data = np.mean(data, axis=1)
        print("     Konvertiert zu Mono")
    else:
        print("Mono)")
except Exception as e:
    print(f"   ✗ Fehler beim Laden: {e}")
    sys.exit(1)

# 3. Resample wenn nötig (YAMNet erwartet 16 kHz)
print("\n3. Prüfe Sample-Rate...")
if sample_rate != 16000:
    print(f"   ! Sample-Rate ist {sample_rate} Hz, YAMNet braucht 16000 Hz")
    try:
        import scipy.signal
        num_samples = int(len(data) * 16000 / sample_rate)
        data = scipy.signal.resample(data, num_samples)
        print(f"   ✓ Resampled zu 16000 Hz")
    except Exception as e:
        print(f"   ✗ Fehler beim Resampling: {e}")
        sys.exit(1)
else:
    print(f"   ✓ Sample-Rate ist korrekt (16 kHz)")

# 4. Versuche TensorFlow/YAMNet zu laden
print("\n4. Lade TensorFlow und YAMNet-Modell...")
try:
    import tensorflow as tf
    print("   ✓ TensorFlow importiert")

    # Versuche mit direktem Import
    try:
        import tensorflow_hub as hub
        print("   ✓ tensorflow_hub importiert")

        print("   Lade YAMNet-Modell von TensorFlow Hub...")
        yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
        print("   ✓ YAMNet-Modell geladen")

        # 5. Führe Vorhersage durch
        print("\n5. Führe Audio-Klassifizierung durch...")
        scores, embeddings, spectrogram = yamnet_model(data)

        # Lade Klassennamen
        class_map_path = yamnet_model.class_map_path().numpy().decode("utf-8")
        with tf.io.gfile.GFile(class_map_path) as f:
            class_names = [line.strip().split(",")[2].strip('"') for line in f.readlines()[1:]]

        # Auswerte Ergebnisse
        mean_scores = np.mean(scores, axis=0)
        top_class_index = np.argmax(mean_scores)
        inferred_class = class_names[top_class_index]
        confidence = mean_scores[top_class_index]

        print("\n" + "=" * 60)
        print("ERGEBNIS:")
        print("=" * 60)
        print(f"Erkanntes Geräusch: {inferred_class}")
        print(f"Konfidenz: {confidence:.2%}")
        print("=" * 60 + "\n")

    except ImportError as e:
        print(f"   ! Fehler beim Import von tensorflow_hub: {e}")
        print("   → Installieren Sie: pip install --force-reinstall tensorflow-hub")
        sys.exit(1)

except ImportError as e:
    print(f"   ✗ Fehler beim Import: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Test abgeschlossen!")
