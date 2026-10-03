"""
Spektral-Vergleich: Ein Geräusch als Vorlage verwenden
und neue Audios damit abgleichen
"""

import numpy as np
import soundfile as sf
import librosa
import pickle
import os
from scipy.spatial.distance import euclidean
from dtaidistance import dtw
import matplotlib.pyplot as plt

# === KONFIGURATION ===
REFERENCE_FILE = r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav'
TEMPLATE_SAVE_PATH = r'd:\OneDrive\EildiConsult\YAMNet-test\audio_template.pkl'
SIMILARITY_THRESHOLD = 0.7  # 0-1, höher = ähnlicher


class SpektralVergleicher:
    """Vergleicht Audios basierend auf Mel-Spektrogrammen"""

    def __init__(self, n_mels=128, n_fft=2048, hop_length=512):
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.template_mel_spec = None
        self.template_filename = None

    def load_audio(self, file_path, sr=16000):
        """Lädt Audiodatei und resampelt auf 16kHz"""
        print(f"  Lade: {os.path.basename(file_path)}")
        try:
            audio, sr = librosa.load(file_path, sr=sr, mono=True)
            print(f"    [OK] {len(audio)/sr:.2f}s @ {sr}Hz")
            return audio, sr
        except Exception as e:
            print(f"  [ERROR] Fehler: {e}")
            return None, None

    def compute_mel_spectrogram(self, audio, sr):
        """Berechnet Mel-Spektrogramm"""
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_mels=self.n_mels,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        # In dB-Skala konvertieren
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        return mel_spec_db

    def normalize_spectrogram(self, mel_spec):
        """Normalisiert Spektrogramm (0-1)"""
        min_val = np.min(mel_spec)
        max_val = np.max(mel_spec)
        if max_val - min_val == 0:
            return mel_spec
        return (mel_spec - min_val) / (max_val - min_val)

    def create_template(self, file_path):
        """Erstellt und speichert eine Vorlage aus einer Audio-Datei"""
        print(f"\n{'='*60}")
        print("ERSTELLE AUDIO-VORLAGE")
        print(f"{'='*60}")

        audio, sr = self.load_audio(file_path)
        if audio is None:
            return False

        mel_spec = self.compute_mel_spectrogram(audio, sr)
        mel_spec_norm = self.normalize_spectrogram(mel_spec)

        self.template_mel_spec = mel_spec_norm
        self.template_filename = os.path.basename(file_path)

        # Speichere Vorlage
        template_data = {
            'mel_spectrogram': mel_spec_norm,
            'filename': self.template_filename,
            'shape': mel_spec_norm.shape,
            'sr': sr
        }

        with open(TEMPLATE_SAVE_PATH, 'wb') as f:
            pickle.dump(template_data, f)

        print(f"\n[OK] Vorlage gespeichert: {TEMPLATE_SAVE_PATH}")
        print(f"  Form: {mel_spec_norm.shape}")
        return True

    def load_template(self):
        """Lädt gespeicherte Vorlage"""
        if not os.path.exists(TEMPLATE_SAVE_PATH):
            print(f"[ERROR] Vorlage nicht gefunden: {TEMPLATE_SAVE_PATH}")
            return False

        with open(TEMPLATE_SAVE_PATH, 'rb') as f:
            template_data = pickle.load(f)

        self.template_mel_spec = template_data['mel_spectrogram']
        self.template_filename = template_data['filename']
        print(f"[OK] Vorlage geladen: {self.template_filename}")
        return True

    def compare_spectrograms_dtw(self, mel_spec1, mel_spec2):
        """
        Vergleicht zwei Spektrogramme mit Dynamic Time Warping (DTW)
        DTW ist besser für zeitliche Abweichungen

        Returns: Ähnlichkeit (0-1), höher = ähnlicher
        """
        # Reduziere Dimensionen für schnellere DTW
        spec1_mean = np.mean(mel_spec1, axis=0)
        spec2_mean = np.mean(mel_spec2, axis=0)

        try:
            # DTW Distanz berechnen
            distance = dtw.distance(spec1_mean, spec2_mean)
            # Normalisiere Distanz zu Ähnlichkeit (0-1)
            max_distance = len(spec1_mean) + len(spec2_mean)
            similarity = 1.0 - min(distance / max_distance, 1.0)
            return float(similarity)
        except Exception as e:
            print(f"    DTW-Fehler: {e}, verwende Alternative")
            return self.compare_spectrograms_cosine(mel_spec1, mel_spec2)

    def compare_spectrograms_cosine(self, mel_spec1, mel_spec2):
        """
        Vergleicht Spektrogramme mit Cosine-Ähnlichkeit
        Schneller, aber weniger flexibel gegenüber zeitlichen Unterschieden
        """
        # Glätte beide Spektrogramme
        spec1_flat = np.mean(mel_spec1, axis=1)
        spec2_flat = np.mean(mel_spec2, axis=1)

        # Resample auf gleiche Länge
        if len(spec1_flat) != len(spec2_flat):
            min_len = min(len(spec1_flat), len(spec2_flat))
            spec1_flat = spec1_flat[:min_len]
            spec2_flat = spec2_flat[:min_len]

        # Cosine-Ähnlichkeit
        dot_product = np.dot(spec1_flat, spec2_flat)
        norm1 = np.linalg.norm(spec1_flat)
        norm2 = np.linalg.norm(spec2_flat)

        if float(norm1) == 0 or float(norm2) == 0:
            return 0.0

        similarity = float(dot_product / (norm1 * norm2))
        return float(max(0.0, float(similarity)))

    def compare_audio(self, file_path, method='dtw'):
        """
        Vergleicht eine Audio-Datei mit der Vorlage

        Args:
            file_path: Pfad zur Vergleichsdatei
            method: 'dtw' oder 'cosine'

        Returns:
            Dictionary mit Ergebnis
        """
        if self.template_mel_spec is None:
            print("[ERROR] Keine Vorlage geladen")
            return None

        audio, sr = self.load_audio(file_path)
        if audio is None:
            return None

        mel_spec = self.compute_mel_spectrogram(audio, sr)
        mel_spec_norm = self.normalize_spectrogram(mel_spec)

        # Vergleiche
        if method == 'dtw':
            similarity = self.compare_spectrograms_dtw(
                self.template_mel_spec,
                mel_spec_norm
            )
        else:
            similarity = self.compare_spectrograms_cosine(
                self.template_mel_spec,
                mel_spec_norm
            )

        is_match = bool(similarity >= SIMILARITY_THRESHOLD)

        result = {
            'filename': os.path.basename(file_path),
            'similarity': float(similarity),
            'match': is_match,
            'threshold': float(SIMILARITY_THRESHOLD),
            'method': method
        }

        return result

    def visualize_comparison(self, file_path, output_path=None):
        """Visualisiert Vorlage und Vergleichsspektrogramm"""
        if self.template_mel_spec is None:
            print("[ERROR] Keine Vorlage geladen")
            return

        audio, sr = self.load_audio(file_path)
        if audio is None:
            return

        mel_spec = self.compute_mel_spectrogram(audio, sr)
        mel_spec_norm = self.normalize_spectrogram(mel_spec)

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Vorlage
        img1 = librosa.display.specshow(
            self.template_mel_spec,
            sr=sr,
            hop_length=self.hop_length,
            x_axis='time',
            y_axis='mel',
            ax=axes[0],
            cmap='viridis'
        )
        axes[0].set_title(f'Vorlage: {self.template_filename}')
        fig.colorbar(img1, ax=axes[0], format='%+2.0f dB')

        # Vergleich
        img2 = librosa.display.specshow(
            mel_spec_norm,
            sr=sr,
            hop_length=self.hop_length,
            x_axis='time',
            y_axis='mel',
            ax=axes[1],
            cmap='viridis'
        )
        axes[1].set_title(f'Vergleich: {os.path.basename(file_path)}')
        fig.colorbar(img2, ax=axes[1], format='%+2.0f dB')

        plt.tight_layout()

        if output_path is None:
            output_path = r'd:\OneDrive\EildiConsult\YAMNet-test\spektrogramme.png'

        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\n[OK] Visualisierung gespeichert: {output_path}")
        plt.close()


