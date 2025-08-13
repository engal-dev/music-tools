#!/usr/bin/env python3
"""
Spotify Music Library Sync Script
Sincronizza metadati tra libreria musicale locale e Spotify
"""

import os
import sys
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import time
from dotenv import load_dotenv
import utility

sys.path.append('../')
sys.path.append('../common_py_utils')

from common_py_utils import json_utils, log_utils, file_utils, progress_utils
import tags_utils

# Librerie richieste
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    import mutagen
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    import yaml
except ImportError as e:
    print(f"Errore import: {e}")
    print("Installa le dipendenze: pip install spotipy mutagen pyyaml")
    sys.exit(1)


# Carica le credenziali dal file .env
load_dotenv()

REPORT_DIR = "spotify_sync_report"
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """Carica configurazione da file YAML"""
    default_config = {
        'write_tags': False,
        'audio_features': False,
        'skip_synced': True,
        'log_level': 'INFO',
        'max_retries': 5,
        'spotify_search_limit': 30,
        'progress_report_interval': 100,
        'base_delay': 0.1,
        'supported_formats': ['.mp3', '.flac', '.m4a', '.ogg', '.opus'],
        'report_dir': 'spotify_sync_report',
        'progress_bar': {
            'enabled': True,
            'show_eta': True,
            'show_rate': True,
            'show_stats': True,
            'width': 40,
            'update_interval': 0.5
        }
    }
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    default_config.update(file_config)
                    print(f"Configurazione caricata da: {config_file}")
        except Exception as e:
            print(f"Errore caricamento config {config_file}: {e}")
            print("Uso configurazione predefinita")
    
    return default_config

