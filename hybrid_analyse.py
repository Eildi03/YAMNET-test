"""
Hybrid-Analyse: YAMNet + Spektral-Vergleich
Kombiniert die vordefinierte YAMNet-Klassifikation mit dem neuen Spektral-Vergleich
"""

import sys
import os
from predifinedModel import predict_audio
from spektral_vergleich import SpektralVergleicher

def analyze_audio(file_path):
    """
    Analysiert eine Audiodatei mit beiden Methoden

    Returns:
        Dictionary mit Ergebnissen von YAMNet und Spektral-Vergleich
    """

    print("\n" + "="*60)
    print(f"HYBRID-ANALYSE: {os.path.basename(file_path)}")
    print("="*60)

    if not os.path.exists(file_path):
        print(f"✗ Datei nicht gefunden: {file_path}")
        return None

    results = {}

    # === METHODE 1: YAMNet ===
    print("\n[1/2] YAMNet-Klassifikation...")
    print("-" * 60)
    yamnet_result = predict_audio(file_path)

    if yamnet_result:
        results['yamnet'] = yamnet_result
        print(f"✓ Erkanntes Geräusch:  {yamnet_result['class']}")
        print(f"  Konfidenz:           {yamnet_result['confidence']:.2%}")
        print(f"  Methode:             {yamnet_result['method']}")
    else:
        print("✗ YAMNet-Klassifikation fehlgeschlagen")

    # === METHODE 2: Spektral-Vergleich ===
    print("\n[2/2] Spektral-Vergleich...")
    print("-" * 60)

    vergleicher = SpektralVergleicher()
    if vergleicher.load_template():
        spektral_result = vergleicher.compare_audio(file_path, method='dtw')
        if spektral_result:
            results['spektral'] = spektral_result
            match_text = "✓ MATCH" if spektral_result['match'] else "✗ KEIN MATCH"
            print(f"Ähnlichkeit zur Vorlage: {spektral_result['similarity']:.1%}  {match_text}")
            print(f"Schwelle:                {spektral_result['threshold']:.0%}")
    else:
        print("✗ Spektral-Vergleich nicht möglich (Vorlage fehlt)")

    # === ZUSAMMENFASSUNG ===
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)

    if 'yamnet' in results:
        yamnet = results['yamnet']
        print(f"\n🎙️  YAMNet-Klassifikation:")
        print(f"    Klasse:   {yamnet['class']}")
        print(f"    Vertrauen: {yamnet['confidence']:.2%}")

    if 'spektral' in results:
        spektral = results['spektral']
        print(f"\n📊 Spektral-Vergleich:")
        print(f"    Ähnlichkeit: {spektral['similarity']:.1%}")
        print(f"    Status:      {'✓ MATCH' if spektral['match'] else '✗ KEIN MATCH'}")

    print("\n" + "="*60)

    return results


def main():
    # Teste mit der Referenzdatei
    reference_file = r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav'

    print("\n" + "="*70)
    print(" "*15 + "HYBRID-ANALYSE SYSTEM")
    print("="*70)
    print("\nKombiniert YAMNet (vordefiniert) mit Spektral-Vergleich")
    print("Ideal für: Echtzeit-Erkennung + Ähnlichkeitsmatching")

    # Analysiere Referenzdatei
    analyze_audio(reference_file)

    print("\n" + "="*70)
    print("VERWENDUNG IN EIGENEM CODE:")
    print("="*70)
    print("""
from hybrid_analyse import analyze_audio

# Analysiere eine Audio-Datei
results = analyze_audio('path/to/audio.wav')

# Zugriff auf Ergebnisse:
if 'yamnet' in results:
    print(f"YAMNet erkannte: {results['yamnet']['class']}")

if 'spektral' in results:
    if results['spektral']['match']:
        print("Audio ähnelt der Vorlage!")
    """)
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
