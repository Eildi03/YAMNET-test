"""
Testet neue Audio-Dateien gegen die gespeicherte Vorlage
"""

from spektral_vergleich import SpektralVergleicher, SIMILARITY_THRESHOLD
import os

def main():
    print("\n" + "="*60)
    print("AUDIO-VERGLEICH TESTER")
    print("="*60)

    vergleicher = SpektralVergleicher()

    # Lade gespeicherte Vorlage
    print("\nLade Vorlage...")
    if not vergleicher.load_template():
        print("✗ Vorlage konnte nicht geladen werden")
        return

    # Definiere Test-Dateien (anpassen nach Bedarf)
    test_files = [
        r'd:\OneDrive\EildiConsult\YAMNet-test\wav\AUDIO-2026-09-29-02-04-15.wav',  # Selbstvergleich
        # Hier weitere Test-Dateien hinzufügen:
        # r'path/to/test1.wav',
        # r'path/to/test2.wav',
    ]

    print("\n" + "-"*60)
    print("VERGLEICHE DATEIEN")
    print("-"*60)

    results = []

    for i, file_path in enumerate(test_files, 1):
        if not os.path.exists(file_path):
            print(f"\n[{i}] ✗ Datei nicht gefunden: {os.path.basename(file_path)}")
            continue

        print(f"\n[{i}] {os.path.basename(file_path)}")

        # Vergleiche mit DTW (besser für zeitliche Unterschiede)
        result = vergleicher.compare_audio(file_path, method='dtw')

        if result:
            results.append(result)

            # Formatiere Output
            match_symbol = "✓" if result['match'] else "✗"
            print(f"    Ähnlichkeit: {result['similarity']:6.1%}  {match_symbol}")
            print(f"    Schwelle:    {result['threshold']:.0%}")
            print(f"    Status:      {'MATCH' if result['match'] else 'KEIN MATCH'}")

    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)

    if results:
        matches = sum(1 for r in results if r['match'])
        total = len(results)
        print(f"\nMatches: {matches}/{total}")
        print(f"Schwelle: {SIMILARITY_THRESHOLD:.0%}")

        print("\nDetaillierte Ergebnisse:")
        for r in results:
            status = "✓ MATCH" if r['match'] else "✗ KEIN"
            print(f"  {r['filename']:40s} | {r['similarity']:6.1%} | {status}")
    else:
        print("Keine gültigen Dateien zum Vergleichen")

    print("\n" + "="*60)
    print("\nTIPPS:")
    print("  1. Um neue Dateien zu testen, zur test_files-Liste hinzufügen")
    print("  2. Schwelle anpassen: SIMILARITY_THRESHOLD in spektral_vergleich.py")
    print("  3. Methoden: 'dtw' (flexibel) oder 'cosine' (schnell)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
