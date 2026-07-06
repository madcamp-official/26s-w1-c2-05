from fastapi import FastAPI

from app.models.content import Content
from app.models.grammar import Grammar
from app.models.vocabulary import Vocabulary
from app.models.grammar_quiz import GrammarQuiz
from app.models.user import User
from app.models.language import Language
from app.models.learning_progress import LearningProgresses
from app.models.refresh_token import RefreshToken
from app.models.eventlog import EventLog

from app.api import auth, vocabulary, onboarding, me, learning
from app.database import Base, engine

app = FastAPI(
    title="LinguaAI",
    version="0.1.0",
)
app.include_router(auth.router)
app.include_router(vocabulary.router)
app.include_router(onboarding.router)
app.include_router(me.router)
app.include_router(learning.router)

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}