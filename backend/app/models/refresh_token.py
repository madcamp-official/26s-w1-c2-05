from sqlalchemy import Column, Integer, String
from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token = Column(String, primary_key=True, index=True, nullable=False)
    id = Column(Integer, nullable=False)
