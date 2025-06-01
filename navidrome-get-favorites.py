import navidrome
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import json_utils, log_utils

PLAYLIST_NAME = "Brani preferiti"
logger = log_utils.setup_logging(os.path.basename(__file__))

def get_starred_songs(session):
    """Recupera tutti i brani preferiti."""
    # Ottieni tutti i brani
    starred_songs = navidrome.get_starred(session)
    
    return starred_songs

def main():
    # Authentication
    session = navidrome.authenticate()

    try:
        # Ottieni i brani preferiti
        starred_songs = get_starred_songs(session)
        logger.info(f"Trovati {len(starred_songs)} brani preferiti")

        # Save data to file
        json_utils.save_to_json_file(starred_songs, PLAYLIST_NAME+".json", "navidrome-playlists")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    main()

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    # Converti la durata in ore, minuti e secondi
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Duration: {hours} hours, {minutes} minutes, {seconds} seconds")
