from sqlalchemy import Column, DateTime, Integer, String
from app.database import Base


class LearningProgresses(Base):
    __tablename__ = "learning_progresses"

    # 사용자가 모르는 정수 id
    learning_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    lang_id = Column(Integer, nullable=False)
    target_days = Column(Integer, nullable=False)
    study_days = Column(Integer, nullable=False)
    last_studied = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, nullable=False)
    language_total = Column(Integer, nullable=False)
    current_level = Column(Integer, nullable=False)
    total_answers = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)