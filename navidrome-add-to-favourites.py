import json
import utility
import navidrome

# File input
REPORT_DIR = "compare_report"
NOT_FOUND_FILE = "compare_report/songs_not_found.json"
PARTIAL_MATCH_FILE = "partial_matches.log"

def write_partial_matches(file_path, spotify_track, navidrome_tracks, output_dir=None):
    """Scrive i partial match nel file di output."""
    file_path = utility.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "a", encoding="utf-8") as file:
        for navidrome_track in navidrome_tracks:
            file.write(
                f"🎵 Artista: {spotify_track['artists'][0]['name']}\n"
                f"   Album: {spotify_track['album']}\n"
                f"   Titolo: {spotify_track['name']}\n"
                f"   ID: {spotify_track['id']}\n"
                f"   ↔️ Corrispondenze Navidrome:\n"
            )
            for navidrome_track in navidrome_tracks:
                file.write(
                    f"      - Artista: {navidrome_track['artist']}\n"
                    f"        Album: {navidrome_track['album']}\n"
                    f"        Titolo: {navidrome_track['title']}\n"
                    f"        Starred: {navidrome_track.get('starred', 'No')}\n"
                    f"        ID: {navidrome_track['id']}\n"
                    f"        CORRELATION: {spotify_track['id']},{navidrome_track['id']}\n"
                )
        file.write("\n")

def main():
    # Carica i dati
    not_found_songs = utility.load_json_data(NOT_FOUND_FILE)

    # Autenticazione a Navidrome
    session = navidrome.authenticate()

    # Contatori per il riepilogo
    added_to_favorites_count = 0
    partial_matches_count = 0

    # Cerca e aggiorna i preferiti
    for song in not_found_songs:
        spotify_artist = utility.clean_string(song["artists"][0]["name"])
        spotify_album = utility.clean_string(utility.album_title_match(song["album"]))
        spotify_title = utility.clean_string(song["name"])
        
        # Cerca il brano esatto su Navidrome
        matches = navidrome.search_song(session, spotify_artist, spotify_album, spotify_title)

        if matches:
            print(f"Trovati {len(matches)} brani per {spotify_title} - {spotify_artist} ({spotify_album}).")
            navidrome.add_to_favorites(session, matches)
            added_to_favorites_count += len(matches)
            continue

        # Seconda ricerca (senza album)
        partial_matches = navidrome.search_song_no_album(session, spotify_artist, spotify_title)

        if partial_matches:
            print(f"Trovati {len(partial_matches)} POTENZIALI brani per {spotify_title} - {spotify_artist}.")
            write_partial_matches(PARTIAL_MATCH_FILE, song, partial_matches, output_dir=REPORT_DIR)
            partial_matches_count += len(partial_matches)
        else:
            print(f"Nessun brano trovato per {spotify_title} - {spotify_artist} ({spotify_album}).")
    
    # Riepilogo
    print("\n--- Riepilogo ---")
    print(f"Brani aggiunti ai preferiti: {added_to_favorites_count}")
    print(f"Partial match trovati: {partial_matches_count}")

if __name__ == "__main__":
    main()
