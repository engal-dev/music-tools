import sys
import json
import os
import logging
import winsound

sys.path.append('../')
sys.path.append('../common_py_utils')

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Album choice cache
# Il file di cache è derivato dal nome dello script chiamante (sys.argv[0]),
# così ogni batch ha la propria cache indipendente.
# Es: spotify_sync_library.py  →  spotify_sync_library_album_cache.json
# ---------------------------------------------------------------------------

_album_cache = None       # lazy loaded
_album_cache_file = None  # calcolato una volta sola


def _cache_file() -> str:
    global _album_cache_file
    if _album_cache_file is None:
        script = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        _album_cache_file = f"{script}_album_cache.json"
    return _album_cache_file


def _load_album_cache() -> list:
    global _album_cache
    if _album_cache is None:
        path = _cache_file()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _album_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Impossibile leggere la cache degli album ({path}): {e}")
                _album_cache = []
        else:
            _album_cache = []
    return _album_cache


def _save_album_cache() -> None:
    try:
        with open(_cache_file(), 'w', encoding='utf-8') as f:
            json.dump(_album_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Impossibile salvare la cache degli album: {e}")


def _candidates_key(matches: list) -> str:
    """Chiave ordinata dagli album ID unici — indipendente dall'ordine della lista."""
    album_ids = sorted(set(song['album']['id'] for song in matches))
    return "|".join(album_ids)


def _candidates_info(matches: list) -> list:
    """Album unici con id, nome e artista, per editabilità manuale del file JSON."""
    seen: set = set()
    info = []
    for song in matches:
        aid = song['album']['id']
        if aid not in seen:
            seen.add(aid)
            info.append({
                "album_id": aid,
                "album_name": song['album']['name'],
                "artist": ", ".join(a["name"] for a in song["artists"])
            })
    return sorted(info, key=lambda c: c["album_id"])


def _lookup_cache(key: str) -> dict | None:
    for entry in _load_album_cache():
        if entry.get("candidates_key") == key:
            return entry
    return None


def _persist_choice(key: str, info: list, chosen_song) -> None:
    global _album_cache
    cache = _load_album_cache()
    new_cache = [e for e in cache if e.get("candidates_key") != key]
    new_cache.append({
        "candidates_key": key,
        "candidates": info,
        "chosen_album_id": chosen_song['album']['id'] if chosen_song else None,
        "chosen_album_name": chosen_song['album']['name'] if chosen_song else None,
    })
    _album_cache = new_cache
    _save_album_cache()


# ---------------------------------------------------------------------------
# Funzione pubblica — firma invariata (retrocompatibile)
# ---------------------------------------------------------------------------

def choose_song(matches, input_title, input_artist, input_album, song_list_format):

    # Cache attiva solo per spotify_ext (unico formato con album.id)
    cache_key = None
    if song_list_format == "spotify_ext":
        cache_key = _candidates_key(matches)
        cached = _lookup_cache(cache_key)
        if cached is not None:
            chosen_id = cached.get("chosen_album_id")
            chosen_name = cached.get("chosen_album_name", chosen_id)
            if chosen_id is None:
                print(f"\n[Cache] Skip memorizzato per: {input_title} - {input_artist} [{input_album}]")
                logger.info(f"Cache hit: Skip per '{input_title}'")
                return None
            for song in matches:
                if song['album']['id'] == chosen_id:
                    print(f"\n[Cache] Album '{chosen_name}' (scelta memorizzata) per: {input_title} - {input_artist}")
                    logger.info(f"Cache hit: album '{chosen_name}' per '{input_title}'")
                    return song
            # Album in cache non presente tra i candidati attuali → chiedi all'utente
            logger.warning(f"Cache hit ma album '{chosen_id}' non tra i candidati, chiedo all'utente")

    # Nessuna cache valida: chiedi all'utente
    winsound.MessageBeep()

    logger.info("\nMore than one match found with the same score for:")
    logger.info(f"\n\t{input_title} - {input_artist} [{input_album}]")
    logger.info("\nChoose the song:")

    print("\n##################################################")
    print("\nMore than one match found with the same score for:")
    print(f"\n\t{input_title} - {input_artist} [{input_album}]")
    print("\nChoose the song:\n")
    print("0. Skip")

    try:
        for i, song in enumerate(matches, 1):
            if song_list_format == "spotify":
                title = song['name']
                artist = [a["name"] for a in song["artists"]]
                album = song['album']
            elif song_list_format == "spotify_ext":
                title = song['name']
                artist = [a["name"] for a in song["artists"]]
                album = song['album']['name']
            elif song_list_format == "navidrome":
                title = song['title']
                artist = song['artist']
                album = song['album']

            print(f"{i}. {title} - {artist} [{album}]")
            if song.get('path'):
                print(f"\t{song['path']}")
    except Exception as e:
        logger.error(f"Errore durante la stampa delle canzoni: {e}")
        print("Errore durante la stampa delle canzoni. Controlla i log per dettagli.")
        return None

    result = None
    while True:
        try:
            choice = int(input("\nInsert the number of the song to select: "))
            if 1 <= choice <= len(matches):
                logger.info(f"User choice: {choice}")
                result = matches[choice - 1]
                break
            elif choice == 0:
                logger.info("User choice: Skipped")
                result = None
                break
            else:
                print(f"Please insert a number between 1 and {len(matches)}")
        except ValueError:
            print("Please insert a valid number")
        except Exception as e:
            logger.error(f"Errore durante la scelta: {e}")
            print("Errore durante la scelta. Controlla i log per dettagli.")
            return None

    # Salva scelta in cache (solo spotify_ext)
    if cache_key:
        _persist_choice(cache_key, _candidates_info(matches), result)
        logger.info(f"Scelta memorizzata in: {_cache_file()}")

    return result
