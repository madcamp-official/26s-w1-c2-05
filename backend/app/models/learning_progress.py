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
    # 오늘 이미 선정해서 내려준 단어 목록 캐시 (/flashcard, /vocabulary가 공유).
    # voca_selected_ids는 content_id를 comma로 이어붙인 문자열이며, voca_selected_date의
    # 날짜가 오늘이 아니면 캐시를 무시하고 다시 선정한다 (app/utils/learning.py 참고).
    voca_selected_date = Column(DateTime, nullable=True)
    voca_selected_ids = Column(String, nullable=True)