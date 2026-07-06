from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from app.database import Base


class Content(Base):
    __tablename__ = "contents"

    content_id = Column(Integer, primary_key=True, index=True)
    type = Column(Integer, nullable=False)
    lang_id = Column(Integer, nullable=False)

    vocabulary = relationship(
        "Vocabulary", back_populates="content", uselist=False, cascade="all, delete-orphan"
    )
    grammar = relationship(
        "Grammar", back_populates="content", uselist=False, cascade="all, delete-orphan"
    )
    grammar_quiz = relationship(
        "GrammarQuiz", back_populates="content", uselist=False, cascade="all, delete-orphan"
    )