from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Vocabulary(Base):
    __tablename__ = "vocabularies"

    content_id = Column(Integer, ForeignKey("contents.content_id"), primary_key=True, index=True)
    level = Column(Integer, nullable=False)
    word = Column(String, nullable=False)
    meaning = Column(String, nullable=False)
    example = Column(String, nullable=True)

    content = relationship("Content", back_populates="vocabulary")