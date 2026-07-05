from fastapi import FastAPI

from app.api import auth, vocabulary
from app.database import Base, engine

app = FastAPI(
    title="LinguaAI",
    version="0.1.0",
)
app.include_router(auth.router)
app.include_router(vocabulary.router)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}