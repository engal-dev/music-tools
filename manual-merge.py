import csv
import utility

# File paths
REPORT_DIR = "compare_report"
SONGS_NOT_FOUND_FILE = "partially_matched.json"
VERIFIED_SONGS_FILE = "verified_songs.json"
MATCHES_CSV_FILE = "manual-merge.csv"  # Il tuo file CSV con le corrispondenze

def update_verified_songs(songs_not_found, verified_songs, matches):
    """Aggiungi le corrispondenze verificate al file verified_songs.json."""
    for match in matches:
        spotify_id = match["id_song_spotify"]
        navidrome_id = match["id_song_navidrome"]

        # Cerca la canzone in songs_not_found
        song_to_verify = next((song for song in songs_not_found if song.get("spotify", {}).get("id") == spotify_id), None)

        if song_to_verify:
            print(f"✅ Trovata corrispondenza verificata: Spotify ID {spotify_id}, Navidrome ID {navidrome_id}")
            verified_songs.append(song_to_verify.get("spotify", {}))
        else:
            print(f"⚠️ Spotify ID {spotify_id} non trovato in songs_not_found.")

    return verified_songs

def load_csv_matches(csv_file):
    """Carica le corrispondenze da un file CSV."""
    matches = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, fieldnames=["id_song_spotify", "id_song_navidrome"])
        for row in reader:
            matches.append(row)
    return matches

def main():
    # Carica i file JSON
    songs_not_found = utility.load_json_data(utility.append_dir_to_file_name(SONGS_NOT_FOUND_FILE, REPORT_DIR))
    verified_songs = utility.load_json_data(utility.append_dir_to_file_name(VERIFIED_SONGS_FILE, REPORT_DIR))

    # Carica le corrispondenze dal CSV
    matches = load_csv_matches(utility.append_dir_to_file_name(MATCHES_CSV_FILE, REPORT_DIR))

    # Aggiorna il file verified_songs.json
    updated_verified_songs = update_verified_songs(songs_not_found, verified_songs, matches)
    utility.save_to_json_file(updated_verified_songs, VERIFIED_SONGS_FILE, REPORT_DIR, append=False)

    print(f"Aggiornato il file {VERIFIED_SONGS_FILE} con {len(matches)} corrispondenze.")

if __name__ == "__main__":
    main()
