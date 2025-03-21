import requests
import os
import json
import hashlib
import utility
from dotenv import load_dotenv

# Carica le credenziali dal file .env
load_dotenv()

USERNAME = os.getenv("NAVIDROME_USERNAME")
PASSWORD = os.getenv("NAVIDROME_PASSWORD")
NAVIDROME_URL = os.getenv("NAVIDROME_URL")
CLIENT_ID = os.getenv("NAVIDROME_CLIENT_ID")
API_VERSION = os.getenv("NAVIDROME_API_VERSION")

def authenticate():
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
    """Genera un token per l'autenticazione a Navidrome."""
    salt = "random_salt"
    token = hashlib.md5(f"{password}{salt}".encode("utf-8")).hexdigest()
    return token, salt

def search_song(session, artist, album, title):
    """Cerca esattamente un brano su Navidrome basato su artista, album e titolo."""
    response = session.get(f"{NAVIDROME_URL}/search2.view", params={
        "query": title,
        "f": "json"
    })
    if response.status_code != 200:
        print(f"❌ Errore nella ricerca per {title}: {response.text}")
        return []

    # Filtra i risultati cercando una corrispondenza esatta su artista, album e titolo
    results = response.json().get("subsonic-response", {}).get("searchResult2", {}).get("song", [])
    matches = [
        song for song in results
        if utility.clean_string(song["artist"]) == artist and
           utility.clean_string(utility.album_title_match(song["album"])) == album and
           utility.clean_string(song["title"]) == title
    ]
    return matches

def search_song_no_album(session, artist, title):
    """Cerca esattamente un brano su Navidrome basato su artista e titolo."""
    response = session.get(f"{NAVIDROME_URL}/search2.view", params={
        "query": title,
        "f": "json"
    })
    if response.status_code != 200:
        print(f"❌ Errore nella ricerca per {title}: {response.text}")
        return []

    # Filtra i risultati cercando una corrispondenza esatta su artista, album e titolo
    results = response.json().get("subsonic-response", {}).get("searchResult2", {}).get("song", [])
    matches = [
        song for song in results
        if utility.clean_string(song["artist"]) == artist and
           utility.clean_string(song["title"]) == title
    ]
    return matches

def add_to_favorites(session, navidrome_songs):
    for song in navidrome_songs:
        response = session.get(f"{NAVIDROME_URL}/star.view", params={
            "id": song["id"],
            "f": "json"
        })
        if response.status_code == 200:
            print(f"✅ Brano preferito aggiunto: {song['title']} - {song['artist']} ({song['album']})")
        else:
            print(f"❌ Errore durante l'aggiunta del brano: {song['title']} - {song['artist']}")

def get_playlist_songs(session, playlist_id):
    response = session.get(f"{NAVIDROME_URL}/getPlaylist.view", params={
        "f": "json",
        "id": playlist_id,
    })
    response.raise_for_status()
    return response.json()["subsonic-response"]["playlist"]["entry"]
    
def get_playlists(session):
    response = session.get(f"{NAVIDROME_URL}/getPlaylists.view", params={
        "f": "json",
    })
    if response.status_code != 200:
        print("Errore nella chiamata API:")
        print(response.text)  # Log della risposta
        response.raise_for_status()

    # Stampa per debug
    print("Risposta API getPlaylists.view:")
    print(json.dumps(response.json(), indent=2))

    # Recupera le playlist
    data = response.json()["subsonic-response"]
    if "playlists" not in data:
        raise ValueError("Nessun campo 'playlists' trovato nella risposta API.")
    return data["playlists"]["playlist"]