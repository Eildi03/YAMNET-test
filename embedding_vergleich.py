"""
YAMNet-Embedding basierter Audio-Vergleich (Option C)
Nutzt die versteckte Schicht von YAMNet als kompakte Signatur
"""

import numpy as np
import pickle
import os
from scipy.spatial.distance import cosine
from pathlib import Path

try:
    import tensorflow_hub as hub
    YAMNET_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    YAMNET_AVAILABLE = False
    YAMNET_ERROR = str(e)

class EmbeddingVergleicher:
    """Vergleicht Audios mittels YAMNet-Embeddings"""

    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)

        if not YAMNET_AVAILABLE:
            print(f"[WARNING] YAMNet nicht verfuegbar: {YAMNET_ERROR}")
            print("   Fallback: Verwende Spektral-Vergleich statt Embedding")
            self.yamnet_model = None
            self.template_embedding = None
            self.template_filename = None
            self.similarity_threshold = 0.65
            return

        # YAMNet Modell laden
        try:
            print("[*] Lade YAMNet-Modell...")
            self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
            print("[OK] YAMNet geladen")
        except Exception as e:
            print(f"[ERROR] Fehler beim Laden von YAMNet: {e}")
            self.yamnet_model = None

        # Template-Speicher
        self.template_embedding = None
        self.template_filename = None
        self.similarity_threshold = 0.65

    def extract_embedding(self, audio_array, sr=16000):
        """Extrahiert YAMNet-Embedding aus Audio"""
        if self.yamnet_model is None:
            raise RuntimeError("YAMNet nicht verfuegbar - verwende spektral_vergleich stattdessen")

        # Audio muss auf 16kHz sein (YAMNet Standard)
        if sr != 16000:
            import librosa
            audio_array = librosa.resample(audio_array, orig_sr=sr, target_sr=16000)

        # Begrenzte Länge für Effizienz
        max_samples = 16000 * 30  # max 30 Sekunden
        if len(audio_array) > max_samples:
            audio_array = audio_array[:max_samples]

        # YAMNet inference
        scores, embeddings, spectrogram = self.yamnet_model(audio_array)

        # Durchschnitt über die Zeit - ein einzelner Vektor
        mean_embedding = np.mean(embeddings.numpy(), axis=0)

        return mean_embedding, scores.numpy(), spectrogram.numpy()

    def load_audio(self, audio_file):
        """Lädt Audio-Datei"""
        import soundfile as sf
        audio, sr = sf.read(audio_file)

        # Mono konvertieren
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        return audio.astype(np.float32), sr

    def create_template(self, audio_file):
        """Speichert Embedding als Template"""
        if self.yamnet_model is None:
            print("[ERROR] YAMNet nicht verfuegbar - Embedding-Template kann nicht erstellt werden")
            return False

        try:
            print(f"[*] Erstelle Embedding-Template aus: {Path(audio_file).name}")

            # Audio laden
            audio, sr = self.load_audio(audio_file)

            # Embedding extrahieren
            embedding, scores, spec = self.extract_embedding(audio, sr)

            # Speichere
            template_path = os.path.join(self.template_dir, "template_embedding.pkl")
            with open(template_path, 'wb') as f:
                pickle.dump({
                    'embedding': embedding,
                    'shape': embedding.shape,
                    'filename': Path(audio_file).name
                }, f)

            self.template_embedding = embedding
            self.template_filename = Path(audio_file).name

            print(f"[OK] Template gespeichert: {template_path}")
            print(f"     Embedding-Shape: {embedding.shape}")
            return True

        except Exception as e:
            print(f"[ERROR] Fehler beim Template erstellen: {e}")
            return False

    def load_template(self):
        """Lädt gespeichertes Template-Embedding"""
        try:
            template_path = os.path.join(self.template_dir, "template_embedding.pkl")
            if not os.path.exists(template_path):
                return False

            with open(template_path, 'rb') as f:
                data = pickle.load(f)

            self.template_embedding = data['embedding']
            self.template_filename = data['filename']
            print(f"[OK] Template geladen: {self.template_filename}")
            return True

        except Exception as e:
            print(f"[ERROR] Fehler beim Template laden: {e}")
            return False

    def compare_audio(self, audio_file):
        """Vergleicht Audio mit Template"""
        if self.yamnet_model is None:
            return None

        try:
            if self.template_embedding is None:
                return None

            # Audio laden
            audio, sr = self.load_audio(audio_file)

            # Embedding extrahieren
            embedding, scores, spec = self.extract_embedding(audio, sr)

            # Cosine Similarity berechnen (1 - distance)
            distance = cosine(self.template_embedding, embedding)
            similarity = 1.0 - distance

            # Match-Status
            match = similarity >= self.similarity_threshold

            return {
                'filename': Path(audio_file).name,
                'similarity': float(similarity),
                'match': bool(match),
                'threshold': float(self.similarity_threshold),
                'method': 'embedding',
                'embedding_shape': embedding.shape,
                'yamnet_class_scores': scores.tolist()
            }

        except Exception as e:
            print(f"[ERROR] Fehler beim Vergleich: {e}")
            return None

    def get_top_classes(self, scores, top_n=3):
        """Extrahiert Top-Klassen aus YAMNet-Scores"""
        yamnet_classes = [
            'Speech', 'Child speech', 'Conversation', 'Whispering', 'Singing',
            'Yodeling', 'Chanting', 'Whistling', 'Breathing', 'Coughing',
            'Sneezing', 'Throat clearing', 'Snoring', 'Gasp', 'Happy laughter',
            'Sad laughter', 'Giggling', 'Snickering', 'Bellowing', 'Yelling',
            'Background music', 'Domestic sounds', 'Heartbeat', 'Footsteps',
            'Keyboard typing', 'Keys jangling', 'Doorbell', 'Knock',
            'Door', 'Scratching', 'Scraping', 'Rub', 'Rolling', 'Bouncing',
            'Impact', 'Collision', 'Thump', 'Thud'
        ]

        top_indices = np.argsort(scores)[-top_n:][::-1]
        results = []
        for idx in top_indices:
            if idx < len(yamnet_classes):
                results.append({
                    'class': yamnet_classes[idx],
                    'confidence': float(scores[idx])
                })
        return results