class MusicLibrarySync:
    """Classe principale per la sincronizzazione con Spotify"""
    
    SUPPORTED_FORMATS = {'.mp3', '.flac', '.m4a', '.ogg', '.opus'}
    
    # Configurazione tag Spotify da recuperare
    SPOTIFY_TAGS = {
        'spotify_id': 'ID Spotify del brano',
        'spotify_popularity': 'Popolarità Spotify (0-100)',
        'spotify_preview_url': 'URL anteprima Spotify',
        'spotify_external_urls': 'URL esterni Spotify',
        'spotify_duration_ms': 'Durata in millisecondi',
        'spotify_explicit': 'Contenuto esplicito',
        'spotify_album_id': 'ID album Spotify',
        'spotify_artist_ids': 'ID artisti Spotify',
        'spotify_release_date': 'Data rilascio Spotify',
        'spotify_genres': 'Generi associati',
        'spotify_danceability': 'Danceability',
        'spotify_energy': 'Energy',
        'spotify_valence': 'Valence',
        'spotify_tempo': 'Tempo (BPM)'
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il sincronizzatore da configurazione
        
        Args:
            config: Dizionario di configurazione
        """
        # Salva configurazione completa
        self.config = config
        
        # Estrai configurazione
        self.music_dir = Path(config['music_dir'])
        self.write_tags = config['write_tags']
        self.audio_features = config['audio_features']
        self.max_retries = config['max_retries']
        self.skip_synced = config['skip_synced']
        
        # Configurazioni aggiuntive
        self.spotify_search_limit = config.get('spotify_search_limit', 30)
        self.progress_report_interval = config.get('progress_report_interval', 100)
        self.base_delay = config.get('base_delay', 0.1)
        
        # Aggiorna formati supportati se specificati
        if 'supported_formats' in config:
            self.SUPPORTED_FORMATS = set(config['supported_formats'])
        
        # Aggiorna directory report se specificata  
        global REPORT_DIR
        if 'report_dir' in config:
            REPORT_DIR = config['report_dir']
        
        # Setup logging
        self.logger = log_utils.setup_logging(os.path.basename(__file__), config['log_level'])
        self.logger.info(f"Inizializzazione script - Modalità: {'SCRITTURA' if self.write_tags else 'SIMULAZIONE'}")
        self.logger.info(f"Max retries per rate limit: {self.max_retries}")

        # Setup Spotify
        self.setup_spotify()
        
        # Statistiche
        self.stats = {
            'files_processed': 0,
            'spotify_matches': 0,
            'spotify_not_found': 0,
            'tags_written': 0,
            'errors': 0,
            'skipped': 0,
            'already_synced': 0,
            'rate_limit_retries': 0
        }
        
        # Report dettagliato
        self.detailed_report = []
        
    def setup_spotify(self):
        """Configura connessione Spotify"""
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=CLIENT_ID, 
                client_secret=CLIENT_SECRET
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            
            # Test connessione
            self.spotify.search(q='test', type='track', limit=1)
            self.logger.info("Connessione Spotify stabilita con successo")
            
        except Exception as e:
            self.logger.error(f"Errore connessione Spotify: {e}")
            raise
    
    def get_audio_file_metadata(self, file_path: Path) -> Optional[Dict[str, str]]:
        """Estrae metadati da file audio"""
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.mp3':
                audio_file = mutagen.File(file_path)
                if audio_file is None:
                    return None
                    
                # Prova prima a leggere ARTISTS per artisti multipli
                artists = self._get_multiple_tag_values(audio_file, ['ARTISTS', 'TPE2'])
                if not artists:
                    # Fallback su ARTIST singolo
                    artists = [self._get_tag_value(audio_file, ['TPE1', 'ARTIST'])]
                
                metadata = {
                    'title': self._get_tag_value(audio_file, ['TIT2', 'TITLE']),
                    'artist': artists[0] if artists else None,  # Manteniamo il primo artista come principale
                    'artists': artists,  # Lista completa degli artisti
                    'album': self._get_tag_value(audio_file, ['TALB', 'ALBUM']),
                    'date': self._get_tag_value(audio_file, ['TDRC', 'DATE', 'YEAR']),
                    'spotify_id': self._get_tag_value(audio_file, ['TXXX:spotify_id'])
                }
                
            elif file_ext == '.flac':
                audio_file = FLAC(file_path)
                # Prova prima a leggere ARTISTS per artisti multipli
                artists = self._get_multiple_vorbis_tags(audio_file, 'ARTISTS')
                if not artists:
                    # Fallback su ARTIST singolo
                    artists = [self._get_vorbis_tag(audio_file, 'ARTIST')]
                
                metadata = {
                    'title': self._get_vorbis_tag(audio_file, 'TITLE'),
                    'artist': artists[0] if artists else None,  # Manteniamo il primo artista come principale
                    'artists': artists,  # Lista completa degli artisti
                    'album': self._get_vorbis_tag(audio_file, 'ALBUM'),
                    'date': self._get_vorbis_tag(audio_file, 'DATE'),
                    'spotify_id': self._get_vorbis_tag(audio_file, 'SPOTIFY_ID')
                }
                
            elif file_ext == '.m4a':
                audio_file = MP4(file_path)
                # Prova prima a leggere ARTISTS per artisti multipli
                artists = self._get_multiple_mp4_tags(audio_file, 'aART')
                if not artists:
                    # Fallback su ARTIST singolo
                    artists = [self._get_mp4_tag(audio_file, '©ART')]
                
                metadata = {
                    'title': self._get_mp4_tag(audio_file, '©nam'),
                    'artist': artists[0] if artists else None,  # Manteniamo il primo artista come principale
                    'artists': artists,  # Lista completa degli artisti
                    'album': self._get_mp4_tag(audio_file, '©alb'),
                    'date': self._get_mp4_tag(audio_file, '©day'),
                    'spotify_id': self._get_mp4_tag(audio_file, '----:com.apple.iTunes:spotify_id')
                }
                
            elif file_ext in ['.ogg', '.opus']:
                audio_file = OggVorbis(file_path)
                # Prova prima a leggere ARTISTS per artisti multipli
                artists = self._get_multiple_vorbis_tags(audio_file, 'ARTISTS')
                if not artists:
                    # Fallback su ARTIST singolo
                    artists = [self._get_vorbis_tag(audio_file, 'ARTIST')]
                
                metadata = {
                    'title': self._get_vorbis_tag(audio_file, 'TITLE'),
                    'artist': artists[0] if artists else None,  # Manteniamo il primo artista come principale
                    'artists': artists,  # Lista completa degli artisti
                    'album': self._get_vorbis_tag(audio_file, 'ALBUM'),
                    'date': self._get_vorbis_tag(audio_file, 'DATE'),
                    'spotify_id': self._get_vorbis_tag(audio_file, 'SPOTIFY_ID')
                }
            else:
                return None
            
            # Pulisci metadati
            for key in metadata:
                if metadata[key]:
                    if isinstance(metadata[key], list):
                        metadata[key] = [str(x).strip() for x in metadata[key] if x]
                    else:
                        metadata[key] = str(metadata[key]).strip()
                        if key == 'date' and len(metadata[key]) > 4:
                            metadata[key] = metadata[key][:4]  # Solo anno
            
            # Aggiungi flag per indicare se già sincronizzato
            metadata['already_synced'] = bool(metadata.get('spotify_id'))
                        
            return metadata if any(metadata.values()) else None
            
        except Exception as e:
            self.logger.warning(f"Errore lettura metadati {file_path}: {e}")
            return None
    
    def _get_tag_value(self, audio_file, tag_names: List[str]) -> Optional[str]:
        """Recupera valore tag da vari formati"""
        for tag_name in tag_names:
            if tag_name in audio_file:
                value = audio_file[tag_name]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_vorbis_tag(self, audio_file, tag_name: str) -> Optional[str]:
        """Recupera tag Vorbis"""
        if tag_name in audio_file:
            values = audio_file[tag_name]
            return values[0] if values else None
        return None
    
    def _get_mp4_tag(self, audio_file, tag_name: str) -> Optional[str]:
        """Recupera tag MP4"""
        if tag_name in audio_file:
            values = audio_file[tag_name]
            if isinstance(values, list) and values:
                value = values[0]
                # Se è un tag personalizzato (bytes), decodificalo
                if isinstance(value, bytes):
                    return value.decode('utf-8')
                return str(value)
            elif values:
                return str(values)
        return None
    
    def _get_multiple_tag_values(self, audio_file, tag_names: List[str]) -> List[str]:
        """Recupera valori multipli per un tag"""
        values = []
        for tag_name in tag_names:
            if tag_name in audio_file:
                value = audio_file[tag_name]
                if isinstance(value, list):
                    values.extend([str(v) for v in value if v])
                elif value:
                    values.append(str(value))
        return values

    def _get_multiple_vorbis_tags(self, audio_file, tag_name: str) -> List[str]:
        """Recupera valori multipli per tag Vorbis"""
        if tag_name in audio_file:
            return [str(v) for v in audio_file[tag_name] if v]
        return []

    def _get_multiple_mp4_tags(self, audio_file, tag_name: str) -> List[str]:
        """Recupera valori multipli per tag MP4"""
        if tag_name in audio_file:
            return [str(v) for v in audio_file[tag_name] if v]
        return []
    
    def search_spotify_track(self, metadata: Dict[str, str]) -> Optional[Dict]:
        """Cerca brano su Spotify con retry per rate limit"""
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # Costruisci query di ricerca
                query_parts = []
                
                if metadata.get('title'):
                    query_parts.append(f'track:"{metadata["title"]}"')
                    
                    # Gestione artisti multipli
                    if metadata.get('artists'):
                        # Se abbiamo artisti multipli, usiamo il primo per la ricerca principale
                        # e aggiungiamo gli altri come termini di ricerca aggiuntivi
                        artists = metadata['artists']
                        if artists:
                            query_parts.append(f'artist:"{artists[0]}"')
                            # Aggiungi gli altri artisti come termini di ricerca
                            for artist in artists[1:]:
                                query_parts.append(f'artist:"{artist}"')
                    elif metadata.get('artist'):
                        query_parts.append(f'artist:"{metadata["artist"]}"')
                        
                    if metadata.get('album'):
                        query_parts.append(f'album:"{metadata["album"]}"')
                        
                    if not query_parts:
                        return None
                        
                    query = ' '.join(query_parts)
                    
                    # Ricerca su Spotify
                    results = self.spotify.search(q=query, type='track', limit=self.spotify_search_limit)
                
                    if not results['tracks']['items']:
                        # Prova ricerca più permissiva usando tutti gli artisti
                        if metadata.get('artists'):
                            simple_query = f"{' '.join(metadata['artists'])} {metadata.get('title', '')}"
                        else:
                            simple_query = f"{metadata.get('artist', '')} {metadata.get('title', '')}"
                        results = self.spotify.search(q=simple_query, type='track', limit=self.spotify_search_limit)
                
                    if results['tracks']['items']:
                        # Usa lista artisti se disponibile, altrimenti fallback su artista singolo
                        artists = metadata.get('artists', [metadata.get('artist', '')])
                        track = utility.find_song(metadata["title"], artists, metadata["album"], results['tracks']['items'], "spotify_ext", only_first_result=False, permit_choice=True, consider_album=True)
                        # Prendi il primo risultato (più rilevante)
                        #track = results['tracks']['items'][0]
                
                if not track:
                    return None
                else:
                    spotify_data = {
                        'spotify_id': track['id'],
                        'spotify_popularity': track['popularity'],
                        'spotify_preview_url': track.get('preview_url', ''),
                        'spotify_external_urls': track['external_urls']['spotify'],
                        'spotify_duration_ms': track['duration_ms'],
                        'spotify_explicit': track['explicit'],
                        'spotify_album_id': track['album']['id'],
                        'spotify_artist_ids': ','.join([artist['id'] for artist in track['artists']]),
                        'spotify_artists': [artist['name'] for artist in track['artists']],  # Aggiungiamo anche i nomi degli artisti
                        'spotify_release_date': track['album']['release_date']
                    }
                    self.logger.debug(f"{spotify_data}")
                    
                    # Aggiungi audio features se richieste
                    if self.audio_features:
                        try:
                            features = self.spotify.audio_features(track['id'])[0]
                            if features:
                                spotify_data.update({
                                    'spotify_danceability': features['danceability'],
                                    'spotify_energy': features['energy'],
                                    'spotify_valence': features['valence'],
                                    'spotify_tempo': features['tempo']
                                })
                        except Exception as e:
                            self.logger.warning(f"Errore recupero audio features: {e}")
                    
                    return spotify_data
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Controlla se è un rate limit
                if 'rate limit' in error_msg:
                    retry_count += 1
                    self.stats['rate_limit_retries'] += 1
                    
                    if retry_count <= self.max_retries:
                        wait_time = 10 * retry_count  # Tempo di attesa progressivo
                        self.logger.warning(f"Rate limit raggiunto (tentativo {retry_count}/{self.max_retries}), attendo {wait_time} secondi...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"Rate limit persistente dopo {self.max_retries} tentativi, abbandono ricerca")
                        return None
                else:
                    # Altri errori non sono rate limit, non fare retry
                    self.logger.warning(f"Errore ricerca Spotify: {e}")
                    self.logger.debug(f"Traceback completo:\n{traceback.format_exc()}")
                    return None
                
        return None
    
    def write_spotify_tags(self, file_path: Path, spotify_data: Dict) -> bool:
        """Scrive tag Spotify nel file"""
        if not self.write_tags:
            return True  # Simulazione
            
        try:
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.mp3':
                return tags_utils.write_mp3_tags(file_path, spotify_data)
            elif file_ext == '.flac':
                return tags_utils.write_flac_tags(file_path, spotify_data)
            elif file_ext == '.m4a':
                return tags_utils.write_mp4_tags(file_path, spotify_data)
            elif file_ext in ['.ogg', '.opus']:
                return tags_utils.write_ogg_tags(file_path, spotify_data)
                
        except Exception as e:
            self.logger.error(f"Errore scrittura tag {file_path}: {e}")
            
        return False
    
    def process_file(self, file_path: Path) -> Dict:
        """Processa singolo file audio"""
        self.stats['files_processed'] += 1
        
        result = {
            'file': str(file_path),
            'status': 'error',
            'metadata': {},
            'spotify_data': {},
            'message': ''
        }
        
        # Leggi metadati esistenti
        metadata = self.get_audio_file_metadata(file_path)
        if not metadata:
            result['message'] = 'Impossibile leggere metadati'
            self.stats['errors'] += 1
            return result
            
        result['metadata'] = metadata
        
        # Verifica se già sincronizzato e skip_synced è attivo
        if metadata.get('already_synced') and self.skip_synced:
            result['message'] = 'File già sincronizzato (spotify_id presente)'
            result['status'] = 'already_synced'
            self.stats['already_synced'] += 1
            return result
        
        # Verifica metadati minimi
        if not metadata.get('title') or not metadata.get('artist'):
            result['message'] = 'Metadati insufficienti (titolo/artista mancanti)'
            self.stats['skipped'] += 1
            result['status'] = 'skipped'
            return result
        
        self.logger.info(f"{metadata.get('artist')} - {metadata.get('album')} - {metadata.get('title')}")

        # Cerca su Spotify
        spotify_data = self.search_spotify_track(metadata)
        if spotify_data:
            result['spotify_data'] = spotify_data
            result['status'] = 'found'
            self.stats['spotify_matches'] += 1
            
            # Scrivi tag
            if self.write_spotify_tags(file_path, spotify_data):
                self.stats['tags_written'] += 1
                result['message'] = f"Tag {'scritti' if self.write_tags else 'simulati'} con successo"
            else:
                result['message'] = 'Errore scrittura tag'
                result['status'] = 'error'
                self.stats['errors'] += 1
        else:
            result['status'] = 'not_found'
            result['message'] = 'Brano non trovato su Spotify'
            self.logger.info("Brano non trovato su Spotify")
            self.stats['spotify_not_found'] += 1
            
        return result
    
    def scan_directory(self) -> List[Path]:
        """Scansiona directory per file audio"""
        audio_files = []
        
        for root, dirs, files in os.walk(self.music_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                    audio_files.append(file_path)
                    
        self.logger.info(f"Trovati {len(audio_files)} file audio")
        return audio_files
    
    def run(self):
        """Esegue sincronizzazione completa"""
        start_time = datetime.now()
        self.logger.info(f"Inizio sincronizzazione - Directory: {self.music_dir}")
        
        # Scansiona file
        audio_files = self.scan_directory()
        if not audio_files:
            self.logger.warning("Nessun file audio trovato")
            return
        
        print(f"\nProcessando {len(audio_files)} file audio...")
        
        # Setup progress bar dalla configurazione
        progress_bar_config = self.config.get('progress_bar', {})
        
        if progress_bar_config.get('enabled', True):
            # Processa file con progress bar
            display_config = {k: v for k, v in progress_bar_config.items() 
                            if k != 'enabled' and k != 'update_interval'}
            
            with progress_utils.create_progress_tracker(
                total=len(audio_files),
                description="Sincronizzazione Spotify",
                update_interval=progress_bar_config.get('update_interval', 0.5),
                display_config=display_config
            ) as progress:
                self._process_files_with_progress(audio_files, progress)
        else:
            # Processa file senza progress bar (modalità tradizionale)
            self._process_files_traditional(audio_files)
        
        # Genera report finale
        end_time = datetime.now()
        duration = end_time - start_time
        
        print()  # Nuova riga dopo progress bar
        self.generate_final_report(duration)
    
    def _process_files_with_progress(self, audio_files, progress):
        """Processa file con progress bar"""
        for file_path in audio_files:
            self.logger.debug(f"Processando: {file_path.name}")
            
            result = self.process_file(file_path)
            self.detailed_report.append(result)
            
            # Aggiorna progress in base al risultato
            status = result['status']
            if status in ['found', 'already_synced']:
                progress.increment('completed')
            elif status in ['not_found', 'skipped']:
                progress.increment('skipped')
            else:  # error
                progress.increment('failed')
            
            # Rate limiting Spotify
            time.sleep(self.base_delay)
    
    def _process_files_traditional(self, audio_files):
        """Processa file con output tradizionale (senza progress bar)"""
        for i, file_path in enumerate(audio_files, 1):
            self.logger.info(f"[{i}/{len(audio_files)}] Processando: {file_path.name}")
            
            result = self.process_file(file_path)
            self.detailed_report.append(result)
            
            # Rate limiting Spotify
            time.sleep(self.base_delay)
            
            # Progress report configurabile
            if i % self.progress_report_interval == 0:
                self.logger.info(f"Progresso: {i}/{len(audio_files)} file processati")
        
    def generate_final_report(self, duration):
        """Genera report finale"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Report testuale
        report_file = f"spotify_sync_report_{timestamp}.txt"

        report_file = file_utils.append_dir_to_file_name(file_utils.sanitize_filename(report_file), REPORT_DIR)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("SPOTIFY MUSIC LIBRARY SYNC - REPORT FINALE\n")
            f.write("="*50 + "\n\n")
            f.write(f"Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Directory: {self.music_dir}\n")
            f.write(f"Modalità: {'SCRITTURA' if self.write_tags else 'SIMULAZIONE'}\n")
            f.write(f"Audio Features: {'SÌ' if self.audio_features else 'NO'}\n")
            f.write(f"Max Retries: {self.max_retries}\n")
            f.write(f"Durata: {duration}\n\n")
            
            f.write("STATISTICHE:\n")
            f.write("-" * 20 + "\n")
            for key, value in self.stats.items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")
            
            if self.stats['files_processed'] > 0:
                success_rate = (self.stats['spotify_matches'] / self.stats['files_processed']) * 100
                f.write(f"Tasso successo: {success_rate:.1f}%\n")
            
            f.write("\nDETTAGLI PER STATO:\n")
            f.write("-" * 20 + "\n")
            
            status_groups = {}
            for item in self.detailed_report:
                status = item['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(item)
            
            for status, items in status_groups.items():
                if status.upper()=="FOUND":
                    f.write(f"\n{status.upper()} ({len(items)} file)\n")
                else:
                    f.write(f"\n{status.upper()} ({len(items)} file):\n")
                    
                    for item in items:
                        f.write(f"  - {item['metadata'].get('artist')} - {item['metadata'].get('album')} - {item['metadata'].get('title')}: {item['message']}\n")
        
        # Report JSON dettagliato
        json_report_file = f"spotify_sync_detailed_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'music_dir': str(self.music_dir),
                'write_tags': self.write_tags,
                'audio_features': self.audio_features,
                'max_retries': self.max_retries
            },
            'stats': self.stats,
            'duration_seconds': duration.total_seconds(),
            'detailed_results': self.detailed_report
        }
        
        json_utils.save_to_json_file(report_data, json_report_file, REPORT_DIR)
        
        # Log finale
        self.logger.info(f"Sincronizzazione completata in {duration}")
        self.logger.info(f"Report salvato in: {report_file}")
        self.logger.info(f"Report dettagliato: {json_report_file}")
        #self.logger.info(f"Log dettagliato: {self.log_file}")
        
        # Stampa statistiche finali
        print("\n" + "="*50)
        print("SINCRONIZZAZIONE COMPLETATA")
        print("="*50)
        print(f"File processati: {self.stats['files_processed']}")
        print(f"Trovati su Spotify: {self.stats['spotify_matches']}")
        print(f"Non trovati: {self.stats['spotify_not_found']}")
        print(f"Già sincronizzati: {self.stats['already_synced']}")
        print(f"Tag {'scritti' if self.write_tags else 'simulati'}: {self.stats['tags_written']}")
        print(f"Errori: {self.stats['errors']}")
        print(f"Retry rate limit: {self.stats['rate_limit_retries']}")
        if self.stats['files_processed'] > 0:
            success_rate = (self.stats['spotify_matches'] / self.stats['files_processed']) * 100
            print(f"Tasso successo: {success_rate:.1f}%")
        print(f"\nReport: {report_file}")


