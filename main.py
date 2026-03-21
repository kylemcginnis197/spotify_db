"""
Saves 50 previous songs in sqlalchemy database periodically
"""
from sqlalchemy import create_engine, Column, Integer, Boolean, String, DateTime
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import declarative_base, Session
from spotify_lib import get_recently_played_songs
from log import logger

base = declarative_base()

class MusicSchema(base):
    __tablename__ = "music_history"
    played_at = Column(DateTime, primary_key=True)
    track_name = Column(String, nullable=True)
    track_uri = Column(String, nullable=True)
    album_name = Column(String, nullable=True)
    album_uri = Column(String, nullable=True)
    artist_names = Column(String, nullable=True)
    artist_uris = Column(String, nullable=True)

engine = create_engine(url=f"sqlite:///data/spotify_music_history.db")
base.metadata.create_all(engine)

def update_tracks(tracks: list[dict[str]]): 
    if not tracks:
        return

    insert_stmt = insert(MusicSchema).values(tracks)

    on_conflict_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["played_at"],
        set_={col: insert_stmt.excluded[col] for col in tracks[0]}
    )

    with engine.begin() as connection:
        connection.execute(on_conflict_stmt)

import time
from os import getenv
from dotenv import load_dotenv
load_dotenv()

update_interval = getenv("UPDATE_INTERVAL")

if not isinstance(update_interval, int):
    try:
        update_interval = int(update_interval)
    except Exception as e:
        logger.info(msg=f"Invalid update interval passed defaulting to 3600s updates. error: {e}")
        update_interval = 3600

if __name__ == "__main__":
    while True:
        try:
            update_tracks(get_recently_played_songs())
        except Exception as e:
            logger.info(msg=f"Failed to fetch tracks: {e}")
            break
        else:
            logger.info(msg=f"Successfully fetched new tracks")
            time.sleep(update_interval)

