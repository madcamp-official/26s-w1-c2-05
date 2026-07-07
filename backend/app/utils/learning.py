'''
학습 알고리즘이 구현된 모듈입니다.

오늘 학습할 단어(Vocabulary)/문법(Grammar)과 그에 딸린 퀴즈를, 사용자의 event_logs
기록을 바탕으로 선정한다. 근거로 삼은 이론/논문은 다음과 같다.

- Ebbinghaus, H. (1885). Über das Gedächtnis. 지수적 망각 곡선(forgetting curve).
- Wozniak, P. A. (1990). SuperMemo 2 (SM-2). 정답/오답 이력에 따라 복습 간격을 조절하는
  spaced-repetition 알고리즘의 원형.
- Settles, B., & Meeder, B. (2016). "A Trainable Spaced Repetition Model for Language
  Learning" (ACL). Duolingo의 Half-Life Regression(HLR) — 정답/오답 횟수로 기억의
  반감기(half-life)를 추정해 현재 회상 확률(recall probability)을 계산한다. 이 모듈은
  실제 학습된 회귀 계수 대신, 논문이 보고한 경향(정답은 반감기를 늘리고 오답은 크게
  줄임)을 반영한 고정 가중치를 사용한 경량화 버전이다.
- Krashen, S. (1985). The Input Hypothesis. i+1(comprehensible input) 가설 — 사용자가
  안정적으로 수행하는 레벨의 바로 다음 단계를 제공해야 학습 효과가 가장 크다는 근거로,
  레벨 적응(난이도 조정) 로직에 사용.
- Leitner, S. (1972). So lernt man lernen. Leitner box 시스템 — "복습 대상 vs 신규 학습"
  비율을 세션마다 일정하게 섞는 아이디어의 근거.
- Roediger, H. L., & Karpicke, J. D. (2006). "The Power of Testing Memory" (testing
  effect) — 아직 정답률이 낮거나 시도하지 않은 문제를 우선 노출하는 퀴즈 선정 로직의 근거.
'''

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api import gemini
from app.models.content import Content
from app.models.dialogue import Dialogue
from app.models.eventlog import EventLog
from app.models.grammar import Grammar
from app.models.grammar_quiz import GrammarQuiz
from app.models.vocabulary import Vocabulary


import random


# ---------------------------------------------------------------------------
# Half-Life Regression(HLR) 기반 회상 확률 추정
# ---------------------------------------------------------------------------

# 실제 서비스가 성숙하면 이 가중치는 로지스틱/선형 회귀로 재학습되어야 하지만,
# 데이터가 충분히 쌓이기 전까지는 SM-2/HLR 논문이 공통적으로 보고하는 경향
# (정답은 반감기를 늘리고, 오답은 반감기를 더 크게 줄임)을 반영한 고정값을 사용한다.
_HLR_BIAS = 1.0
_HLR_WEIGHT_CORRECT = 0.35
_HLR_WEIGHT_INCORRECT = -0.85

_MIN_HALF_LIFE_DAYS = 0.5
_MAX_HALF_LIFE_DAYS = 250.0

# 예측 회상 확률이 이 값 미만이면 "복습이 필요한 항목"으로 간주한다.
_REVIEW_RECALL_THRESHOLD = 0.85
# 오늘 세션에서 복습 항목이 채우는 목표 비율 (Leitner 식 복습/신규 혼합).
_REVIEW_RATIO = 0.6

# CEFR 레벨 범위 (A1~C2), app/api/onboarding.py의 StudyLevel과 동일하게 맞춘다.
_MIN_LEVEL, _MAX_LEVEL = 1, 6
# 특정 레벨을 "숙달"로 판단하기 위한 최소 정답률/시도 횟수 (i+1 승급 조건).
_LEVEL_MASTERY_THRESHOLD = 0.85
_LEVEL_MIN_ATTEMPTS = 6


def _half_life_days(n_correct: int, n_incorrect: int) -> float:
    '''정답/오답 누적 횟수로부터 기억의 반감기(half-life, 단위: 일)를 추정한다.'''
    exponent = _HLR_BIAS + _HLR_WEIGHT_CORRECT * n_correct + _HLR_WEIGHT_INCORRECT * n_incorrect
    half_life = 2.0 ** exponent
    return min(max(half_life, _MIN_HALF_LIFE_DAYS), _MAX_HALF_LIFE_DAYS)