def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description='Sincronizza libreria musicale con Spotify')
    
    # Parametri obbligatori
    parser.add_argument('music_dir', help='Directory principale della musica')
    
    # Parametri di configurazione
    parser.add_argument('--config', '-c', help='File di configurazione YAML')
    
    # Parametri che possono sovrascrivere la configurazione
    parser.add_argument('--write-tags', action='store_true', 
                       help='Scrivi effettivamente i tag (sovrascrive config)')
    parser.add_argument('--no-write-tags', action='store_true',
                       help='Modalità simulazione (sovrascrive config)')
    parser.add_argument('--audio-features', action='store_true',
                       help='Recupera audio features (sovrascrive config)')
    parser.add_argument('--no-audio-features', action='store_true',
                       help='Non recuperare audio features (sovrascrive config)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Livello di logging (sovrascrive config)')
    parser.add_argument('--max-retries', type=int,
                       help='Numero massimo di tentativi per rate limit (sovrascrive config)')
    parser.add_argument('--skip-synced', action='store_true',
                       help='Salta tracce già sincronizzate (sovrascrive config)')
    parser.add_argument('--no-skip-synced', action='store_true',
                       help='Non saltare tracce già sincronizzate (sovrascrive config)')
    parser.add_argument('--no-progress-bar', action='store_true',
                       help='Disabilita progress bar (sovrascrive config)')
    
    args = parser.parse_args()
    
    # Carica configurazione
    config = load_config(args.config)
    
    # Override configurazione con parametri CLI (music_dir è sempre da CLI)
    config['music_dir'] = args.music_dir
    if args.write_tags:
        config['write_tags'] = True
    if args.no_write_tags:
        config['write_tags'] = False
    if args.audio_features:
        config['audio_features'] = True
    if args.no_audio_features:
        config['audio_features'] = False
    if args.log_level:
        config['log_level'] = args.log_level
    if args.max_retries is not None:
        config['max_retries'] = args.max_retries
    if args.skip_synced:
        config['skip_synced'] = True
    if args.no_skip_synced:
        config['skip_synced'] = False
    if args.no_progress_bar:
        config['progress_bar']['enabled'] = False
    
    # Verifica directory
    if not os.path.exists(config['music_dir']):
        print(f"Errore: Directory {config['music_dir']} non trovata")
        sys.exit(1)
    
    # Mostra configurazione finale
    print(f"Directory musica: {config['music_dir']}")
    print(f"Modalità: {'SCRITTURA' if config['write_tags'] else 'SIMULAZIONE'}")
    print(f"Audio features: {'SÌ' if config['audio_features'] else 'NO'}")
    print(f"Skip già sincronizzati: {'SÌ' if config['skip_synced'] else 'NO'}")
    print(f"Log level: {config['log_level']}")
    
    try:
        # Inizializza e avvia sincronizzazione
        sync = MusicLibrarySync(config)
        
        sync.run()
        
    except KeyboardInterrupt:
        print("\nSincronizzazione interrotta dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"Errore: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()