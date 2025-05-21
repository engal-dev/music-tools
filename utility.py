import re
import sys
import logging
import os

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import string_utils

logger = logging.getLogger(__name__)

# Terms to ignore
IGNORE_TERMS = [
    r"\[Remastered Version\]",
    r"\[Remastered\]",
    r"\[2011 - Remaster\]",
    r"\(2009 Remaster\)",
    r"\(Remaster 2019\)",
    r"\(Bonus Version\)",
    r"\(Full Moon Edition\)",
    r"\(Deluxe Edition Remastered\)",
    r"\(Deluxe Remastered Edition\)",
    r"\(Special Super Deluxe Box\)",
    r"\(2011 Remastered Version\)",
    r"\(Deluxe Edition\)",
    r"\(2015 stereo mix\)",
    r"\(Deluxe Version\)",
    r"\(Deluxe Album\)",
    r"\(Deluxe\)",
    r"\(Super Deluxe Edition\)",
    r"\(20th Anniversary Remaster\)",
    r"\(30th Anniversary / Deluxe Edition\)",
    r"\(40th Anniversary Deluxe Edition\)",
    r"\(Remastered 1996\)",
    r"\(Prospekt's March Edition\)",
    r"\(Expanded Edition\)",
    r"\(Remastered\)",
    r"- Remastered",
    r"- Live @ San Siro 2015",
    r"- Live",
    r"- edit vrs",
    r"- 2011 Remastered Version",
    r"- Remastered 2020 in 192 KHz",
    r"- Remastered 1996",
    r"- Remastered 2019",
    r"- Remastered 2006",
    r"- 20th Anniversary Remaster",
    r"- Mono / Remastered",
    r"- EP",
    r"EP",
    r"E.P.",
    r": Deluxe Edition",
    r"or Death and All His Friends",
    r"\(Prospekt's March Edition\)",
    r"\(Live\)",
    r" - With Elisa"
]


def clean_string(input_string):
    """Remove terms to ignore, extra spaces and convert in lowercase."""

    # Sostituzione di caratteri specifici
    input_string = input_string.replace("’", "'")
    input_string = input_string.replace("×", "x")
    input_string = input_string.replace("·", "")
    input_string = input_string.replace("‐", "-")
    input_string = input_string.replace("…", "...")
    input_string = input_string.replace(" / ", "/")
    input_string = input_string.replace("A'", "à")
    input_string = input_string.replace("E'", "è")
    input_string = input_string.replace("I'", "ì")
    input_string = input_string.replace("O'", "ò")
    input_string = input_string.replace("U'", "ù")
    input_string = input_string.replace("Sansiro", "San siro")
    input_string = input_string.replace(" - ", "-")
    input_string = input_string.replace("I RIO", "Rio")
    
    input_string = input_string.strip().lower()
    
    for term in IGNORE_TERMS:
        input_string = re.sub(term, "", input_string, flags=re.IGNORECASE)
    return input_string.strip()

def album_title_match(input_string):
    """Manual match for irregoular album title."""
    input_string = input_string.replace("Greatest Hits Volume One - The Singles", "Greatest Hits, Volume One: The Singles")
    return input_string

def match_song_weighed(title1, artistList1, album1, title2, artistList2, album2, 
                       title_weight=0.6, artist_weight=0.3, album_weight=0.1, 
                       threshold=0.85, consider_album=True):
    """
    Confronta metadati completi di canzoni
    """
    # Confronta i titoli
    _, title_score = string_utils.are_strings_similar(title1, title2)
    
    # Assicurati che artistList1 e artistList2 siano liste
    if isinstance(artistList1, str):
        artistList1 = [artistList1]
    if isinstance(artistList2, str):
        artistList2 = [artistList2]
    
    # Calcola il punteggio per gli artisti
    artist_scores = [string_utils.are_strings_similar(artist1, artist2)[1] for artist1 in artistList1 for artist2 in artistList2]
    artist_score = max(artist_scores) if artist_scores else 0  # Usa il punteggio massimo tra gli artisti
    
    # Confronta gli album solo se considerato
    album_score = 0
    if consider_album:
        _, album_score = string_utils.are_strings_similar(album1, album2)
    
    # Calcola punteggio pesato
    score = (
        title_score * title_weight + 
        artist_score * artist_weight + 
        album_score * album_weight
    )
    
    matched = score >= threshold

    if matched:
        logger.info(f"score:{score} [title_score:{title_score};artist_score:{artist_score};album_score:{album_score}]")
    else:
        logger.debug(f"score:{score} [title_score:{title_score};artist_score:{artist_score};album_score:{album_score}]")

    return matched, score

def match_song(title1, artistList1, album1, title2, artistList2, album2,
               consider_album=True, simple_match=True):
    
    # Assicurati che artistList1 e artistList2 siano liste
    if isinstance(artistList1, str):
        artistList1 = [artistList1]
    if isinstance(artistList2, str):
        artistList2 = [artistList2]

    matched=False
    if simple_match or consider_album:
        matched = title1 == title2 and \
                  bool(set(artistList1) & set(artistList2)) and \
                  (album1 == album2 if consider_album else True)

    if matched:
        score = 1.0
        logger.info(f"score:{score} COMPLETE MATCH!")
    else:
        matched, score = match_song_weighed(
            title1, artistList1, album1,
            title2, artistList2, album2, consider_album=consider_album)
    
    return matched, score