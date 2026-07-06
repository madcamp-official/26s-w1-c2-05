from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.answerlog import AnswerResponse

from app.models.vocabulary import Vocabulary
from app.models.learning_progress import LearningProgresses
from app.models.language import Language
from app.models.user import User
from app.models.eventlog import EventLog

from app.utils.security import get_current_user
from app.utils.learning import (
    select_vocabulary_for_today,
    select_grammar_for_today,
    select_grammar_quizzes,
)

import random

router = APIRouter()

@router.get("/flashcard")
async def get_flashcard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 이벤트 기록(event_logs)을 기반으로 사용자의 학습 수준을 추정하고, spaced-repetition +
    # 레벨 적응 알고리즘(app/utils/learning.py)으로 오늘 학습할 단어를 선정한다.
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    vocabulary_list = select_vocabulary_for_today(db, current_user.user_id, current_user_lang_id, limit=5)
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
        refined_voca = {
            "number": i,
            "content_id": voca.content_id,
            "language": language,
            "word": voca.word,
            "choices": choice_list,
        }
        refined_flashcard_list.append(refined_voca)
        i += 1

    return {"vocabularies": refined_flashcard_list}

@router.get("/grammar")
async def get_grammar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # event_logs 기반 spaced-repetition + 레벨 적응 알고리즘으로 오늘 학습할 문법을 선정한다.
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    grammar_list = select_grammar_for_today(db, current_user.user_id, current_user_lang_id, limit=5)

    #key 중 level을 제거하고 선택지 추가.
    refined_grammar_list = []
    i = 1
    for grammar in grammar_list:
        random_quiz_list = select_grammar_quizzes(db, current_user.user_id, current_user_lang_id, grammar.content_id, limit=5)
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

type_converter = {"flash": 1, "grammar_quiz": 2, "dialogue": 3}

@router.post("/answerlog")
async def post_answer(user_answer: AnswerResponse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    type_int = type_converter[user_answer.type]
    if type_int is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 접근: 학습 type이 맞지 않습니다."
        )
    new_event = EventLog(
        user_id = current_user.user_id,
        content_id = user_answer.content_id,
        lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id,
        type = type_int,
        response_time = user_answer.response_time,
        is_correct = user_answer.is_correct,
        time_studied = user_answer.time,
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)