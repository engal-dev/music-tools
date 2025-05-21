import utility
import sys
import os
import logging
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import file_utils, json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.INFO)

REPORT_DIR = "compare_report"
# File input
NAVIDROME_FILE = "navidrome-playlists/Brani preferiti.json"
SPOTIFY_FILE = "spotify-playlists/Brani preferiti.json"
# File output
FOUND_FILE = "songs_found.json"
NOT_FOUND_FILE = "songs_not_found.json"
PART_MATCH_FILE = "partially_matched.json"
FOUND_LOG_FILE = "songs_found.log"
NOT_FOUND_LOG_FILE = "songs_not_found.log"
NOT_FOUND_DOWNLOAD_FILE = "album_not_found_download.log"
NOT_FOUND_LIST_FILE = "songs_not_found_list.log"
PART_MATCH_LOG_FILE = "partially_matched.log"
VERIFIED_FILE = "verified_songs.json"

def is_verified(song, verified_songs):
    """Controlla se il brano è già verificato."""
    return any(song["id"] == verified["id"] for verified in verified_songs)

def compare_songs(navidrome_songs, spotify_songs, verified_songs, simple_match=True):
    """Confronta i brani tra Navidrome e Spotify."""
    found = []
    partially_matched = []
    not_found = []

    for spotify_song in spotify_songs:
        logger.info(f"Comparing: {spotify_song['name']} - {spotify_song['artists'][0]['name']} - {spotify_song['album']}")
        # Salta i brani già verificati
        if is_verified(spotify_song, verified_songs):
            #print(f'Salto brano già verificato: {spotify_song["artists"][0]["name"]} - {spotify_song["album"]} - {spotify_song["name"]}')
            continue

        spotify_title = spotify_song["name"]
        spotify_artists = [artist["name"] for artist in spotify_song["artists"]]
        spotify_album = utility.album_title_match(spotify_song["album"])

        # Cerca il brano in Navidrome (con album incluso)
        match = None
        for navidrome_song in navidrome_songs:
            # Pulizia dei termini da ignorare
            navidrome_title = navidrome_song["title"]
            navidrome_artist = navidrome_song["artist"]
            navidrome_album = utility.album_title_match(navidrome_song["album"])
            
            founded = utility.match_song(
                    spotify_title, spotify_artists, spotify_album,
                    navidrome_title, navidrome_artist, navidrome_album, simple_match=False)[0]
            
            #TODO: Aggiugnere logica multiMatch

            if founded:
                match = navidrome_song
                break

        if match:
            logger.info("MATCHED!")
            found.append({
                "spotify": spotify_song,
                "navidrome": match
            })
            verified_songs.append(spotify_song)
            continue

        # Seconda verifica (senza album)
        logger.info("No match. Trying without album...")

        partial_match = None
        for navidrome_song in navidrome_songs:
            # Pulizia dei termini da ignorare
            navidrome_title = navidrome_song["title"]
            navidrome_artist = navidrome_song["artist"]
            
            founded = utility.match_song(
                    spotify_title, spotify_artists, spotify_album,
                    navidrome_title, navidrome_artist, navidrome_album,
                    consider_album=False, simple_match=False)[0]
            
            #TODO: Aggiugnere logica multiMatch
            
            if founded:
                partial_match = navidrome_song
                break

        if partial_match:
            logger.info("PARTIALLY MATCHED!")
            partially_matched.append({
                "spotify": spotify_song,
                "navidrome": partial_match
            })
        else:
            logger.info("NOT FOUND!")
            not_found.append(spotify_song)

    return found, partially_matched, not_found, verified_songs

def save_readable_list(data, file_path, found=True, output_dir=None):
    """Salva una lista leggibile dei brani in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            if found:
                spotify_track = entry["spotify"]
                navidrome_track = entry["navidrome"]
                f.write(
                    f"{spotify_track['name']};{' - '.join(artist['name'] for artist in spotify_track['artists'])};{spotify_track['album']}\n"
                    f"{navidrome_track['title']};{navidrome_track['artist']};{navidrome_track['album']}\n\n"
                )
            else:
                f.write(
                    f"Artista: {' - '.join(artist['name'] for artist in entry['artists'])}\n"
                    f"Album: {entry['album']}\n"
                    f"Titolo: {entry['name']}\n\n"
                )

def save_download_album_list(data, file_path, found=False, output_dir=None):
    """Salva una lista scaricabile degli album in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(
                f"/search qobuz album {entry['album']} {entry['artists'][0]['name']}\n"
            )

def save_not_found_list(data, file_path, found=False, output_dir=None):
    """Salva una lista delle canzoni non trovate in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(
                f"{entry['name']}, {entry['artists'][0]['name']}, {entry['album']}\n"
            )

def main():
    # Carica i dati
    navidrome_songs = json_utils.load_json_data(NAVIDROME_FILE)
    spotify_songs = json_utils.load_json_data(SPOTIFY_FILE)
    verified_songs = json_utils.load_json_data(file_utils.append_dir_to_file_name(VERIFIED_FILE, REPORT_DIR), create_if_not_exists=True)

    # Confronta i brani
    found, partially_matched, not_found, verified_songs = compare_songs(navidrome_songs, spotify_songs, verified_songs, False)

    # Salva i report in formato JSON e leggibile
    if found:
        json_utils.save_to_json_file(found, FOUND_FILE, REPORT_DIR, append=True)
        save_readable_list(found, FOUND_LOG_FILE, found=True, output_dir=REPORT_DIR)
    if partially_matched:
        json_utils.save_to_json_file(partially_matched, PART_MATCH_FILE, REPORT_DIR)
        save_readable_list(partially_matched, PART_MATCH_LOG_FILE, found=True, output_dir=REPORT_DIR)
    if not_found:
        json_utils.save_to_json_file(not_found, NOT_FOUND_FILE, REPORT_DIR)
        save_readable_list(not_found, NOT_FOUND_LOG_FILE, found=False, output_dir=REPORT_DIR)
        save_not_found_list(not_found, NOT_FOUND_LIST_FILE, found=False, output_dir=REPORT_DIR)
        save_download_album_list(not_found, NOT_FOUND_DOWNLOAD_FILE, found=False, output_dir=REPORT_DIR)
    if verified_songs:
        json_utils.save_to_json_file(verified_songs, VERIFIED_FILE, REPORT_DIR) #No need to append because the file is read before.

    logger.info(f"{len(found)} brani trovati. Salvati in {FOUND_FILE} e {FOUND_LOG_FILE}.")
    logger.info(f"{len(partially_matched)} brani parzialmente corrispondenti. Salvati in {PART_MATCH_FILE} e {PART_MATCH_LOG_FILE}.")
    logger.info(f"{len(not_found)} brani non trovati. Salvati in {NOT_FOUND_FILE} e {NOT_FOUND_LOG_FILE}.")

if __name__ == "__main__":
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Ora inizio: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    main()

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    # Converti la durata in ore, minuti e secondi
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ Ora fine: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Durata: {hours} ore, {minutes} minuti, {seconds} secondi")