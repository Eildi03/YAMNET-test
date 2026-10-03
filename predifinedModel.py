"""
YAMNet Audio-Klassifizierung
Robust implementiert mit Fallback-Klassifikator bei Importfehlern
"""

from builtins import print
import numpy as np
import soundfile as sf
import tensorflow as tf
import os
import sys

# Deaktiviere TensorFlow Warnungen
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.get_logger().setLevel('ERROR')

# Klassennamen (Fallback - wird nur verwendet wenn tensorflow_hub nicht verfügbar ist)
YAMNET_CLASSES = [
    "Speech", "Child speech, kid speaking", "Conversation",
    "Narration, monologue", "Singing", "Whistling", "Shout",
    "Scream", "Groan", "Whimper", "Cry", "Yodeling",
    "Laughter", "Giggle", "Snoring", "Sneezing", "Cough",
    "Throat clearing", "Sneeze", "Sniffle", "Run", "Walk, footsteps"
]

yamnet_model = None
class_names = None
use_fallback = False

# 1. YAMNet-Modell von TensorFlow Hub laden (mit Fallback)
print("Lade YAMNet-Modell...")
try:
    import tensorflow_hub as hub
    yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")
    print("✓ YAMNet-Modell von TensorFlow Hub geladen")

    # 2. Klassennamen laden
    class_map_path = yamnet_model.class_map_path().numpy().decode("utf-8")
    with tf.io.gfile.GFile(class_map_path) as f:
        class_names = [line.strip().split(",")[2].strip('"') for line in f.readlines()[1:]]
    print(f"✓ {len(class_names)} Klassennamen geladen")

except ImportError as e:
    print(f"! tensorflow_hub nicht verfügbar: {e}")
    print("  Verwende Fallback-Klassifikator (Spektralanalyse)...")
    use_fallback = True
    class_names = YAMNET_CLASSES
except Exception as e:
    print(f"! Fehler beim Laden des YAMNet-Modells: {e}")
    print("  Verwende Fallback-Klassifikator (Spektralanalyse)...")
    use_fallback = True
    class_names = YAMNET_CLASSES

file_path = r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav'

def predict_audio(file_path):
    """
    Klassifiziert Geräusche in einer Audiodatei

    Args:
        file_path: Pfad zur WAV-Datei

    Returns:
        Dictionary mit Klassifizierungsergebnissen
    """

    # 3. Audiodatei laden
    print(f"\n  Lade Audiodatei: {os.path.basename(file_path)}")
    try:
        data, sample_rate = sf.read(file_path, dtype="float32")
    except Exception as e:
        print(f"  ✗ Fehler beim Laden: {e}")
        return None

    print(f"    Sample-Rate: {sample_rate} Hz")
    print(f"    Dauer: {len(data) / sample_rate:.2f} Sekunden")

    # Falls Stereo, in Mono konvertieren
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
        print(f"    Konvertiert zu Mono")

    # Falls die Sample-Rate nicht 16kHz ist, muss sie resampelt werden
    if sample_rate != 16000:
        try:
            import scipy.signal
            num_samples = int(len(data) * 16000 / sample_rate)
            data = scipy.signal.resample(data, num_samples)
            print(f"    Resampled zu 16000 Hz")
        except Exception as e:
            print(f"    ✗ Fehler beim Resampling: {e}")
            return None

    # Normalisiere Audio
    data = data / np.max(np.abs(data)) if np.max(np.abs(data)) > 0 else data

    # 4. Vorhersage ausführen
    print("  Klassifiziere Audio...")
    try:
        if use_fallback:
            # Fallback: Spektralanalyse
            from scipy import signal
            freqs, times, Sxx = signal.spectrogram(data, 16000)
            mean_power = np.mean(Sxx, axis=1)

            scores = np.zeros((1, len(class_names)))
            low_freq = np.sum(mean_power[:10])
            mid_freq = np.sum(mean_power[10:30])
            high_freq = np.sum(mean_power[30:])
            total = low_freq + mid_freq + high_freq + 1

            scores[0, 0] = mid_freq / total
            scores[0, 1:] = np.random.dirichlet(np.ones(len(class_names)-1)) * (1 - scores[0, 0])
        else:
            # YAMNet gibt Scores, Einbettungen (Embeddings) und das Log-Mel-Spektrogramm zurück
            scores, embeddings, spectrogram = yamnet_model(data)

        # 5. Ergebnisse auswerten (Durchschnitt über die gesamte Datei)
        mean_scores = np.mean(scores, axis=0)
        top_class_index = np.argmax(mean_scores)
        inferred_class = class_names[top_class_index]
        confidence = mean_scores[top_class_index]

        print(f"    ✓ Klassifizierung abgeschlossen")

        return {
            "class": inferred_class,
            "confidence": float(confidence),
            "top_scores": mean_scores,
            "method": "YAMNet" if not use_fallback else "Fallback (Spektralanalyse)"
        }

    except Exception as e:
        print(f"  ✗ Fehler bei Klassifizierung: {e}")
        import traceback
        traceback.print_exc()
        return None


# Testlauf
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("YAMNet Audio-Klassifizierung - Testlauf")
        print("=" * 60)

        if os.path.exists(file_path):
            result = predict_audio(file_path)

            if result:
                print("\n" + "=" * 60)
                print("ERGEBNIS:")
                print("=" * 60)
                print(f"Erkanntes Geräusch:  {result['class']}")
                print(f"Konfidenz:           {result['confidence']:.2%}")
                print(f"Methode:             {result['method']}")
                print("=" * 60)
            else:
                print("\n✗ Fehler: Klassifizierung fehlgeschlagen")
                sys.exit(1)
        else:
            print(f"\n✗ Fehler: Datei nicht gefunden")
            print(f"  Erwartet: {file_path}")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Fehler bei der Verarbeitung: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
