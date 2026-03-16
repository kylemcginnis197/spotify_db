import spotipy
from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from log import logger

load_dotenv()

try:
    scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing playlist-read-private user-library-read user-read-recently-played user-follow-read"
    client = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=getenv("SPOTIPY_CLIENT_ID"),
            client_secret=getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=getenv("SPOTIPY_REDIRECT_URI"),
            open_browser=False,
            scope=scope
        )
    )
except Exception as e:
    client = None
    logger.info(msg=f"Failed to connect to spotify: {e}")

def get_recently_played_songs(limit: int = 50):
    """
    Uses the Spotify Song/Music API.
    Gets the previous 50 songs played on the user's spotify account. Additionally, track URI's can be used to play the song using start_playback tool.
    """
    if client is None:
        raise Exception(f"Spotify client is null (likely failed to authenticate)")

    try:
        results = client.current_user_recently_played(limit=limit)
    except SpotifyException as e:
        raise Exception(f"Failed to get recently played songs, reason: {e}")
    
    if items := results.get("items", None):
        user_tracks = []

        for playback in items:
            played_at = playback.get('played_at', None)

            try:
                dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
            except:
                dt = None

            if track := playback.get("track", None):
                song_name = track.get("name", None)
                song_uri = track.get("uri", None)
                
                if song_name is None or song_uri is None:
                    continue

                album = track.get("album", {})

                artists_str = ""
                artists_uri = ""

                for artist in track.get("artists", []):
                    name = artist.get("name", None)
                    uri = artist.get("uri", "n/a")

                    if name is None:
                        continue
                    
                    if len(artists_str):
                        artists_str += ", "
                        artists_uri += ", "
                    
                    artists_str += name
                    artists_uri += uri

                user_tracks.append({
                    "track_name": track.get("name", "n/a"),
                    "track_uri": track.get("uri", "n/a"),
                    "artist_names": artists_str,
                    "artist_uris": artists_uri,
                    "album_name": album.get("name", "n/a"),
                    "album_uri": album.get("uri", "n/a"),
                    "played_at": dt
                })

        return user_tracks