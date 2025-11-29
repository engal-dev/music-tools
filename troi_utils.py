#!/usr/bin/env python3
"""
Utilities for processing TROI unresolved files.
Centralized functions for parsing files with album/artist and track data.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def parse_unresolved_file(input_file: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse the unresolved file and extract albums and tracks.
    
    Args:
        input_file (str): Path to input file
        
    Returns:
        Tuple containing:
        - List of albums: [{"album": str, "artist": str}, ...]
        - List of tracks: [{"title": str, "album": str, "artist": str}, ...]
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_file}' not found")
    
    albums = []
    tracks = []
    albums_seen = set()  # To avoid duplicate albums
    current_album = None
    current_artist = None
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header line and process the rest
    for line_num, line in enumerate(lines[1:], 2):
        original_line = line
        line = line.rstrip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if line starts with spaces (track line)
        if line.startswith(' ') or line.startswith('\t'):
            # This is a track line
            if current_album and current_artist:
                # Extract track title (remove leading spaces and "1 lookups" suffix)
                track_title = line.strip()
                if track_title.endswith(" lookups"):
                    # Find the last occurrence of a number followed by " lookups"
                    match = re.search(r'\s+\d+\s+lookups$', track_title)
                    if match:
                        track_title = track_title[:match.start()].strip()
                
                if track_title:
                    tracks.append({
                        "title": track_title,
                        "album": current_album,
                        "artist": current_artist
                    })
        else:
            # This should be an album/artist line
            # Use regex to split on multiple spaces (2 or more)
            parts = re.split(r'\s{2,}', line)
            
            if len(parts) >= 2:
                album = parts[0].strip()
                artist = parts[1].strip()
                
                # Create a unique key to avoid duplicates
                album_key = f"{album}|{artist}".lower()
                
                if album and artist and album_key not in albums_seen:
                    albums_seen.add(album_key)
                    albums.append({
                        "album": album,
                        "artist": artist
                    })
                    
                    # Update current album/artist for subsequent tracks
                    current_album = album
                    current_artist = artist
            else:
                print(f"Warning: Could not parse line {line_num}: {original_line.strip()}")
    
    return albums, tracks


def get_unique_albums(input_file: str) -> List[Dict]:
    """
    Extract unique albums from the unresolved file.
    
    Args:
        input_file (str): Path to input file
        
    Returns:
        List of albums: [{"album": str, "artist": str}, ...]
    """
    albums, _ = parse_unresolved_file(input_file)
    return albums


def get_all_tracks(input_file: str) -> List[Dict]:
    """
    Extract all tracks from the unresolved file.
    
    Args:
        input_file (str): Path to input file
        
    Returns:
        List of tracks: [{"title": str, "album": str, "artist": str}, ...]
    """
    _, tracks = parse_unresolved_file(input_file)
    return tracks


def format_search_commands(albums: List[Dict], service: str = "qobuz") -> List[str]:
    """
    Format albums as search commands.
    
    Args:
        albums: List of album dictionaries
        service: Service name for search commands (default: "qobuz")
        
    Returns:
        List of search command strings
    """
    commands = []
    for album_data in albums:
        album = album_data["album"]
        artist = album_data["artist"]
        command = f"/search {service} album {album} {artist}"
        commands.append(command)
    return commands