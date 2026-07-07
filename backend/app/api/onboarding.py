from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import OnboardingResponse
from app.models.learning_progress import LearningProgresses
from app.models.user import User

from app.utils.security import get_current_user

router = APIRouter()

StudyLevel = {
    "A1": 1,
    "A2": 2,
    "B1": 3,
    "B2": 4,
    "C1": 5,
    "C2": 6
}

@router.post("/onboarding")
async def post_survey(user_onboard: OnboardingResponse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 사용자의 설문조사 결과를 기반으로 학습 진도를 초기 설정 후 저장, 그리고 사용자에게 바로 매핑

    lang_id = user_onboard.language
    level_id = StudyLevel.get(user_onboard.level, 0)
    study_goal = user_onboard.StudyGoal

    if lang_id < 1 or lang_id > 8 or level_id == 0 or study_goal < 1 or study_goal > 365 or current_user.current_learning_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바르지 않은 응답입니다"
        )

    # 학습 진도 초기 설정 후 DB에 저장
    learning_progress = LearningProgresses( # 자동 생성되도록 None으로 설정
        user_id=current_user.user_id,
        lang_id=lang_id,
        target_days=study_goal,
        study_days=0,
        last_studied=None,
        daily_streak=0,
        language_total=0,
        current_level=level_id,
        total_answers=0,
        correct_answers=0
    )

    db.add(learning_progress)
    db.commit()
    current_user.current_learning_id = learning_progress.learning_id  # 사용자 모델에 학습 진도 ID 매핑
    current_user.current_level = level_id
    db.add(current_user)
    db.commit()

    return {"details": "다 되었습니다! 이제 메인화면으로 이동합니다.", "userInfo": {
        "userID": current_user.user_id,
        "DailyStreak": 0}}

