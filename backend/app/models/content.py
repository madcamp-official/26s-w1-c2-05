from sqlalchemy import Column, Integer, String
from app.database import Base


class Content(Base):
    __tablename__ = "contents"

    # 사용자가 모르는 정수 id
    content_id = Column(Integer, primary_key=True, index=True)
    type = Column(int, nullable=False)
    lang_id = Column(int, nullable=False)