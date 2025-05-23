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

def get_playlist_by_name(session, playlists, name):
    """Finds a playlist by name."""
    for playlist in playlists:
        if playlist["name"] == name:
            return playlist
    raise ValueError(f"Playlist '{name}' not found.")

def main():
    # Authentication
    session = navidrome.authenticate()

    try:
        # Get all playlists
        navidrome_playlists = navidrome.get_playlists(session)
        requested_playlist = get_playlist_by_name(session, navidrome_playlists, PLAYLIST_NAME)
        logger.info(f"Found playlist: {requested_playlist['name']} (ID: {requested_playlist['id']})")

        # Get playlist tracks
        entries = navidrome.get_playlist_songs(session, requested_playlist["id"])
        logger.info(f"{len(entries)} tracks found in playlist.")

        # Save data to file
        json_utils.save_to_json_file(entries, PLAYLIST_NAME+".json", "navidrome-playlists")

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
