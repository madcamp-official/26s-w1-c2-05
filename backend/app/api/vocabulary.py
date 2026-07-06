from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vocabulary import VocabularyResponse
from app.models.vocabulary import Vocabulary
from app.models.user import User

from app.utils.security import get_current_user

router = APIRouter()

@router.get("/vocabulary", response_model=VocabularyResponse)
async def get_vocabulary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 이벤트 기록을 기반으로 사용자의 학습 수준을 추정하고, 그에 맞는 단어를 추천해야 한다.
    '''
    # 헤더로부터 사용자 정보를 가져와야 한다. (JWT 토큰)
    user_id = get_current_user(access_token, db).user_id
    event_logs = db.query(EventLog).filter(EventLog.user_id == user_id).all()
    '''

    # 일단 지금은 랜덤하게 단어 5개를 추출해서 뜻, 의미, 예시 세 가지를 반환하도록 한다.
    vocabulary_list = db.query(Vocabulary).order_by(func.random()).limit(5).all()
    #key 중 level을 제거하고 프론트엔드가 알 수 있도록 임의 순서 key, value 페어도 부여.
    refined_voca_list = []
    i = 1
    for voca in vocabulary_list:
        refined_voca = {
            "number": i,
            "content_id": voca.content_id,
            "word": voca.word,
            "meaning": voca.meaning,
            "example": voca.example,
        }
        refined_voca_list.append(refined_voca)
        i += 1

    return {"vocabularies": refined_voca_list}

