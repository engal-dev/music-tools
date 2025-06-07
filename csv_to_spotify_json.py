import csv
import json
import sys

def csv_to_spotify_json(csv_file):
    spotify_tracks = []
    
    # Definiamo manualmente i nomi delle colonne
    fieldnames = ['title', 'artist', 'album']
    
    print(f"Apertura del file: {csv_file}")
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=';')  # Specifico il separatore punto e virgola
        for i, row in enumerate(csv_reader, 1):
            print(f"Lettura riga {i}: {row}")
            if len(row) >= 3:
                track = {
                    "name": row[0].strip(),  # title
                    "artists": [{"name": row[1].strip()}],  # artist
                    "album": row[2].strip()  # album
                }
                spotify_tracks.append(track)
                print(f"Traccia aggiunta: {track}")
            else:
                print(f"Riga {i} ignorata: numero insufficiente di colonne")
    
    print(f"Numero totale di tracce processate: {len(spotify_tracks)}")
    return spotify_tracks

def main():
    if len(sys.argv) != 2:
        print("Uso: python csv_to_spotify_json.py <file_csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    try:
        spotify_tracks = csv_to_spotify_json(csv_file)
        
        # Salva il risultato in un file JSON
        output_file = csv_file.rsplit('.', 1)[0] + '.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(spotify_tracks, f, indent=2, ensure_ascii=False)
        
        print(f"Conversione completata! Il file JSON è stato salvato come: {output_file}")
    
    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 