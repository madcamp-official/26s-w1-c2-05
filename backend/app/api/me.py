from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserProfileResponse, UserDashboardResponse
from app.models.learning_progress import LearningProgresses
from app.models.user import User
from app.models.language import Language

from app.utils.security import get_current_user
from app.utils.learning import analyze_category_performance
from math import floor

router = APIRouter()

@router.get("/users/me", response_model=UserProfileResponse)
async def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 사용자의 프로필 정보 및 학습 진도 정보를 가져와서 반환
    current_learning_progress = db.query(LearningProgresses).filter(LearningProgresses.learning_id == user.current_learning_id).first() if user.current_learning_id else None
    lang_id = current_learning_progress.lang_id
    language_name = db.query(Language.language).filter(Language.lang_id == lang_id).scalar() if lang_id else None
    target_days = current_learning_progress.target_days
    studied_days = current_learning_progress.study_days
    daily_streak = current_learning_progress.daily_streak
    profile_data = {
        "userID": user.user_id,
        "email": user.email,
        "current_language": language_name,
        "target_days": target_days,
        "studied_days": studied_days,
        "daily_streak": daily_streak,
    }

    return profile_data

@router.get("/dashboard", response_model=UserDashboardResponse)
async def get_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_learning_progress = db.query(LearningProgresses).filter(LearningProgresses.learning_id == user.current_learning_id).first()
    lang_id = current_learning_progress.lang_id
    # 취약점/가장 개선된 범주 분석: app/utils/learning.py의 analyze_category_performance 참고.
    performance = analyze_category_performance(db, user.user_id, lang_id)
    response = UserDashboardResponse(
      language=db.query(Language.language).filter(Language.lang_id == lang_id).scalar(),
      daily_streak=current_learning_progress.daily_streak,
      language_total=current_learning_progress.language_total,
      # learning_progresses의 total_answers/correct_answers로 정답률(%)을 계산.
      accuracy_rate=0 if current_learning_progress.total_answers == 0 else floor(
          current_learning_progress.correct_answers / current_learning_progress.total_answers * 100
      ),
      most_weak=performance["weakness"],
      most_improved=performance["most_improved"],
      feedback_voca="TODO: 구현예정",  # TODO
      feedback_grammar="TODO: 구현예정",  # TODO
      feedback_dialogue="TODO: 구현예정",  # TODO
      error_trend={"voca": [], "grammar": [], "dialogue": []},  # TODO
    )
    return response


    