def estimate_recall_probability(n_correct: int, n_incorrect: int, days_since_last_study: float) -> float:
    '''
    지수 망각 곡선(Ebbinghaus, 1885)에 따라 현재 시점의 기억 유지 확률(0~1)을 추정한다.

        p = 2 ** (-Δt / half_life)
    '''
    if days_since_last_study <= 0:
        return 1.0
    half_life = _half_life_days(n_correct, n_incorrect)
    return 2.0 ** (-days_since_last_study / half_life)


@dataclass
class ContentStats:
    content_id: int
    n_correct: int
    n_incorrect: int
    n_total: int
    last_studied: datetime | None

    @property
    def is_new(self) -> bool:
        return self.n_total == 0


def _aggregate_event_stats(
    db: Session, user_id: str, lang_id: int, content_ids: Sequence[int]
) -> dict[int, ContentStats]:
    '''주어진 content_id들에 대한 사용자의 event_logs를 (정답 수, 오답 수, 마지막 학습 시각)으로 집계한다.'''
    if not content_ids:
        return {}

    rows = (
        db.query(
            EventLog.content_id,
            func.sum(case((EventLog.is_correct == True, 1), else_=0)).label("n_correct"),
            func.count(EventLog.event_id).label("n_total"),
            func.max(EventLog.time_studied).label("last_studied"),
        )
        .filter(
            EventLog.user_id == user_id,
            EventLog.lang_id == lang_id,
            EventLog.content_id.in_(content_ids),
        )
        .group_by(EventLog.content_id)
        .all()
    )

    stats: dict[int, ContentStats] = {}
    for content_id, n_correct, n_total, last_studied in rows:
        n_correct = int(n_correct or 0)
        n_total = int(n_total or 0)
        stats[content_id] = ContentStats(
            content_id=content_id,
            n_correct=n_correct,
            n_incorrect=n_total - n_correct,
            n_total=n_total,
            last_studied=last_studied,
        )
    return stats


# ---------------------------------------------------------------------------
# 레벨(CEFR) 적응 로직 — Krashen(1985)의 i+1 comprehensible input
# ---------------------------------------------------------------------------

def _content_level_map(db: Session, lang_id: int, model) -> dict[int, int]:
    '''주어진 모델(Vocabulary 또는 Grammar)에 대해 해당 언어의 {content_id: level} 매핑을 반환한다.'''
    if model is Vocabulary:
        rows = (
            db.query(Vocabulary.content_id, Vocabulary.level)
            .join(Content, Content.content_id == Vocabulary.content_id)
            .filter(Content.lang_id == lang_id)
            .all()
        )
    else:
        rows = db.query(Grammar.content_id, Grammar.level).filter(Grammar.lang_id == lang_id).all()
    return dict(rows)


def _estimate_target_level(
    db: Session, user_id: str, lang_id: int, level_map: dict[int, int]
) -> int:
    '''
    사용자가 각 레벨에서 보인 정답률을 근거로 오늘 학습할 목표 레벨을 추정한다.
    - event_log 기록이 없으면 최저 레벨(A1=1)에서 시작한다.
    - 어떤 레벨의 누적 시도 수/정답률이 임계치를 넘으면 다음 레벨로 승급시킨다(i+1).
    - 아직 숙달하지 못한 레벨을 만나면 그 자리에 머무른다.
    '''
    if not level_map:
        return _MIN_LEVEL

    content_ids = list(level_map.keys())
    rows = (
        db.query(EventLog.content_id, EventLog.is_correct)
        .filter(
            EventLog.user_id == user_id,
            EventLog.lang_id == lang_id,
            EventLog.content_id.in_(content_ids),
        )
        .all()
    )
    if not rows:
        return _MIN_LEVEL

    per_level_correct: dict[int, int] = {}
    per_level_total: dict[int, int] = {}
    for content_id, is_correct in rows:
        level = level_map.get(content_id)
        if level is None:
            continue
        per_level_total[level] = per_level_total.get(level, 0) + 1
        if is_correct:
            per_level_correct[level] = per_level_correct.get(level, 0) + 1

    target_level = _MIN_LEVEL
    for level in range(_MIN_LEVEL, _MAX_LEVEL + 1):
        total = per_level_total.get(level, 0)
        if total == 0:
            break
        correct = per_level_correct.get(level, 0)
        if total >= _LEVEL_MIN_ATTEMPTS and (correct / total) >= _LEVEL_MASTERY_THRESHOLD:
            target_level = min(level + 1, _MAX_LEVEL)
        else:
            target_level = level
            break

    return target_level


