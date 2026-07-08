from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.content import Content
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.grammar_quiz import GrammarQuiz
from app.models.user import User
from app.models.language import Language
from app.models.learning_progress import LearningProgresses
from app.models.refresh_token import RefreshToken
from app.models.eventlog import EventLog
from app.models.dialogue import Dialogue

from app.api import auth, vocabulary, onboarding, me, learning, dashboard
from app.database import Base, engine, SessionLocal

app = FastAPI(
    title="LinguaAI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://languaai.madcamp-kaist.org"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(vocabulary.router)
app.include_router(onboarding.router)
app.include_router(me.router)
app.include_router(learning.router)
app.include_router(dashboard.router)

# 온보딩(language: 1~8)과 프론트 언어 선택지(frontend/src/pages/Onboarding/data/languages.js)의
# id 순서와 반드시 일치해야 한다.
LANGUAGE_SEED = [
    "English", "Japanese", "Chinese", "Spanish",
    "French", "German", "Italian", "Vietnamese",
]

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Language).count() == 0:
            db.add_all(Language(lang_id=i, language=name) for i, name in enumerate(LANGUAGE_SEED, start=1))
            db.commit()
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}