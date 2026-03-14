from fastapi import FastAPI, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select

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
    title="GameBaaS API",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"status": "online"}

@app.get("/leaderboard")
def get_leaderboard(session: Session = Depends(get_session)):
    statement = select(Score).order_by(Score.score.desc()).limit(10)
    scores = session.exec(statement).all()
    return {"top_players": scores}

@app.post("/submit_score")
def submit_new_score(new_score: Score, session: Session = Depends(get_session)):
    session.add(new_score)
    session.commit()
    session.refresh(new_score)
    return {"message": "Scor salvat!", "scor_primit": new_score}