import os
import argparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import sys
import logging
import time
from datetime import datetime, timedelta

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import json_utils, log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.DEBUG)

# Carica le credenziali dal file .env
load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SCOPES = 'playlist-read-private user-library-read'

# Directory per salvare le playlist
OUTPUT_DIR = "spotify-playlists"

def get_all_tracks(sp, playlist_id):
    """Recupera tutte le tracce di una playlist."""
    tracks = []
    results = sp.playlist_items(playlist_id)
    while results:
        for item in results['items']:
            track = item['track']
            if track:  # A volte le tracce possono essere None
                tracks.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [{'id': artist['id'], 'name': artist['name']} for artist in track['artists']],
                    'album-id': track['album']['id'],
                    'album': track['album']['name'],
                    'url': track.get('external_urls', {}).get('spotify', 'URL non disponibile')
                })
        results = sp.next(results)
    return tracks

def get_liked_songs(sp):
    """Recupera i brani preferiti (cuoricini)."""
    tracks = []
    results = sp.current_user_saved_tracks()
    while results:
        for item in results['items']:
            track = item['track']
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artists': [{'id': artist['id'], 'name': artist['name']} for artist in track['artists']],
                'album-id': track['album']['id'],
                'album': track['album']['name'],
                'url': track['external_urls']['spotify']
            })
        results = sp.next(results)
    return tracks

def main():
    parser = argparse.ArgumentParser(description="Esporta playlist Spotify.")
    parser.add_argument('--playlist-ids', nargs='*', help="ID delle playlist da esportare (separati da spazio)")
    args = parser.parse_args()

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=SCOPES))

    if args.playlist_ids:
        # Esporta solo le playlist specificate
        for playlist_id in args.playlist_ids:
            try:
                playlist = sp.playlist(playlist_id)
                playlist_name = playlist.get('name', 'Unnamed Playlist')
                print(f"Elaboro playlist: {playlist_name}")
                tracks = get_all_tracks(sp, playlist_id)
                json_utils.save_to_json_file(tracks, playlist_name+".json", OUTPUT_DIR)
            except Exception as e:
                print(f"Errore durante l'elaborazione della playlist con ID {playlist_id}: {e}")
    else:
        # Esporta tutte le playlist
        print("Recupero tutte le playlist...")
        playlists = sp.current_user_playlists()
        for playlist in playlists['items']:
            if not playlist:
                print("Trovata una playlist non valida, la salto.")
                continue
            playlist_name = playlist.get('name', 'Unnamed Playlist')
            playlist_id = playlist.get('id')
            if not playlist_id:
                print(f"La playlist '{playlist_name}' non ha un ID valido, la salto.")
                continue
            print(f"Elaboro playlist: {playlist_name}")
            tracks = get_all_tracks(sp, playlist_id)
            json_utils.save_to_json_file(tracks, playlist_name+".json", OUTPUT_DIR)
        
        # Recupera i brani preferiti
        print("Recupero brani preferiti...")
        liked_songs = get_liked_songs(sp)
        json_utils.save_to_json_file(liked_songs, "Brani preferiti.json", OUTPUT_DIR)

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
