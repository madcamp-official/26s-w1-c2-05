from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserProfileResponse
from app.models.learning_progress import LearningProgresses
from app.models.user import User
from app.models.language import Language

from app.utils.security import get_current_user

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