# ---------------------------------------------------------------------------
# 오늘의 학습 항목 선정 (복습 + 신규, spaced-repetition + 레벨 적응 결합)
# ---------------------------------------------------------------------------

def _select_items(db: Session, user_id: str, lang_id: int, model, limit: int) -> list:
    '''
    복습(review)과 신규 학습(new)을 섞어 오늘 학습할 콘텐츠(Vocabulary 또는 Grammar row)를 선정한다.

    우선순위:
      1) 학습 이력이 있는 항목 중 예측 회상 확률이 낮은(망각 위험이 큰) 순서로 복습.
      2) 사용자의 목표 레벨(i+1)에 해당하는 미학습 항목으로 나머지 슬롯을 채움.
      3) 그래도 슬롯이 남으면(콘텐츠 부족) 다음으로 망각 위험이 큰 복습 항목으로 채움.
      4) 위 로직이 모두 실패하면(콘텐츠가 매우 적은 경우) 무작위로 대체.
    '''
    level_map = _content_level_map(db, lang_id, model)
    if not level_map:
        return []

    content_ids = list(level_map.keys())
    stats_map = _aggregate_event_stats(db, user_id, lang_id, content_ids)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    review_candidates: list[tuple[float, int]] = []
    for content_id, stats in stats_map.items():
        if stats.is_new or stats.last_studied is None:
            continue
        last_studied = stats.last_studied
        if last_studied.tzinfo is not None:
            last_studied = last_studied.replace(tzinfo=None)
        days_since = max((now - last_studied).total_seconds() / 86400.0, 0.0)
        p_recall = estimate_recall_probability(stats.n_correct, stats.n_incorrect, days_since)
        if p_recall < _REVIEW_RECALL_THRESHOLD:
            review_candidates.append((p_recall, content_id))

    # 회상 확률이 낮은(망각 위험이 큰) 순서로 정렬
    review_candidates.sort(key=lambda pair: pair[0])

    n_review_slots = min(len(review_candidates), max(round(limit * _REVIEW_RATIO), 0), limit)
    selected_ids = [content_id for _, content_id in review_candidates[:n_review_slots]]

    remaining = limit - len(selected_ids)
    if remaining > 0:
        target_level = _estimate_target_level(db, user_id, lang_id, level_map)
        new_ids_by_level: dict[int, list[int]] = {}
        for content_id, level in level_map.items():
            if content_id in selected_ids or content_id in stats_map:
                continue  # 학습 이력이 있는 항목은 "신규" 후보에서 제외
            new_ids_by_level.setdefault(level, []).append(content_id)

        # 목표 레벨에 가장 가까운 레벨부터 채워 넣는다.
        level_order = sorted(new_ids_by_level.keys(), key=lambda lvl: (abs(lvl - target_level), lvl))
        for level in level_order:
            if remaining <= 0:
                break
            candidates = new_ids_by_level[level]
            random.shuffle(candidates)
            take = candidates[:remaining]
            selected_ids.extend(take)
            remaining -= len(take)

    if len(selected_ids) < limit and len(review_candidates) > n_review_slots:
        extra = [cid for _, cid in review_candidates[n_review_slots:] if cid not in selected_ids]
        selected_ids.extend(extra[: limit - len(selected_ids)])

    if not selected_ids:
        selected_ids = list(level_map.keys())
        random.shuffle(selected_ids)
        selected_ids = selected_ids[:limit]

    rows = db.query(model).filter(model.content_id.in_(selected_ids)).all()
    row_map = {row.content_id: row for row in rows}
    return [row_map[cid] for cid in selected_ids if cid in row_map]


