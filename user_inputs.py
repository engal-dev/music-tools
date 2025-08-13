import sys
import logging
import winsound

sys.path.append('../')
sys.path.append('../common_py_utils')

logger = logging.getLogger(__name__)

def choose_song(matches, input_title, input_artist, input_album, song_list_format):
    
    # Play a sound
    winsound.MessageBeep()
    
    logger.info("\nMore than one match found with the same score for:")
    logger.info(f"\n\t{input_title} - {input_artist} [{input_album}]")
    logger.info("\nChoose the song:")
    
    print("\n##################################################")
    print("\nMore than one match found with the same score for:")
    print(f"\n\t{input_title} - {input_artist} [{input_album}]")
    print("\nChoose the song:\n")
    print(f"0. Skip")

    try:
        for i, song in enumerate(matches, 1):
            if (song_list_format=="spotify"):
                title = song['name']
                artist = [artist["name"] for artist in song["artists"]]
                album = song['album']
            elif (song_list_format=="spotify_ext"):
                title = song['name']
                artist = [artist["name"] for artist in song["artists"]]
                album = song['album']['name']
            elif (song_list_format=="navidrome"):
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
    
    while True:
        try:
            choice = int(input("\nInsert the number of the song to select: "))
            if 1 <= choice <= len(matches):
                logger.info(f"User choice: {choice}")
                return matches[choice - 1]
            elif choice == 0:
                logger.info("User choice: Skipped")
                return None
            else:
                print(f"Please insert a number between 1 and {len(matches)}")
        except ValueError:
            print("Please insert a valid number")
        except Exception as e:
            logger.error(f"Errore durante la scelta: {e}")
            print("Errore durante la scelta. Controlla i log per dettagli.")
            return None