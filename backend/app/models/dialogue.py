from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Dialogue(Base):
    __tablename__ = "dialogues"

    content_id = Column(Integer, ForeignKey("contents.content_id"), primary_key=True, nullable=False)
    subject = Column(String, nullable=False)
    flow = Column(String, nullable=False) #하나의 string에 flow를 comma로 구분하여 저장. 왼쪽부터 대화의 흐름 시작.
    lang_id = Column(Integer, nullable=False)

    content = relationship("Content", back_populates="dialogue")