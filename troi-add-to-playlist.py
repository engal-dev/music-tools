#!/usr/bin/env python3
"""
Script to add tracks from TROI unresolved file to a Navidrome playlist.
Reads track data from unresolved file and adds found tracks to "Discover New" playlist.
"""

import sys
import os
import logging
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

import utility
import navidrome
import troi_utils

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.DEBUG)

# Default playlist name
DEFAULT_PLAYLIST_NAME = "Discover New"


def main(input_file, playlist_name=None):
    """
    Process unresolved file and add tracks to Navidrome playlist.
    
    Args:
        input_file (str): Path to unresolved input file
        playlist_name (str): Name of playlist to create/update
    """
    if playlist_name is None:
        playlist_name = DEFAULT_PLAYLIST_NAME
        
    logger.info(f"Processing file: {input_file}")
    logger.info(f"Target playlist: {playlist_name}")

    # Parse the unresolved file to get tracks
    try:
        tracks = troi_utils.get_all_tracks(input_file)
        logger.info(f"Found {len(tracks)} tracks to process")
    except Exception as e:
        logger.error(f"Error parsing input file: {e}")
        return False

    # Authenticate to Navidrome
    session = navidrome.authenticate()
    
    # Find or create the playlist
    playlist_id = navidrome.find_or_create_playlist(session, playlist_name)
    if not playlist_id:
        logger.error(f"Could not find or create playlist '{playlist_name}'")
        return False

    # Counters for the summary
    found_count = 0
    added_count = 0
    not_found_count = 0
    songs_to_add = []

    # Search for each track
    for i, track in enumerate(tracks, 1):
        title = track["title"]
        album = utility.album_title_match(track["album"])
        artist = track["artist"]
        
        logger.info(f"[{i}/{len(tracks)}] Searching: {title} - {artist} - {album}")

        # Search the song in Navidrome
        try:
            # Convert artist to list format if it's a string
            if isinstance(artist, str):
                artists = [artist]
            else:
                artists = artist
                
            match = navidrome.search_song(session, artists, album, title)
            
            if match:
                logger.info(f"✅ Found: {title} - {artist} ({album})")
                found_count += 1
                songs_to_add.append(match["id"])
                
                # Add songs in batches to avoid too many API calls
                if len(songs_to_add) >= 10:
                    success = navidrome.add_songs_to_playlist(session, playlist_id, songs_to_add)
                    if success:
                        added_count += len(songs_to_add)
                    songs_to_add = []
            else:
                logger.info(f"❌ Not found: {title} - {artist} ({album})")
                not_found_count += 1
                
        except Exception as e:
            logger.error(f"Error searching for {title} - {artist}: {e}")
            not_found_count += 1
    
    # Add remaining songs
    if songs_to_add:
        success = navidrome.add_songs_to_playlist(session, playlist_id, songs_to_add)
        if success:
            added_count += len(songs_to_add)

    # Summary
    logger.info("\n" + "="*50)
    logger.info("SUMMARY")
    logger.info("="*50)
    logger.info(f"Total tracks processed: {len(tracks)}")
    logger.info(f"Found in Navidrome: {found_count}")
    logger.info(f"Not found: {not_found_count}")
    logger.info(f"Added to playlist '{playlist_name}': {added_count}")
    logger.info(f"Success rate: {(found_count/len(tracks)*100):.1f}%")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add tracks from TROI unresolved file to Navidrome playlist"
    )
    parser.add_argument(
        "input_file",
        help="Path to TROI unresolved file"
    )
    parser.add_argument(
        "-p", "--playlist",
        default=DEFAULT_PLAYLIST_NAME,
        help=f"Name of playlist to create/update (default: {DEFAULT_PLAYLIST_NAME})"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    start_time = time.time()
    start_datetime = datetime.now()
    
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    success = main(args.input_file, args.playlist)

    end_time = time.time()
    end_datetime = datetime.now()
    duration = timedelta(seconds=int(end_time - start_time))
    
    # Convert duration to hours, minutes and seconds
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    
    logger.info(f"✅ End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⏱️ Duration: {hours} hours, {minutes} minutes, {seconds} seconds")
    
    sys.exit(0 if success else 1)