# === MAIN ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SPEKTRAL-VERGLEICH - Audio-Matching")
    print("="*60)

    vergleicher = SpektralVergleicher()

    # 1. Vorlage erstellen
    print("\n[1/3] Erstelle Vorlage aus Referenzdatei...")
    if vergleicher.create_template(REFERENCE_FILE):

        # 2. Test: Vergleiche Vorlage mit sich selbst
        print("\n[2/3] Test: Vergleiche Vorlage mit sich selbst...")
        print("-" * 60)
        result = vergleicher.compare_audio(REFERENCE_FILE, method='dtw')
        if result:
            print(f"\nDatei:       {result['filename']}")
            print(f"Ähnlichkeit: {result['similarity']:.2%}")
            print(f"Match:       {'[OK] JA' if result['match'] else '[ERROR] NEIN'}")
            print(f"Schwelle:    {result['threshold']:.0%}")
            print(f"Methode:     {result['method'].upper()}")

        # 3. Visualisierung
        print("\n[3/3] Erstelle Visualisierung...")
        vergleicher.visualize_comparison(REFERENCE_FILE)

    print("\n" + "="*60)
    print("FERTIG!")
    print("="*60)
    print(f"\nNächste Schritte:")
    print(f"1. Mit anderen Audio-Dateien testen:")
    print(f"   result = vergleicher.compare_audio('pfad/zur/datei.wav')")
    print(f"\n2. Schwelle anpassen (SIMILARITY_THRESHOLD = {SIMILARITY_THRESHOLD})")
    print(f"3. Methode wechseln: 'dtw' oder 'cosine'")