def select_vocabulary_for_today(db: Session, user_id: str, lang_id: int, limit: int = 5) -> list[Vocabulary]:
    '''오늘 학습할 단어(Vocabulary) 목록을 반환한다.'''
    return _select_items(db, user_id, lang_id, Vocabulary, limit)


def select_grammar_for_today(db: Session, user_id: str, lang_id: int, limit: int = 5) -> list[Grammar]:
    '''오늘 학습할 문법(Grammar) 목록을 반환한다.'''
    return _select_items(db, user_id, lang_id, Grammar, limit)


def select_grammar_quizzes(
    db: Session, user_id: str, lang_id: int, grammar_content_id: int, limit: int = 5
) -> list[GrammarQuiz]:
    '''
    특정 문법(grammar_content_id)에 대한 퀴즈 중, 시도한 적 없거나 정답률이 낮은 문제를
    우선적으로 제공한다 (retrieval practice / testing effect, Roediger & Karpicke, 2006).
    '''
    quizzes = (
        db.query(GrammarQuiz).filter(GrammarQuiz.grammar_content_id == grammar_content_id).all()
    )
    if not quizzes:
        return []

    content_ids = [quiz.content_id for quiz in quizzes]
    stats_map = _aggregate_event_stats(db, user_id, lang_id, content_ids)

    def priority(quiz: GrammarQuiz) -> tuple[int, float, float]:
        stats = stats_map.get(quiz.content_id)
        if stats is None or stats.n_total == 0:
            return (0, 0.0, random.random())  # 미시도 문제 최우선
        accuracy = stats.n_correct / stats.n_total
        return (1, accuracy, random.random())  # 정답률이 낮을수록 먼저

    quizzes.sort(key=priority)
    return quizzes[:limit]


# ---------------------------------------------------------------------------
# 회화(Dialogue) 주제 선정
# ---------------------------------------------------------------------------

def select_dialogue_for_today(db: Session, user_id: str, lang_id: int, limit: int = 1) -> list[Dialogue]:
    '''
    오늘 학습할 회화(Dialogue) 주제를 선정한다. Vocabulary/Grammar와 달리 CEFR 레벨 컬럼이
    없으므로 레벨 적응(i+1) 로직은 적용하지 않는다. 대신,
      1) 아직 한 번도 시도하지 않은 주제를 최우선으로 하고(testing effect, Roediger & Karpicke, 2006),
      2) 이미 시도한 주제 중에서는 예측 회상 확률(half-life regression)이 낮은,
         즉 망각 위험이 큰 주제를 우선 복습으로 배정한다.
    '''
    dialogues = db.query(Dialogue).filter(Dialogue.lang_id == lang_id).all()
    if not dialogues:
        return []

    content_ids = [dialogue.content_id for dialogue in dialogues]
    stats_map = _aggregate_event_stats(db, user_id, lang_id, content_ids)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    def priority(dialogue: Dialogue) -> tuple[int, float, float]:
        stats = stats_map.get(dialogue.content_id)
        if stats is None or stats.is_new:
            return (0, 0.0, random.random())  # 미시도 주제 최우선

        last_studied = stats.last_studied
        if last_studied is not None and last_studied.tzinfo is not None:
            last_studied = last_studied.replace(tzinfo=None)
        days_since = max((now - last_studied).total_seconds() / 86400.0, 0.0) if last_studied else 0.0
        p_recall = estimate_recall_probability(stats.n_correct, stats.n_incorrect, days_since)
        return (1, p_recall, random.random())  # 회상 확률이 낮을수록(망각 위험이 클수록) 먼저

    dialogues.sort(key=priority)
    return dialogues[:limit]


# ---------------------------------------------------------------------------
# 회화 흐름(flow) 파싱/진행
#
# Dialogue.flow는 하나의 문자열에 대화 흐름 단계를 comma로 구분해 저장한다
# (예: "greeting,ordering,payment,farewell", 왼쪽부터 시작).
# ---------------------------------------------------------------------------

def parse_flow_stages(flow: str) -> list[str]:
    '''Dialogue.flow 문자열을 흐름 단계 리스트로 변환한다.'''
    return [stage.strip() for stage in flow.split(",") if stage.strip()]


