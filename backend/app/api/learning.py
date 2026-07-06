from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vocabulary import VocabularyResponse
from app.models.content import Content
from app.models.vocabulary import Vocabulary
from app.models.grammar import Grammar
from app.models.grammar_quiz import GrammarQuiz
from app.models.learning_progress import LearningProgresses
from app.models.language import Language
from app.models.user import User
from app.models.eventlog import EventLog

from app.utils.security import get_current_user

import random

router = APIRouter()

@router.get("/flashcard")
async def get_flashcard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 이벤트 기록을 기반으로 사용자의 학습 수준을 추정하고, 그에 맞는 플래시카드를 제공해야 한다.
    '''
    # 헤더로부터 사용자 정보를 가져와야 한다. (JWT 토큰)
    user_id = get_current_user(access_token, db).user_id
    event_logs = db.query(EventLog).filter(EventLog.user_id == user_id).all()
    '''

    # 일단 지금은 랜덤하게 단어 5개를 추출해서 의미의 선택지와 함께 제공
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    vocabulary_content_id_list = db.query(Content.content_id).filter(Content.lang_id == current_user_lang_id, Content.type == 1).order_by(func.random()).limit(5).all()
    vocabulary_content_id_list = [content_id for (content_id,) in vocabulary_content_id_list]
    print(vocabulary_content_id_list)
    vocabulary_list =[]
    for content_id in vocabulary_content_id_list:
        vocabulary_list.append(db.query(Vocabulary).filter(Vocabulary.content_id == content_id).first())
    language = db.query(Language).filter(Language.lang_id == current_user_lang_id).first()

    #key 중 level을 제거하고 선택지 추가.
    refined_flashcard_list = []
    i = 1
    for voca in vocabulary_list:
        random_voca_list = db.query(Vocabulary).filter(Vocabulary.content_id != voca.content_id).order_by(func.random()).limit(3).all()
        random_voca_list.append(voca)
        choice_list = []
        for choice in random_voca_list:
            choice_list.append(choice.meaning)
        random.shuffle(choice_list)
        answer = choice_list.index(voca.meaning) + 1
        refined_voca = {
            "number": i,
            "content_id": voca.content_id,
            "language": language.language,
            "word": voca.word,
            "choices": choice_list,
            "answer": answer,
        }
        refined_flashcard_list.append(refined_voca)
        i += 1

    return {"vocabularies": refined_flashcard_list}

@router.get("/grammar")
async def get_grammar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 일단 지금은 랜덤하게 문법 5개를 추출해서 퀴즈와 함께 제공
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    grammar_list = db.query(Grammar).filter(Grammar.lang_id == current_user_lang_id).order_by(func.random()).limit(5).all()

    #key 중 level을 제거하고 선택지 추가.
    refined_grammar_list = []
    i = 1
    for grammar in grammar_list:
        random_quiz_list = db.query(GrammarQuiz).filter(GrammarQuiz.grammar_content_id == grammar.content_id).order_by(func.random()).limit(5).all()
        quiz_list = []
        for quiz in random_quiz_list:
            quiz_list.append({"quiz": quiz.problem,
                              "quiz_content_id": quiz.content_id,
                              "answer": quiz.answer})
        refined_grammar = {
            "number": i,
            "content_id": grammar.content_id,
            "subject": grammar.subject,
            "explanation": grammar.grammar_expl,
            "quiz": quiz_list,
        }
        refined_grammar_list.append(refined_grammar)
        i += 1
    return {"grammars": refined_grammar_list}


class AnswerLogRequest(BaseModel):
    content_id: int
    type: str
    response_time: float
    is_correct: bool
    time: datetime


@router.post("/answerlog")
async def post_answerlog(
    body: AnswerLogRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user_lang_id = db.query(LearningProgresses).filter(
        current_user.current_learning_id == LearningProgresses.learning_id
    ).first().lang_id

    event_log = EventLog(
        user_id=current_user.user_id,
        content_id=body.content_id,
        lang_id=current_user_lang_id,
        type=body.type,
        response_time=round(body.response_time),
        is_correct=body.is_correct,
        time_studied=body.time,
    )
    db.add(event_log)
    db.commit()

    return {"detail": "기록되었습니다"}