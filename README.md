# Spotify Tracker

Fetches your 50 most recently played Spotify tracks and persists them to a local SQLite database. Designed to run on a schedule (e.g. cron) to build a continuous listening history beyond Spotify's 50-item API limit.

A companion read-only **FastAPI service** (`api.py`) exposes the database over HTTP with pagination and period-based summaries, suitable for use behind a Cloudflare Tunnel.

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
API_KEY="your-api-key"
```

`API_KEY` is used to authenticate requests to the FastAPI service (see below).

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

Pull and run with docker-compose (starts both the tracker and the API):
```bash
docker-compose up -d
```

> Note: Initial OAuth requires an interactive browser step. Run `python main.py` locally first to generate the `.cache` token file — it is mounted into the container automatically via `docker-compose.yml`.

## API

`api.py` is a read-only FastAPI service that queries the SQLite database. All endpoints require an `X-API-Key` header matching the `API_KEY` environment variable.

### Running locally

```bash
uvicorn api:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

### Endpoints

#### `GET /history`

Returns listening history ordered by most recent first.

| Parameter | Default | Max | Description |
|---|---|---|---|
| `limit` | 50 | 500 | Number of rows to return |
| `offset` | 0 | — | Rows to skip |

```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/history?limit=10&offset=0"
```

Response:
```json
{
  "total": 1042,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "played_at": "2026-03-21T14:32:00",
      "track_name": "Song Title",
      "album_name": "Album Name",
      "artist_names": "Artist 1, Artist 2",
      ...
    }
  ]
}
```

#### `GET /summary`

Returns top tracks, artists, and albums for a given time period.

| Parameter | Default | Max | Description |
|---|---|---|---|
| `period` | required | — | `weekly`, `biweekly`, `monthly`, `quarterly`, `yearly` |
| `top_n` | 10 | 50 | Number of entries per category |

```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/summary?period=weekly&top_n=5"
```

Response:
```json
{
  "period": "weekly",
  "start_date": "2026-03-14T14:32:00",
  "end_date": "2026-03-21T14:32:00",
  "top_tracks": [{"name": "Song Title", "play_count": 7}],
  "top_artists": [{"name": "Artist Name", "play_count": 12}],
  "top_albums": [{"name": "Album Name", "play_count": 9}]
}
```

### Authentication

Requests without a valid `X-API-Key` header return `HTTP 401`. To rotate the key, update `API_KEY` in `.env` and restart the `spotify_api` container — no code changes needed.

### Remote access via Cloudflare Tunnel

The API is designed to be exposed via [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) rather than opening a port directly:

- Cloudflare handles TLS termination — no HTTPS config needed on the server
- Port `8000` does not need to be publicly exposed on the host firewall
- The `cloudflared` daemon connects outbound to Cloudflare's edge

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