def get_next_flow_stage(flow: str, current_flow: str) -> str | None:
    '''
    현재 흐름 단계(current_flow) 다음에 올 단계를 반환한다.
    current_flow가 마지막 단계이거나 flow 목록에 없으면 None을 반환한다
    (대화가 끝났다는 의미로 사용, get_more_dialogue 참고).
    '''
    stages = parse_flow_stages(flow)
    try:
        index = stages.index(current_flow)
    except ValueError:
        return None
    if index + 1 < len(stages):
        return stages[index + 1]
    return None


# ---------------------------------------------------------------------------
# 회화(Dialogue) 문장/피드백 생성 — Gemini 연동 (app/api/gemini.py)
#
# 실제 문장 생성/평가는 app/api/gemini.py의 LLM 호출 함수가 담당한다. 다만 flow가 다음
# 단계로 넘어갈지, 대화가 끝났는지(is_end)는 LLM의 advance_flow 판단을 받아 서버가
# Dialogue.flow 목록 위치를 기준으로 구조적으로 계산한다 (LLM이 flow 위치를 직접 세다가
# 착각해 대화가 조기 종료되거나 무한 반복되는 것을 방지하기 위함).
# ---------------------------------------------------------------------------

# 대화에 자연스럽게 녹여낼 추천 단어 개수.
_DIALOGUE_TARGET_WORD_COUNT = 5


def _recommended_words_for_dialogue(db: Session, user_id: str, lang_id: int) -> list[str]:
    '''오늘의 단어 학습 알고리즘(select_vocabulary_for_today)에서 대화에 사용할 추천 단어를 가져온다.'''
    vocabularies = select_vocabulary_for_today(db, user_id, lang_id, limit=_DIALOGUE_TARGET_WORD_COUNT)
    return [vocabulary.word for vocabulary in vocabularies]


def generate_dialogue_opening_line(db: Session, dialogue: Dialogue, language: str, user_id: str) -> str:
    '''대화 주제(subject)와 flow의 첫 단계에 맞는 대화 시작 문장을 LLM으로 생성한다.'''
    flow_stages = parse_flow_stages(dialogue.flow)
    target_words = _recommended_words_for_dialogue(db, user_id, dialogue.lang_id)
    return gemini.generate_dialogue_opening(
        subject=dialogue.subject,
        language=language,
        flow_stages=flow_stages,
        target_words=target_words,
    )


@dataclass
class DialogueStepResult:
    content: str
    feedback: str
    flow: str
    is_end: bool


def generate_dialogue_step(
    db: Session, dialogue: Dialogue, language: str, current_flow: str, user_response: str, user_id: str
) -> DialogueStepResult:
    '''
    사용자의 응답을 LLM으로 평가해 다음 대화 문장(content)과 한국어 피드백(feedback)을 생성하고,
    LLM의 advance_flow 판단(현재 flow 단계를 통과했는지)을 바탕으로 다음 flow 단계와 대화
    종료 여부(is_end)를 서버가 구조적으로 결정한다.

    - advance_flow=True 이고 다음 flow 단계가 있으면: 다음 단계로 진행 (is_end=False)
    - advance_flow=True 이고 다음 flow 단계가 없으면(마지막 단계 통과): 대화 종료 (is_end=True)
    - advance_flow=False 이면: 같은 flow 단계에 머무르며 재시도 (is_end=False)
    '''
    flow_stages = parse_flow_stages(dialogue.flow)
    target_words = _recommended_words_for_dialogue(db, user_id, dialogue.lang_id)

    turn = gemini.generate_dialogue_turn(
        subject=dialogue.subject,
        language=language,
        flow_stages=flow_stages,
        current_flow=current_flow,
        user_response=user_response,
        target_words=target_words,
    )

    next_flow = get_next_flow_stage(dialogue.flow, current_flow) if turn.advance_flow else current_flow
    is_end = turn.advance_flow and next_flow is None

    return DialogueStepResult(
        content=turn.content,
        feedback=turn.feedback,
        flow=next_flow if next_flow is not None else current_flow,
        is_end=is_end,
    )
