# Spotify Tracker

Fetches your 50 most recently played Spotify tracks and persists them to a local SQLite database. Designed to run on a schedule (e.g. cron) to build a continuous listening history beyond Spotify's 50-item API limit.

## How it works

1. Authenticates with the Spotify API via OAuth
2. Fetches up to 50 recently played tracks
3. Upserts them into `data/spotify_music_history.db` keyed by `played_at` timestamp

Logs are written to `data/history.log`.

## Setup

**1. Clone and install dependencies**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Create a Spotify app**

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app. Set the redirect URI to `http://127.0.0.1:8888/callback`.

**3. Configure environment variables**

```bash
cp .env_example .env
```

Fill in your credentials:
```env
SPOTIPY_CLIENT_ID="your-client-id"
SPOTIPY_CLIENT_SECRET="your-secret-id"
SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
```

**4. Create the data directory**
```bash
mkdir -p data
```

**5. Authenticate**

Run once manually to complete the OAuth flow:
```bash
python main.py
```

A `.cache` file will be saved with your token for future runs.

## Running

```bash
python main.py
```

To run on a schedule, add a cron job (e.g. every 30 minutes):
```
*/30 * * * * /path/to/venv/bin/python /path/to/spotify_tracker/main.py
```

## Docker

The `data/` directory is created automatically inside the container.

Pull and run with docker-compose:
```bash
docker-compose up -d
```

> Note: Initial OAuth requires an interactive browser step. Run `python main.py` locally first to generate the `.cache` token file — it is mounted into the container automatically via `docker-compose.yml`.

## Database schema

Table: `music_history`

| Column | Type | Notes |
|---|---|---|
| `played_at` | DateTime | Primary key |
| `track_name` | String | |
| `track_uri` | String | Spotify URI |
| `album_name` | String | |
| `album_uri` | String | |
| `artist_names` | String | Comma-separated |
| `artist_uris` | String | Comma-separated |
