import utility

# File input/output
NAVIDROME_FILE = "navidrome-playlists/Brani preferiti.json"
###SPOTIFY_FILE = "spotify.json"
SPOTIFY_FILE = "spotify-playlists/Brani preferiti.json"
REPORT_DIR = "compare_report"
FOUND_FILE = "songs_found.json"
NOT_FOUND_FILE = "songs_not_found.json"
PART_MATCH_FILE = "partially_matched.json"
FOUND_LOG_FILE = "songs_found.log"
NOT_FOUND_LOG_FILE = "songs_not_found.log"
PART_MATCH_LOG_FILE = "partially_matched.log"
VERIFIED_FILE = "verified_songs.json"

def is_verified(song, verified_songs):
    """Controlla se il brano è già verificato."""
    return any(song["id"] == verified["id"] for verified in verified_songs)

def compare_songs(navidrome_songs, spotify_songs, verified_songs):
    """Confronta i brani tra Navidrome e Spotify."""
    found = []
    partially_matched = []
    not_found = []

    for spotify_song in spotify_songs:
        # Salta i brani già verificati
        if is_verified(spotify_song, verified_songs):
            print(f'Salto brano già verificato: {spotify_song["artists"][0]["name"]} - {spotify_song["album"]} - {spotify_song["name"]}')
            continue

        # Pulizia dei termini da ignorare
        spotify_title = utility.clean_string(spotify_song["name"])
        spotify_artist = utility.clean_string(spotify_song["artists"][0]["name"])
        spotify_album = utility.clean_string(spotify_song["album"])

        # Cerca il brano in Navidrome (con album incluso)
        match = next(
            (
                navidrome_song
                for navidrome_song in navidrome_songs
                if spotify_title == utility.clean_string(navidrome_song["title"])
                and spotify_artist == utility.clean_string(navidrome_song["artist"])
                and spotify_album == utility.clean_string(navidrome_song["album"])
            ),
            None,
        )

        if match:
            found.append({
                "spotify": spotify_song,
                "navidrome": match
            })
            verified_songs.append(spotify_song)
            continue

        # Seconda verifica (senza album)
        partial_match = next(
            (
                navidrome_song
                for navidrome_song in navidrome_songs
                if spotify_title == utility.clean_string(navidrome_song["title"])
                and spotify_artist == utility.clean_string(navidrome_song["artist"])
            ),
            None,
        )

        if partial_match:
            partially_matched.append({
                "spotify": spotify_song,
                "navidrome": partial_match
            })
        else:
            not_found.append(spotify_song)

    return found, partially_matched, not_found, verified_songs

def save_readable_list(data, file_path, found=True, output_dir=None):
    """Salva una lista leggibile dei brani in un file di testo."""
    file_path = utility.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            if found:
                spotify_track = entry["spotify"]
                navidrome_track = entry["navidrome"]
                f.write(
                    f"🎵 Artista: {spotify_track['artists'][0]['name']}\n"
                    f"   Album: {spotify_track['album']}\n"
                    f"   Titolo: {spotify_track['name']}\n"
                    f"   ID: {spotify_track['id']}\n"
                    f"   ↔️ Navidrome corrispondente:\n"
                    f"      Artista: {navidrome_track['artist']}\n"
                    f"      Album: {navidrome_track['album']}\n"
                    f"      Titolo: {navidrome_track['title']}\n"
                    f"      Starred: {navidrome_track['starred']}\n\n"
                )
            else:
                f.write(
                    f"❌ Artista: {entry['artists'][0]['name']}\n"
                    f"   Album: {entry['album']}\n"
                    f"   Titolo: {entry['name']}\n\n"
                )

def main():
    # Carica i dati
    navidrome_songs = utility.load_json_data(NAVIDROME_FILE)
    spotify_songs = utility.load_json_data(SPOTIFY_FILE)
    verified_songs = utility.load_json_data(utility.append_dir_to_file_name(VERIFIED_FILE, REPORT_DIR))

    # Confronta i brani
    found, partially_matched, not_found, verified_songs = compare_songs(navidrome_songs, spotify_songs, verified_songs)

    # Salva i report in formato JSON e leggibile
    if found:
        utility.save_to_json_file(found, FOUND_FILE, REPORT_DIR, append=True)
        save_readable_list(found, FOUND_LOG_FILE, found=True, output_dir=REPORT_DIR)
    if partially_matched:
        utility.save_to_json_file(partially_matched, PART_MATCH_FILE, REPORT_DIR)
        save_readable_list(partially_matched, PART_MATCH_LOG_FILE, found=True, output_dir=REPORT_DIR)
    if not_found:
        utility.save_to_json_file(not_found, NOT_FOUND_FILE, REPORT_DIR)
        save_readable_list(not_found, NOT_FOUND_LOG_FILE, found=False, output_dir=REPORT_DIR)
    if verified_songs:
        utility.save_to_json_file(verified_songs, VERIFIED_FILE, REPORT_DIR) #No need to append because the file is read before.

    print(f"{len(found)} brani trovati. Salvati in {FOUND_FILE} e {FOUND_LOG_FILE}.")
    print(f"{len(partially_matched)} brani parzialmente corrispondenti. Salvati in {PART_MATCH_FILE} e {PART_MATCH_LOG_FILE}.")
    print(f"{len(not_found)} brani non trovati. Salvati in {NOT_FOUND_FILE} e {NOT_FOUND_LOG_FILE}.")

if __name__ == "__main__":
    main()
