import navidrome
import os
import sys
import requests
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__))

def get_artists_image(session, artists):
    """Request artists image."""
    for artist_index in artists:
        for artist in artist_index['artist']:
            logger.info(f'Refresh {artist["name"]} ...')
            logger.debug(artist["artistImageUrl"])
            r = requests.get(artist["artistImageUrl"])
            if r.status_code != 200:
                print(f'{artist["name"]} image => error: {r.content.decode("utf-8")}')
            else:
                print(f'{artist["name"]} image OK!')
            
            artistInfo = navidrome.get_artist_info(session, artist["id"])
            logger.debug(artistInfo)
            print(f'{artist["name"]} data OK!')

def main():
    # Authentication
    session = navidrome.authenticate()

    try:
        # Get all playlists
        navidrome_artists = navidrome.get_artists(session)
        get_artists_image(session, navidrome_artists)
        
    except Exception as e:
        logger.error(f"Error: {e}")

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
