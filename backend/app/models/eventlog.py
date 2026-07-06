from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base


class EventLog(Base):
    __tablename__ = "event_logs"

    # 사용자가 모르는 정수 id
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    content_id = Column(Integer, nullable=False)
    lang_id = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    response_time = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_studied = Column(DateTime, nullable=False) 