import requests
import os
import json
import hashlib
import utility
from dotenv import load_dotenv
import sys
import logging
import user_inputs

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import string_utils

logger = logging.getLogger(__name__)

# Load credentials from .env file
load_dotenv()

USERNAME = os.getenv("NAVIDROME_USERNAME")
PASSWORD = os.getenv("NAVIDROME_PASSWORD")
NAVIDROME_URL = os.getenv("NAVIDROME_URL")
CLIENT_ID = os.getenv("NAVIDROME_CLIENT_ID")
API_VERSION = os.getenv("NAVIDROME_API_VERSION")

def authenticate():
    """Authenticates and returns a session object."""
    token, salt = generate_token(PASSWORD)
    session = requests.Session()
    session.params = {
        "u": USERNAME,
        "t": token,
        "s": salt,
        "v": API_VERSION,
        "c": CLIENT_ID
    }
    session.verify=True #SSL verification
    return session

def generate_token(password):
    """Generates a token for authentication."""
    salt = "random_salt"
    token = hashlib.md5(f"{password}{salt}".encode("utf-8")).hexdigest()
    return token, salt

def search_song(session, artist, album, title, consider_album=True, only_one_result=False, permit_choice=True):
    """Searches for an exact song match in Navidrome based on artist, album and title."""
    response = session.get(f"{NAVIDROME_URL}/search2.view", params={
        "query": string_utils.clean_string(title),
        "songCount": 1000,
        "f": "json"
    })
    
    logger.debug(response.text)
    #logger.debug(json.dumps(response.json(), indent=2))

    if response.status_code != 200:
        logger.error(f"Error searching for {title}: {response.text}")
        return []

    # Filter results looking for an exact match on artist, album and title
    results = response.json().get("subsonic-response", {}).get("searchResult2", {}).get("song", [])

    return utility.find_song(title, artist, album, results, "navidrome", only_first_result=False, permit_choice=True, consider_album=consider_album)

def add_to_favorites(session, navidrome_songs):
    """Adds songs to favorites in Navidrome."""
    for song in navidrome_songs:
        starred = song.get('starred', 'No')
        if (starred=="No"):
            response = session.get(f"{NAVIDROME_URL}/star.view", params={
                "id": song["id"],
                "f": "json"
            })
            if response.status_code == 200:
                logger.info(f"✅ Song added to favorites: {song['title']} - {song['artist']} ({song['album']})")
            else:
                logger.error(f"❌ Error adding song: {song['title']} - {song['artist']}")
        else:
            logger.info(f"Song already favorite: {song['title']} - {song['artist']} ({song['album']})")

def get_playlist_songs(session, playlist_id):
    """Retrieves the songs from a specific playlist."""
    response = session.get(f"{NAVIDROME_URL}/getPlaylist.view", params={
        "f": "json",
        "id": playlist_id,
    })
    response.raise_for_status()
    return response.json()["subsonic-response"]["playlist"]["entry"]
    
def get_playlists(session):
    """Retrieves all playlists from Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/getPlaylists.view", params={
        "f": "json",
    })

    logger.debug(response.text)

    if response.status_code != 200:
        logger.error("API call error:")
        response.raise_for_status()

    logger.debug("API response getPlaylists.view:")
    logger.debug(json.dumps(response.json(), indent=2))

    # Get playlists
    data = response.json()["subsonic-response"]
    if "playlists" not in data:
        raise ValueError("No 'playlists' field found in API response.")
    return data["playlists"]["playlist"]

def get_artists(session):
    """Retrieves all artists from Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/getArtists.view", params={
        "f": "json",
    })

    logger.debug(response.text)

    if response.status_code != 200:
        logger.error("API call error:")
        response.raise_for_status()

    logger.debug("API response getArtists.view:")
    logger.debug(json.dumps(response.json(), indent=2))

    # Get artists
    data = response.json()["subsonic-response"]
    if "artists" not in data:
        raise ValueError("No 'artists' field found in API response.")
    return data["artists"]["index"]

def get_artist_info(session, artistId):
    """Retrieves artist info from Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/getArtistInfo.view", params={
        "f": "json",
        "id": artistId,
    })

    logger.debug(response.text)

    if response.status_code != 200:
        logger.error("API call error:")
        response.raise_for_status()

    logger.debug("API response getArtists.view:")
    logger.debug(json.dumps(response.json(), indent=2))

    # Get artistInfo
    data = response.json()["subsonic-response"]
    if "artistInfo" not in data:
        raise ValueError("No 'artistsInfo' field found in API response.")
    return data["artistInfo"]

def get_song_by_id(session, songId):
    """Retrieves song from Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/getSong.view", params={
        "f": "json",
        "id": songId,
    })

    logger.debug(response.text)

    if response.status_code != 200:
        logger.error("API call error:")
        response.raise_for_status()

    logger.debug("API response getSong.view:")
    logger.debug(json.dumps(response.json(), indent=2))

    # Get songInfo
    data = response.json()["subsonic-response"]
    if "song" not in data:
        raise ValueError("No 'song' field found in API response.")
    return data["song"]

