from sqlalchemy import Column, Integer, String
from app.database import Base


class Language(Base):
    __tablename__ = "languages"

    # 사용자가 모르는 정수 id
lang_id = Column(Integer, primary_key=True, index=True)
language = Column(String, nullable=False)