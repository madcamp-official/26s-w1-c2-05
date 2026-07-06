from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Grammar(Base):
    __tablename__ = "grammars"

    content_id = Column(Integer, ForeignKey("contents.content_id"), primary_key=True, nullable=False)
    lang_id = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    grammar_expl = Column(String, nullable=False)

    content = relationship("Content", back_populates="grammar")