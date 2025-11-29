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

REPORT_DIR = "compare_report/csv"
# File input
NAVIDROME_FILE = "navidrome-playlists/Brani preferiti.json"
# File output
FOUND_FILE = "songs_found.json"
NOT_FOUND_FILE = "songs_not_found.json"
PART_MATCH_FILE = "partially_matched.json"
FOUND_LOG_FILE = "songs_found.log"
NOT_FOUND_LOG_FILE = "songs_not_found.log"
NOT_FOUND_DOWNLOAD_FILE = "album_not_found_download.log"
NOT_FOUND_LIST_FILE = "songs_not_found_list.log"
PART_MATCH_LOG_FILE = "partially_matched.log"
VERIFIED_FILE = "verified_songs.csv"

def is_verified(song, verified_songs):
    """Controlla se il brano è già verificato confrontando i primi tre campi del CSV."""
    return any(
        song[0] == verified[0] and 
        song[1] == verified[1] and 
        song[2] == verified[2] 
        for verified in verified_songs
    )

def compare_songs(navidrome_songs, csv_songs, verified_songs, simple_match=True):
    """Confronta i brani tra Navidrome e CSV."""
    found = []
    partially_matched = []
    not_found = []

    for source_song in csv_songs:
        # Salta i brani già verificati
        if is_verified(source_song, verified_songs):
            #print(f'Salto brano già verificato: {spotify_song["artists"][0]["name"]} - {spotify_song["album"]} - {spotify_song["name"]}')
            continue

        logger.info(f"Comparing: {source_song[0]} - {source_song[1]} - {source_song[2]}")

        source_title = source_song[0]
        source_artists = [source_song[1]]
        source_album = source_song[2]

        # Search in Navidrome (including album)
        match = utility.find_song(source_title, source_artists, source_album, navidrome_songs, "navidrome", only_first_result=False, permit_choice=True, consider_album=True)

        if match:
            logger.info("MATCHED!")
            found.append({
                "source": source_song,
                "navidrome": match
            })
            verified_songs.append(source_song)
            continue

        # Second search (without album)
        logger.info("No match. Trying without album...")

        partial_match = utility.find_song(source_title, source_artists, source_album, navidrome_songs, "navidrome", only_first_result=False, permit_choice=True, consider_album=False)
        
        if partial_match:
            logger.info("PARTIALLY MATCHED!")
            partially_matched.append({
                "source": source_song,
                "navidrome": partial_match
            })
        else:
            logger.info("NOT FOUND!")
            not_found.append(source_song)

    return found, partially_matched, not_found, verified_songs

def save_readable_list(data, file_path, found=True, output_dir=None):
    """Salva una lista leggibile dei brani in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            if found:
                source_track = entry["source"]
                navidrome_track = entry["navidrome"]
                f.write(
                    f"{source_track[0]};{source_track[1]};{source_track[2]}\n"
                    f"{navidrome_track['title']};{navidrome_track['artist']};{navidrome_track['album']}\n\n"
                )
            else:
                f.write(
                    f"Titolo: {entry[0]}\n"
                    f"Artista: {entry[1]}\n"
                    f"Album: {entry[2]}\n\n"
                )

def save_download_album_list(data, file_path, found=False, output_dir=None):
    """Salva una lista scaricabile degli album in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(
                f"/search qobuz album {entry[2]} {entry[1]}\n"
            )

def save_not_found_list(data, file_path, found=False, output_dir=None):
    """Salva una lista delle canzoni non trovate in un file di testo."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(
                f"{entry[0]}, {entry[1]}, {entry[2]}\n"
            )

def main():
    # Carica i dati
    navidrome_songs = json_utils.load_json_data(NAVIDROME_FILE)
    csv_songs = json_utils.load_json_data(CSV_FILE)
    verified_songs = json_utils.load_json_data(file_utils.append_dir_to_file_name(VERIFIED_FILE, REPORT_DIR), create_if_not_exists=True)

    # Confronta i brani
    found, partially_matched, not_found, verified_songs = compare_songs(navidrome_songs, csv_songs, verified_songs, False)

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

    logger.info(f"{len(found)} songs found. Saved in {FOUND_FILE} e {FOUND_LOG_FILE}.")
    logger.info(f"{len(partially_matched)} partial match songs. Saved in {PART_MATCH_FILE} e {PART_MATCH_LOG_FILE}.")
    logger.info(f"{len(not_found)} songs not found. Saved in {NOT_FOUND_FILE} e {NOT_FOUND_LOG_FILE}.")

if __name__ == "__main__":
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    main()

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Duration: {hours} hours, {minutes} minutes, {seconds} seconds")