def remove_from_favorites(session, id):
    """Remove song from favorites in Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/unstar.view", params={
        "id": id,
        "f": "json"
    })

    if response.status_code == 200:
        logger.info(f"✅ Song removed from favorites: {id})")
    else:
        logger.error(f"❌ Error unstarring song: {id}")

def get_starred(session):
    """Retrieves all starred songs from Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/getStarred2.view", params={
        "f": "json",
    })

    logger.debug(response.text)

    if response.status_code != 200:
        logger.error("API call error:")
        response.raise_for_status()

    logger.debug("API response getStarred2.view:")
    logger.debug(json.dumps(response.json(), indent=2))

    # Get starred songs
    data = response.json()["subsonic-response"]
    if "starred2" not in data:
        raise ValueError("No 'starred2' field found in API response.")
    return data["starred2"]["song"]

def get_all_songs(session):
    """Retrieves all songs from Navidrome using search2 with pagination."""
    all_songs = []
    offset = 0
    batch_size = 500
    
    logger.info("Recupero tutti i brani da Navidrome...")
    
    while True:
        try:
            response = session.get(f"{NAVIDROME_URL}/search2.view", params={
                "query": "",  # Query vuota per ottenere tutti i brani
                "songOffset": offset,
                "songCount": batch_size,
                "albumOffset": 0,
                "albumCount": 0,
                "artistOffset": 0,
                "artistCount": 0,
                "f": "json"
            })
            
            if response.status_code != 200:
                logger.error(f"Errore API search2: {response.text}")
                break
                
            data = response.json().get("subsonic-response", {})
            search_result = data.get("searchResult2", {})
            songs = search_result.get("song", [])
            
            if not songs:
                break  # Nessun altro brano da recuperare
                
            all_songs.extend(songs)
            offset += batch_size
            
            # logger.debug(f"{songs}")
            logger.debug(f"Recuperati {len(all_songs)} brani finora...")
            
            # Pausa per non sovraccaricare il server
            import time
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Errore durante recupero brani: {e}")
            break
    
    logger.info(f"Recuperati {len(all_songs)} brani totali da Navidrome")
    return all_songs

def set_song_rating(session, song_id, rating):
    """Sets the rating for a song in Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/setRating.view", params={
        "id": song_id,
        "rating": rating,
        "f": "json"
    })
    
    if response.status_code == 200:
        logger.debug(f"✅ Rating set successfully for song {song_id}: {rating} stars")
        return True
    else:
        logger.error(f"❌ Error setting rating for song {song_id}: {response.text}")
        return False

def create_playlist(session, name):
    """Creates a new playlist in Navidrome."""
    response = session.get(f"{NAVIDROME_URL}/createPlaylist.view", params={
        "name": name,
        "f": "json"
    })
    
    if response.status_code == 200:
        playlist_data = response.json().get("subsonic-response", {}).get("playlist", {})
        playlist_id = playlist_data.get("id")
        logger.info(f"✅ Playlist created successfully: {name} (ID: {playlist_id})")
        return playlist_id
    else:
        logger.error(f"❌ Error creating playlist {name}: {response.text}")
        return None

def add_songs_to_playlist(session, playlist_id, song_ids):
    """Adds songs to an existing playlist in Navidrome."""
    if not song_ids:
        logger.warning("No song IDs provided to add to playlist")
        return False
    
    # Convert song_ids to list if it's a single ID
    if isinstance(song_ids, str):
        song_ids = [song_ids]
    
    params = {
        "playlistId": playlist_id,
        "f": "json"
    }
    
    # Add each song ID as a separate parameter
    for i, song_id in enumerate(song_ids):
        params[f"songIdToAdd"] = song_id if i == 0 else params.get("songIdToAdd", []) + [song_id]
    
    # Handle multiple song IDs properly
    if len(song_ids) == 1:
        params["songIdToAdd"] = song_ids[0]
    else:
        # For multiple songs, we need to make multiple calls or use a different approach
        # Let's make individual calls for each song to be safe
        success_count = 0
        for song_id in song_ids:
            single_params = {
                "playlistId": playlist_id,
                "songIdToAdd": song_id,
                "f": "json"
            }
            response = session.get(f"{NAVIDROME_URL}/updatePlaylist.view", params=single_params)
            
            if response.status_code == 200:
                success_count += 1
                logger.debug(f"✅ Song {song_id} added to playlist {playlist_id}")
            else:
                logger.error(f"❌ Error adding song {song_id} to playlist: {response.text}")
        
        logger.info(f"Added {success_count}/{len(song_ids)} songs to playlist {playlist_id}")
        return success_count == len(song_ids)
    
    # Single song case
    response = session.get(f"{NAVIDROME_URL}/updatePlaylist.view", params=params)
    
    if response.status_code == 200:
        logger.info(f"✅ Song(s) added to playlist {playlist_id}")
        return True
    else:
        logger.error(f"❌ Error adding songs to playlist: {response.text}")
        return False

def find_or_create_playlist(session, name):
    """Finds an existing playlist by name or creates a new one."""
    try:
        playlists = get_playlists(session)
        
        # Look for existing playlist with the same name
        for playlist in playlists:
            if playlist.get("name") == name:
                logger.info(f"Found existing playlist: {name} (ID: {playlist['id']})")
                return playlist["id"]
        
        # Playlist doesn't exist, create it
        logger.info(f"Playlist '{name}' not found, creating new one...")
        return create_playlist(session, name)
        
    except Exception as e:
        logger.error(f"Error finding/creating playlist {name}: {e}")
        return None
