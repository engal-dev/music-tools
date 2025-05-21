# Music Tools

A collection of Python scripts to manage and synchronize music between Spotify and Navidrome.

## Features

- Export Spotify playlists to JSON format
- Retrieve Navidrome playlists
- Compare playlists between Spotify and Navidrome
- Add matched songs to Navidrome favorites
- Backup and restore functionality
- Manual song matching capabilities

## Prerequisites

- Python 3.x
- Spotify API credentials
- Navidrome server access
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/music-tools.git
cd music-tools
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your credentials:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
NAVIDROME_USERNAME=your_navidrome_username
NAVIDROME_PASSWORD=your_navidrome_password
NAVIDROME_URL=your_navidrome_server_url
NAVIDROME_CLIENT_ID=your_navidrome_client_id
NAVIDROME_API_VERSION=your_navidrome_api_version
```

## Usage

### 1. Export Spotify Playlists

```bash
python spotify-playlist-exporter.py [--playlist-ids PLAYLIST_ID1 PLAYLIST_ID2 ...]
```

This will export your Spotify playlists to JSON files in the `spotify-playlists` directory.

### 2. Get Navidrome Playlists

```bash
python navidrome-get-playlist.py
```

This will retrieve your Navidrome playlists and save them to JSON files in the `navidrome-playlists` directory.

### 3. Compare Playlists

```bash
python compare-spotify-navidrome.py
```

This will compare your Spotify and Navidrome playlists and generate reports in the `compare_report` directory.

### 4. Add to Favorites

```bash
python navidrome-add-to-favourites.py
```

This will add matched songs to your Navidrome favorites.

### 5. Backup and Restore

```bash
python backup-compare.py
```

This will create a backup of your current state.

### 6. Manual Merge

```bash
python manual-merge.py
```

Use this to manually match songs between Spotify and Navidrome.

## Directory Structure

```
music-tools/
├── spotify-playlists/     # Exported Spotify playlists
├── navidrome-playlists/   # Retrieved Navidrome playlists
├── compare_report/        # Comparison reports
├── spotify-playlist-exporter.py
├── navidrome-get-playlist.py
├── compare-spotify-navidrome.py
├── navidrome-add-to-favourites.py
├── backup-compare.py
├── manual-merge.py
├── navidrome.py          # Navidrome API utilities
├── utility.py           # Common utilities
├── requirements.txt
└── .env
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 