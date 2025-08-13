#!/usr/bin/env python3
"""
Navidrome Rating Updater from Spotify Popularity Tags
Legge i tag SPOTIFY_POPULARITY dai file audio e aggiorna le stelline su Navidrome
"""

import sys
import os
import logging
import navidrome
import tags_utils
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import log_utils

logger = log_utils.setup_logging(os.path.basename(__file__), logging.DEBUG)
base_path = "M:/"

def convert_popularity_to_rating(popularity):
    """
    Converte la popolarità Spotify (0-100) in rating a stelle (1-5)
    
    Args:
        popularity: Valore di popolarità da 0 a 100
        
    Returns:
        Rating da 0 a 5 stelle (0 = nessun rating)
    """
    if popularity == 0:
        return 0  # Nessun rating
    elif popularity <= 20:
        return 1
    elif popularity <= 40:
        return 2
    elif popularity <= 60:
        return 3
    elif popularity <= 80:
        return 4
    else:
        return 5

def find_audio_file_path(song):
    """
    Trova il percorso del file audio basandosi sui metadati del brano
    
    Args:
        song: Dizionario con metadati del brano da Navidrome
        
    Returns:
        Percorso del file audio o None se non trovato
    """
    try:
        # Navidrome fornisce il percorso nel campo 'path'
        if 'path' in song:
            # Sostituisce '/music/' con base_path se presente
            path_str = song['path']
            if path_str.startswith('/music/'):
                path_str = path_str.replace('/music/', base_path, 1)
            
            file_path = Path(path_str)
            if file_path.exists():
                return file_path
        
        # Se il path non esiste, prova varianti comuni
        # Nota: questo dipende dalla configurazione specifica di Navidrome
        logger.debug(f"File non trovato: {path_str}")
        return None
        
    except Exception as e:
        logger.error(f"Errore ricerca file per {song.get('title', 'Unknown')}: {e}")
        return None

def main():
    """Funzione principale"""
    logger.info("🎵 Avvio aggiornamento rating Navidrome da tag Spotify Popularity")
    
    start_time = time.time()
    start_datetime = datetime.now()
    logger.info(f"🚀 Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Autenticazione con Navidrome
        logger.info("Autenticazione con Navidrome...")
        session = navidrome.authenticate()
        
        # Recupera tutti i brani
        logger.info("Recupero tutti i brani da Navidrome...")
        all_songs = navidrome.get_all_songs(session)
        
        if not all_songs:
            logger.warning("Nessun brano trovato su Navidrome")
            return 1
        
        # Statistiche
        stats = {
            'total_songs': len(all_songs),
            'files_found': 0,
            'tags_found': 0,
            'ratings_updated': 0,
            'errors': 0,
            'skipped_no_path': 0
        }
        
        logger.info(f"Trovati {stats['total_songs']} brani su Navidrome")
        
        # Processa ogni brano
        for i, song in enumerate(all_songs, 1):
            try:
                song_title = song.get('title', 'Unknown')
                song_artist = song.get('artist', 'Unknown')
                song_id = song.get('id')
                
                if i % 100 == 0:
                    logger.info(f"Elaborazione: {i}/{stats['total_songs']} ({(i/stats['total_songs']*100):.1f}%)")
                
                # Trova il file audio
                file_path = find_audio_file_path(song)
                if not file_path:
                    stats['skipped_no_path'] += 1
                    logger.debug(f"File non trovato per: {song_artist} - {song_title}")
                    continue
                
                stats['files_found'] += 1
                
                # Leggi il tag popularity
                popularity = tags_utils.read_spotify_popularity_tag(file_path)
                if popularity is None:
                    logger.debug(f"Tag SPOTIFY_POPULARITY non trovato per: {song_artist} - {song_title}")
                    continue
                
                stats['tags_found'] += 1
                
                # Converte in rating
                rating = convert_popularity_to_rating(popularity)
                
                # Aggiorna il rating su Navidrome
                if navidrome.set_song_rating(session, song_id, rating):
                    stats['ratings_updated'] += 1
                    logger.info(f"✅ Rating aggiornato: {song_artist} - {song_title} | Popularity: {popularity} → Rating: {rating} stelle")
                else:
                    stats['errors'] += 1
                    logger.error(f"❌ Errore aggiornamento: {song_artist} - {song_title}")
                
                # Pausa per non sovraccaricare il server
                time.sleep(0.05)
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Errore processando brano {i}: {e}")
                continue
        
        # Report finale
        end_time = time.time()
        duration = timedelta(seconds=int(end_time - start_time))
        
        logger.info("=" * 60)
        logger.info("📊 REPORT FINALE")
        logger.info("=" * 60)
        logger.info(f"Brani totali elaborati: {stats['total_songs']}")
        logger.info(f"File audio trovati: {stats['files_found']}")
        logger.info(f"Brani senza percorso file: {stats['skipped_no_path']}")
        logger.info(f"Tag popularity trovati: {stats['tags_found']}")
        logger.info(f"Rating aggiornati con successo: {stats['ratings_updated']}")
        logger.info(f"Errori: {stats['errors']}")
        logger.info(f"Tempo totale: {duration}")
        
        if stats['tags_found'] > 0:
            success_rate = (stats['ratings_updated'] / stats['tags_found']) * 100
            logger.info(f"Tasso successo aggiornamenti: {success_rate:.1f}%")
        
        logger.info("=" * 60)
        
        if stats['ratings_updated'] > 0:
            logger.info("🎉 Aggiornamento completato con successo!")
        else:
            logger.warning("⚠️ Nessun rating aggiornato")
            
    except Exception as e:
        logger.error(f"Errore generale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)