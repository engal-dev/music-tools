import sys
import os
import logging
import navidrome
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import file_utils, json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.DEBUG)

def main(source_file_path):
    logger.info(f"Processing file: {source_file_path}")

    # Carica i dati dalla playlist Navidrome
    songs_to_remove = json_utils.load_json_data(source_file_path)

    # Autenticazione a Navidrome
    session = navidrome.authenticate()

    # Contatori per il riepilogo
    removed_from_favorites_count = 0

    # Rimuovi dai preferiti
    for song in songs_to_remove:
        navidrome.remove_from_favorites(session, song['id'])
        removed_from_favorites_count += 1            

    logger.info("\n--- Riepilogo ---")
    logger.info(f"Brani rimossi dai preferiti: {removed_from_favorites_count}")

if __name__ == "__main__":
    default_source_file = "navidrome-playlists/to_remove_from_favourites.json"
    source_file_path = input(f"Enter the path to your file (default: {default_source_file}): ").strip()
    if not source_file_path:
        source_file_path = default_source_file
        logger.info(f"Using default file: {source_file_path}")
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    main(source_file_path)

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    # Converti la durata in ore, minuti e secondi
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Duration: {hours} hours, {minutes} minutes, {seconds} seconds")