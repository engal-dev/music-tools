from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

try:
    from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
except ImportError as e:
    print(f"Errore import: {e}")
    print("Installa le dipendenze: pip install spotipy mutagen")

logger = logging.getLogger(__name__)

def write_mp3_tags(file_path: Path, spotify_data: Dict) -> bool:
    """Scrive tag MP3/ID3"""
    try:
        try:
            audio_file = ID3(file_path)
        except ID3NoHeaderError:
            audio_file = ID3()
            
        for key, value in spotify_data.items():
            if value is not None and value != '':
                audio_file.add(TXXX(encoding=3, desc=key, text=str(value)))
                
        audio_file.save(file_path)
        return True
        
    except Exception as e:
        logger.error(f"Errore scrittura MP3 tags: {e}")
        return False

def write_flac_tags(file_path: Path, spotify_data: Dict) -> bool:
    """Scrive tag FLAC"""
    try:
        audio_file = FLAC(file_path)
        
        for key, value in spotify_data.items():
            if value is not None and value != '':
                audio_file[key.upper()] = str(value)
                
        audio_file.save()
        return True
        
    except Exception as e:
        logger.error(f"Errore scrittura FLAC tags: {e}")
        return False

def write_mp4_tags(file_path: Path, spotify_data: Dict) -> bool:
    """Scrive tag MP4"""
    try:
        audio_file = MP4(file_path)
        
        for key, value in spotify_data.items():
            if value is not None and value != '':
                # MP4 usa il formato ----:com.apple.iTunes:TAGNAME
                tag_name = f"----:com.apple.iTunes:{key}"
                audio_file[tag_name] = [str(value).encode('utf-8')]
                
        audio_file.save()
        return True
        
    except Exception as e:
        logger.error(f"Errore scrittura MP4 tags: {e}")
        return False

def write_ogg_tags(file_path: Path, spotify_data: Dict) -> bool:
    """Scrive tag OGG/Vorbis"""
    try:
        audio_file = OggVorbis(file_path)
        
        for key, value in spotify_data.items():
            if value is not None and value != '':
                audio_file[key.upper()] = str(value)
                
        audio_file.save()
        return True
        
    except Exception as e:
        logger.error(f"Errore scrittura OGG tags: {e}")
        return False

def read_spotify_popularity_tag(file_path: Path) -> Optional[int]:
    """
    Legge il tag SPOTIFY_POPULARITY da un file audio
    
    Args:
        file_path: Percorso del file audio
        
    Returns:
        Valore di popularità (0-100) o None se non trovato
    """
    try:
        extension = file_path.suffix.lower()
        
        if extension == '.mp3':
            return read_mp3_popularity(file_path)
        elif extension == '.flac':
            return read_flac_popularity(file_path)
        elif extension in ['.m4a', '.mp4']:
            return read_mp4_popularity(file_path)
        elif extension in ['.ogg', '.opus']:
            return read_ogg_popularity(file_path)
        else:
            logger.warning(f"Formato file non supportato: {extension}")
            return None
            
    except Exception as e:
        logger.error(f"Errore lettura tag da {file_path}: {e}")
        return None

def read_mp3_popularity(file_path: Path) -> Optional[int]:
    """Legge popularity da file MP3/ID3"""
    try:
        audio_file = ID3(file_path)
        # Cerca il tag TXXX con descrizione 'spotify_popularity'
        for tag in audio_file.getall('TXXX'):
            if tag.desc.lower() == 'spotify_popularity':
                return int(tag.text[0])
        return None
    except (ID3NoHeaderError, Exception):
        return None

def read_flac_popularity(file_path: Path) -> Optional[int]:
    """Legge popularity da file FLAC"""
    try:
        audio_file = FLAC(file_path)
        if 'SPOTIFY_POPULARITY' in audio_file:
            return int(audio_file['SPOTIFY_POPULARITY'][0])
        return None
    except Exception:
        return None

def read_mp4_popularity(file_path: Path) -> Optional[int]:
    """Legge popularity da file MP4"""
    try:
        audio_file = MP4(file_path)
        tag_name = "----:com.apple.iTunes:spotify_popularity"
        if tag_name in audio_file:
            return int(audio_file[tag_name][0].decode('utf-8'))
        return None
    except Exception:
        return None

def read_ogg_popularity(file_path: Path) -> Optional[int]:
    """Legge popularity da file OGG/Vorbis"""
    try:
        audio_file = OggVorbis(file_path)
        if 'SPOTIFY_POPULARITY' in audio_file:
            return int(audio_file['SPOTIFY_POPULARITY'][0])
        return None
    except Exception:
        return None
