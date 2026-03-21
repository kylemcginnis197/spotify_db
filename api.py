from collections import Counter
from datetime import datetime, timedelta
from os import getenv

from dateutil.relativedelta import relativedelta
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# --- DB setup ---

engine = create_engine("sqlite:///data/spotify_music_history.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class MusicHistory(Base):
    __tablename__ = "music_history"
    played_at = Column(DateTime, primary_key=True)
    track_name = Column(String, nullable=True)
    track_uri = Column(String, nullable=True)
    album_name = Column(String, nullable=True)
    album_uri = Column(String, nullable=True)
    artist_names = Column(String, nullable=True)
    artist_uris = Column(String, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Auth ---

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(key: str = Security(api_key_header)):
    expected = getenv("API_KEY")
    if not key or key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key


# --- Pydantic models ---

class HistoryItem(BaseModel):
    played_at: datetime
    track_name: str | None
    track_uri: str | None
    album_name: str | None
    album_uri: str | None
    artist_names: str | None
    artist_uris: str | None

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[HistoryItem]


class TopEntry(BaseModel):
    name: str
    play_count: int


class SummaryResponse(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    top_tracks: list[TopEntry]
    top_artists: list[TopEntry]
    top_albums: list[TopEntry]


# --- Period helper ---

def resolve_period(period: str) -> tuple[datetime, datetime]:
    end = datetime.utcnow()
    match period:
        case "weekly":
            start = end - timedelta(days=7)
        case "biweekly":
            start = end - timedelta(days=14)
        case "monthly":
            start = end - relativedelta(months=1)
        case "quarterly":
            start = end - relativedelta(months=3)
        case "yearly":
            start = end - relativedelta(years=1)
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown period '{period}'. Valid values: weekly, biweekly, monthly, quarterly, yearly")
    return start, end


# --- App ---

app = FastAPI(title="Spotify Tracker API")


@app.get("/history", response_model=HistoryResponse)
def get_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: str = Depends(get_api_key),
):
    if limit > 500:
        limit = 500
    total = db.query(func.count(MusicHistory.played_at)).scalar()
    items = (
        db.query(MusicHistory)
        .order_by(MusicHistory.played_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return HistoryResponse(total=total, limit=limit, offset=offset, items=items)


@app.get("/summary", response_model=SummaryResponse)
def get_summary(
    period: str,
    top_n: int = 10,
    db: Session = Depends(get_db),
    _: str = Depends(get_api_key),
):
    if top_n > 50:
        top_n = 50
    start, end = resolve_period(period)
    rows = (
        db.query(MusicHistory)
        .filter(MusicHistory.played_at >= start, MusicHistory.played_at <= end)
        .all()
    )

    track_counter: Counter = Counter()
    artist_counter: Counter = Counter()
    album_counter: Counter = Counter()

    for row in rows:
        if row.track_name:
            track_counter[row.track_name] += 1
        if row.album_name:
            album_counter[row.album_name] += 1
        if row.artist_names:
            for artist in row.artist_names.split(", "):
                artist_counter[artist.strip()] += 1

    def top(counter: Counter) -> list[TopEntry]:
        return [TopEntry(name=name, play_count=count) for name, count in counter.most_common(top_n)]

    return SummaryResponse(
        period=period,
        start_date=start,
        end_date=end,
        top_tracks=top(track_counter),
        top_artists=top(artist_counter),
        top_albums=top(album_counter),
    )
