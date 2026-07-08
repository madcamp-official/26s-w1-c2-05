from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.answerlog import AnswerResponse, DialogueResponse

from app.models.vocabulary import Vocabulary
from app.models.learning_progress import LearningProgresses
from app.models.language import Language
from app.models.user import User
from app.models.eventlog import EventLog
from app.models.dialogue import Dialogue
from app.models.grammar import Grammar

from app.utils.security import get_current_user
from app.utils.learning import (
    select_vocabulary_for_today,
    select_grammar_for_today,
    select_grammar_quizzes,
    select_dialogue_for_today,
    parse_flow_stages,
    generate_dialogue_opening_line,
    generate_dialogue_step,
    record_daily_activity,
)

import random

router = APIRouter()

# 카테고리별 "오늘의 학습 목표" 문항/주제 수. 아래 GET 엔드포인트들이 오늘 실제로 내려주는
# 콘텐츠 개수와 일치시켜서, 대시보드(app/api/dashboard.py)가 "오늘 이만큼 풀면 목표 달성"을
# 판단하는 기준으로도 그대로 재사용한다.
DAILY_GOALS = {"voca": 20, "grammar": 3, "dialogue": 1}

@router.get("/flashcard")
async def get_flashcard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 이벤트 기록(event_logs)을 기반으로 사용자의 학습 수준을 추정하고, spaced-repetition +
    # 레벨 적응 알고리즘(app/utils/learning.py)으로 오늘 학습할 단어를 선정한다.
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    vocabulary_list = select_vocabulary_for_today(db, current_user.user_id, current_user_lang_id, limit=DAILY_GOALS["voca"])
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
    # event_logs 기반 spaced-repetition + 레벨 적응 알고리즘으로 오늘 학습할 문법을 선정한다.
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    grammar_list = select_grammar_for_today(db, current_user.user_id, current_user_lang_id, limit=DAILY_GOALS["grammar"])

    #key 중 level을 제거하고 선택지 추가.
    refined_grammar_list = []
    i = 1
    for grammar in grammar_list:
        random_quiz_list = select_grammar_quizzes(db, current_user.user_id, current_user_lang_id, grammar.content_id, limit=10)
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

@router.get("/grammar/all")
async def get_all_grammar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 오늘의 학습(select_grammar_for_today)과 달리 spaced-repetition 선별 없이,
    # 현재 학습 언어의 전체 문법 개념을 level 순으로 반환한다 (커리큘럼 조회용, 퀴즈 미포함).
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    grammar_list = (
        db.query(Grammar)
        .filter(Grammar.lang_id == current_user_lang_id)
        .order_by(Grammar.level, Grammar.content_id)
        .all()
    )

    refined_grammar_list = [
        {
            "content_id": grammar.content_id,
            "level": grammar.level,
            "subject": grammar.subject,
            "explanation": grammar.grammar_expl,
        }
        for grammar in grammar_list
    ]
    return {"grammars": refined_grammar_list}

type_converter = {"flash": 1, "grammar": 2, "dialogue": 3}

@router.get("/dialogue")
async def get_dialogue(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    #content_id, subject, flow, content는 current_user의 이벤트로그를 참조해서 고름.
    #회화 주제 선정 알고리즘은 app/utils/learning.py의 select_dialogue_for_today 참고.
    #content는 LLM(app/api/gemini.py)에 subject/flow/추천 단어를 넣어 생성한 대화 시작 문장이다.
    current_user_lang_id = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first().lang_id
    dialogue_list = select_dialogue_for_today(db, current_user.user_id, current_user_lang_id, limit=DAILY_GOALS["dialogue"])
    if not dialogue_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="학습할 수 있는 회화 콘텐츠가 없습니다."
        )
    dialogue = dialogue_list[0]
    language = db.query(Language).filter(Language.lang_id == dialogue.lang_id).first()

    flow_stages = parse_flow_stages(dialogue.flow)
    first_flow = flow_stages[0]
    opening = generate_dialogue_opening_line(db, dialogue, language.language, current_user.user_id)

    return {
        "content_id": dialogue.content_id,
        "subject": dialogue.subject,
        "flow": first_flow,
        "flow_stages": flow_stages,
        "content": opening.content,
        "translation": opening.translation,
    }

@router.post("/answerlog")
async def post_answer(user_answer: AnswerResponse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    type_int = type_converter.get(user_answer.type)
    if type_int is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 접근: 학습 type이 맞지 않습니다."
        )
    progress = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first()
    new_event = EventLog(
        user_id = current_user.user_id,
        content_id = user_answer.content_id,
        lang_id = progress.lang_id,
        type = type_int,
        response_time = user_answer.response_time,
        is_correct = user_answer.is_correct,
        time_studied = user_answer.time,
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    record_daily_activity(db, progress)

@router.post("/dialoguelog")
async def get_more_dialogue(user_answer: DialogueResponse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    #user_answer를 기반으로 LLM(app/api/gemini.py)에 답변 제공 -> LLM이 constraint에 따라 답변을 평가하고
    #피드백 작성, flow 등을 참고해서 다음 대화 흐름에 맞는 문장 생성. (app/utils/learning.py의 generate_dialogue_step)
    #is_end 변수는 LLM의 advance_flow 판단(현재 flow를 통과했는지)을 받아, Dialogue.flow 목록에서
    #현재 flow가 마지막 단계인지로 서버가 구조적으로 판단한다 (LLM이 flow 위치를 직접 세다가
    #착각해 대화가 조기 종료/무한 반복되는 것을 방지하기 위함).
    #is_end가 true면 get_more_dialogue를 return하기 전에 eventlog에 날짜, 정답 여부(전체 대화 맥락
    #기반 정답 여부 평가는 추후 고도화 대상이며, 지금은 True로 고정한다) 등을 포함하여 db에 추가한다.
    dialogue = db.query(Dialogue).filter(Dialogue.content_id == user_answer.content_id).first()
    if dialogue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회화 콘텐츠를 찾을 수 없습니다."
        )
    if user_answer.flow not in parse_flow_stages(dialogue.flow):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 접근: flow가 해당 회화 콘텐츠의 흐름에 속하지 않습니다."
        )

    language = db.query(Language).filter(Language.lang_id == dialogue.lang_id).first()
    step = generate_dialogue_step(
        db, dialogue, language.language, user_answer.flow, user_answer.response, current_user.user_id,
        history=user_answer.history,
    )

    progress = db.query(LearningProgresses).filter(current_user.current_learning_id == LearningProgresses.learning_id).first()
    record_daily_activity(db, progress)

    if step.is_end:
        new_event = EventLog(
            user_id = current_user.user_id,
            content_id = dialogue.content_id,
            lang_id = progress.lang_id,
            type = type_converter["dialogue"],
            response_time = user_answer.response_time,
            is_correct = True,  # TODO(LLM 연동 고도화): 전체 대화 맥락을 바탕으로 한 정답 여부 평가로 교체.
            time_studied = user_answer.time,
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

    return {
        "content_id": dialogue.content_id,
        "end": step.is_end,
        "subject": dialogue.subject,
        "flow": step.flow,
        "flow_stages": parse_flow_stages(dialogue.flow),
        "content": step.content,
        "translation": step.translation,
        "feedback": step.feedback,
    }
