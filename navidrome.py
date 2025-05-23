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
