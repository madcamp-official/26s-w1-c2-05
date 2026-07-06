from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class GrammarQuiz(Base):
    __tablename__ = "grammar_quizzes"

    content_id = Column(Integer, ForeignKey("contents.content_id"), primary_key=True, nullable=False)
    grammar_content_id = Column(Integer, nullable=False, index=True)
    problem = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    content = relationship("Content", back_populates="grammar_quiz")  