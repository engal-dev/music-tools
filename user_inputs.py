import sys
import logging
import winsound

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import string_utils

logger = logging.getLogger(__name__)

def choose_song(matches, input_title, input_artist, input_album):
    
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
    for i, song in enumerate(matches, 1):
        print(f"{i}. {song['title']} - {song['artist']} [{song['album']}]")
        print(f"\t{song['path']}")
    
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