from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Field, Session, SQLModel, create_engine, select

API_KEY = "ATOD_SECRET_KEY_2026"
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(status_code=403, detail="Acces Respins: API Key invalidă!")
    return api_key_header

class Score(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    score: int
    game_id: str

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI(
    title="AtodCore API",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"status": "online"}

@app.get("/leaderboard")
def get_global_leaderboard(session: Session = Depends(get_session)):
    statement = select(Score).order_by(Score.score.desc()).limit(10)
    scores = session.exec(statement).all()
    return {"top_players": scores}

@app.get("/leaderboard/{game_id}")
def get_game_leaderboard(game_id: str, session: Session = Depends(get_session)):
    statement = select(Score).where(Score.game_id == game_id).order_by(Score.score.desc()).limit(10)
    scores = session.exec(statement).all()
    return {"game": game_id, "top_players": scores}

@app.post("/submit_score")
def submit_new_score(new_score: Score, session: Session = Depends(get_session), api_key: str = Depends(get_api_key)):
    statement = select(Score).where(Score.username == new_score.username).where(Score.game_id == new_score.game_id)
    existing_score = session.exec(statement).first()

    if existing_score:
        if new_score.score > existing_score.score:
            existing_score.score = new_score.score
            session.add(existing_score)
            session.commit()
            session.refresh(existing_score)
            return {"message": "Nou record salvat!", "scor_primit": existing_score}
        else:
            return {"message": "Scorul nu a fost depășit.", "scor_primit": existing_score}
    else:
        session.add(new_score)
        session.commit()
        session.refresh(new_score)
        return {"message": "Scor nou salvat!", "scor_primit": new_score}