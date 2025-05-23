import utility
import sys
import os
import logging
import navidrome
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import file_utils, json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.INFO)

# File input
REPORT_DIR = "compare_report"
PARTIAL_MATCH_FILE = "adding_partial_matches.log"

def write_partial_matches(file_path, source_track, founded_tracks, input_service, output_dir=None):
    """Scrive i partial match nel file di output."""
    file_path = file_utils.append_dir_to_file_name(file_path, output_dir)

    if (input_service=="spotify"):
        source_id = source_track['id']
        source_title = source_track['name']
        source_artists = [artist["name"] for artist in source_track["artists"]]
        source_album = source_track['album']
    elif (input_service=="navidrome"):
        source_id = source_track['id']
        source_title = source_track['title']
        source_artists = [source_track['artist']]
        source_album = source_track['album']

    with open(file_path, "a", encoding="utf-8") as file:
        for navidrome_track in founded_tracks:
            file.write(
                f"{source_id};{source_title};{' - '.join(artist for artist in source_artists)};{source_album}\n"
                f"Corrispondenze Navidrome:\n"
            )
            for navidrome_track in founded_tracks:
                file.write(
                    f"    {navidrome_track['id']};{navidrome_track['title']};{navidrome_track['artist']};{navidrome_track['album']};Starred:{navidrome_track.get('starred', 'No')}\n"
                    f"CORRELATION: {source_id},{navidrome_track['id']}\n"
                )
        file.write("\n")

def main(source_file_path, input_service):
    logger.info(f"Processing file: {source_file_path} (service={input_service})")

    # Carica i dati
    songs_to_add = json_utils.load_json_data(source_file_path)

    # Autenticazione a Navidrome
    session = navidrome.authenticate()

    # Contatori per il riepilogo
    added_to_favorites_count = 0
    partial_matches_count = 0

    # Cerca e aggiorna i preferiti
    id = None
    for song in songs_to_add:
        if input_service=='spotify':
            artists =[artist["name"] for artist in song["artists"]]
            album = utility.album_title_match(song["album"])
            title = song["name"]
        elif input_service=="navidrome":
            artists = song["artist"]
            album = utility.album_title_match(song["album"])
            title = song["title"]
            id = song["id"]

        logger.info(f"Searching: {title} - {' - '.join(artist for artist in artists)} - {album}")

        # Cerca il brano esatto su Navidrome
        if id:
            try:
                match = [navidrome.get_song_by_id(session, id)]
            except ValueError:
                logger.info("Song not found by ID, trying searching...")
                match = navidrome.search_song(session, artists, album, title)
        else:
            match = navidrome.search_song(session, artists, album, title)

        if match:
            logger.info(f"Trovato brano per {title} - {artists} ({album}).")
            navidrome.add_to_favorites(session, [match])
            added_to_favorites_count += 1
            continue

#        # Seconda ricerca (senza album)
#        partial_matches = navidrome.search_song(session, artists, None, title, consider_album=False)
#
#        if partial_matches:
#            logger.info(f"Trovati {len(partial_matches)} POTENZIALI brani per {title} - {artists}.")
#            write_partial_matches(PARTIAL_MATCH_FILE, song, partial_matches, input_service, output_dir=REPORT_DIR)
#            partial_matches_count += len(partial_matches)
#        else:
#            logger.info(f"Nessun brano trovato per {title} - {artists} ({album}).")
    
    # Riepilogo
    logger.info("\n--- Riepilogo ---")
    logger.info(f"Brani aggiunti ai preferiti: {added_to_favorites_count}")
#    logger.info(f"Partial match trovati: {partial_matches_count}")

if __name__ == "__main__":
    default_source_file = "compare_report/songs_not_found.json"
    source_file_path = input(f"Enter the path to your source file (default: {default_source_file}): ").strip()
    if not source_file_path:
        source_file_path = default_source_file
        logger.info(f"Using default file: {source_file_path}")

    input_service = input("Select source service (Spotify/Navidrome)? ").strip().lower()
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    main(source_file_path, input_service)

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    # Converti la durata in ore, minuti e secondi
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Duration: {hours} hours, {minutes} minutes, {seconds} seconds")