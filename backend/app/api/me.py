from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserProfileResponse, LanguageSwitchRequest, LanguageOption
from app.models.learning_progress import LearningProgresses
from app.models.user import User
from app.models.language import Language

from app.utils.security import get_current_user
from app.utils.constants import STUDY_LEVELS, STUDY_LEVEL_NAMES

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

@router.get("/me/languages", response_model=list[LanguageOption])
async def get_my_languages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 언어 전환 모달에서 보여줄 목록: 지원하는 8개 언어 각각에 대해, 이 사용자가
    # 이미 학습을 시작한 적이 있는지(진도 보존 대상)와 현재 학습 중인 언어인지를 함께 내려준다.
    languages = db.query(Language).order_by(Language.lang_id).all()
    progresses = db.query(LearningProgresses).filter(LearningProgresses.user_id == user.user_id).all()
    progress_by_lang = {p.lang_id: p for p in progresses}

    result = []
    for lang in languages:
        progress = progress_by_lang.get(lang.lang_id)
        result.append({
            "lang_id": lang.lang_id,
            "language": lang.language,
            "in_progress": progress is not None,
            "is_current": bool(progress and user.current_learning_id == progress.learning_id),
            "current_level": STUDY_LEVEL_NAMES.get(progress.current_level) if progress else None,
            "studied_days": progress.study_days if progress else None,
        })
    return result

@router.post("/me/language")
async def switch_language(payload: LanguageSwitchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 언어별로 LearningProgresses row를 따로 유지해, 전환 후 되돌아와도 진도가 보존되게 한다.
    if payload.language < 1 or payload.language > 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바르지 않은 언어입니다")

    existing = db.query(LearningProgresses).filter(
        LearningProgresses.user_id == user.user_id,
        LearningProgresses.lang_id == payload.language,
    ).first()

    if existing:
        user.current_learning_id = existing.learning_id
        user.current_level = existing.current_level
    else:
        level_id = STUDY_LEVELS.get(payload.level or "", 0)
        study_goal = payload.StudyGoal or 0
        if level_id == 0 or study_goal < 1 or study_goal > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="처음 시작하는 언어는 레벨과 목표 기간을 함께 보내야 합니다",
            )
        new_progress = LearningProgresses(
            user_id=user.user_id,
            lang_id=payload.language,
            target_days=study_goal,
            study_days=0,
            last_studied=None,
            daily_streak=0,
            language_total=0,
            current_level=level_id,
            total_answers=0,
            correct_answers=0,
        )
        db.add(new_progress)
        db.commit()
        user.current_learning_id = new_progress.learning_id
        user.current_level = level_id

    db.add(user)
    db.commit()

    language_name = db.query(Language.language).filter(Language.lang_id == payload.language).scalar()
    return {"detail": "학습 언어가 전환되었습니다.", "current_language": language_name}

