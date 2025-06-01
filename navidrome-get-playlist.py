import navidrome
import os
import sys
import time
import argparse
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__))

def get_playlist_by_name(session, playlists, name):
    """Finds a playlist by name."""
    for playlist in playlists:
        if playlist["name"] == name:
            return playlist
    raise ValueError(f"Playlist '{name}' not found.")

def show_all_playlists(session, playlists):
    """Mostra tutte le playlist disponibili e le salva in file JSON separati."""
    logger.info("Playlist disponibili:")
    for playlist in playlists:
        logger.info(f"- {playlist['name']} (ID: {playlist['id']})")
        
        # Ottieni e salva le canzoni per ogni playlist
        try:
            entries = navidrome.get_playlist_songs(session, playlist["id"])
            logger.info(f"  ↳ {len(entries)} brani trovati")
            json_utils.save_to_json_file(entries, playlist['name']+".json", "navidrome-playlists")
        except Exception as e:
            logger.error(f"  ↳ Errore nel recupero della playlist {playlist['name']}: {e}")

def main():
    # Configurazione degli argomenti da riga di comando
    parser = argparse.ArgumentParser(description='Ottieni le canzoni da una playlist Navidrome')
    parser.add_argument('--playlist', '-p', help='Nome della playlist da recuperare')
    args = parser.parse_args()

    # Authentication
    session = navidrome.authenticate()

    try:
        # Get all playlists
        navidrome_playlists = navidrome.get_playlists(session)
        
        if not args.playlist:
            show_all_playlists(session, navidrome_playlists)
            return

        requested_playlist = get_playlist_by_name(session, navidrome_playlists, args.playlist)
        logger.info(f"Found playlist: {requested_playlist['name']} (ID: {requested_playlist['id']})")

        # Get playlist tracks
        entries = navidrome.get_playlist_songs(session, requested_playlist["id"])
        logger.info(f"{len(entries)} tracks found in playlist.")

        # Save data to file
        json_utils.save_to_json_file(entries, args.playlist+".json", "navidrome-playlists")

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
