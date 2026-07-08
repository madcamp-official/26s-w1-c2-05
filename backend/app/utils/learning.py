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
- Canale, M., & Swain, M. (1980). "Theoretical Bases of Communicative Approaches to
  Second Language Teaching and Testing." 언어 능력을 어휘(단어)/문법/의사소통(회화) 등으로
  구분하는 근거 — 취약점/개선점 분석을 "단어·문법·회화" 세 범주로 나누는 데 사용.
- Bloom, B. S. (1984). "The 2 Sigma Problem." Mastery learning — 목표 숙달 수준에 가장
  못 미치는 범주를 취약점으로 우선 노출해야 한다는 근거.
- Newell, A., & Rosenbloom, P. S. (1981). "Mechanisms of Skill Acquisition and the Law
  of Practice." 연습에 따라 오류율이 감소하는 학습 곡선 — 이력을 전반부/후반부로 나누어
  비교함으로써 "가장 개선된 범주"를 근사적으로 측정하는 데 사용.
'''

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api import gemini
from app.models.content import Content
from app.models.dialogue import Dialogue
from app.models.eventlog import EventLog
from app.models.grammar import Grammar
from app.models.grammar_quiz import GrammarQuiz
from app.models.learning_progress import LearningProgresses
from app.models.vocabulary import Vocabulary


import random


# ---------------------------------------------------------------------------
# 학습일수(study_days)/연속 학습일(daily_streak) 갱신
# ---------------------------------------------------------------------------

def record_daily_activity(db: Session, progress: LearningProgresses) -> None:
    '''
    오늘 처음으로 학습 활동(답변 제출/회화 turn)이 발생했을 때만 study_days와
    daily_streak을 갱신한다. last_studied의 날짜를 기준으로 판단하므로, 같은 날
    여러 번 답을 제출해도(플래시카드 20문제 등) 하루에 한 번만 반영된다.

    - 어제 학습했다면 streak을 이어서 +1.
    - 어제가 아니라면(하루 이상 건너뛰었거나 첫 학습이라면) streak을 1로 리셋.
    '''
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today = now.date()
    last_date = progress.last_studied.date() if progress.last_studied else None

    if last_date == today:
        return

    progress.daily_streak = progress.daily_streak + 1 if last_date == today - timedelta(days=1) else 1
    progress.study_days += 1
    progress.last_studied = now
    db.add(progress)
    db.commit()


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

def _daily_tiebreaker(user_id: str, lang_id: int, content_id: int) -> float:
    '''
    user_id/lang_id/content_id/오늘 날짜(UTC)로 시드를 고정한 난수를 반환한다.

    select_dialogue_for_today는 아직 시도하지 않은 주제가 여러 개면 무작위로 순서를 정하는데,
    매 요청마다 전역 random을 쓰면 진행 중인 학습 이력(EventLog) 변화가 전혀 없어도 화면에
    들어갈 때마다 다른 주제가 뽑힌다. content_id별로 오늘 하루는 항상 같은 값이 나오도록 고정하되,
    날짜가 바뀌면 자연스럽게 다른 조합이 나오도록 시드에 날짜를 포함한다.
    '''
    today = datetime.now(timezone.utc).date().isoformat()
    seed = f"{user_id}:{lang_id}:{today}:{content_id}"
    return random.Random(seed).random()


def select_dialogue_for_today(db: Session, user_id: str, lang_id: int, limit: int = 1) -> list[Dialogue]:
    '''
    오늘 학습할 회화(Dialogue) 주제를 선정한다. Vocabulary/Grammar와 달리 CEFR 레벨 컬럼이
    없으므로 레벨 적응(i+1) 로직은 적용하지 않는다. 대신,
      1) 아직 한 번도 시도하지 않은 주제를 최우선으로 하고(testing effect, Roediger & Karpicke, 2006),
      2) 이미 시도한 주제 중에서는 예측 회상 확률(half-life regression)이 낮은,
         즉 망각 위험이 큰 주제를 우선 복습으로 배정한다.

    동률(예: 미시도 주제끼리)일 때의 순서는 _daily_tiebreaker로 고정해, 같은 날 안에는 페이지에
    다시 들어가도 같은 주제가 나오도록 한다.
    '''
    dialogues = db.query(Dialogue).filter(Dialogue.lang_id == lang_id).all()
    if not dialogues:
        return []

    content_ids = [dialogue.content_id for dialogue in dialogues]
    stats_map = _aggregate_event_stats(db, user_id, lang_id, content_ids)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    def priority(dialogue: Dialogue) -> tuple[int, float, float]:
        tiebreaker = _daily_tiebreaker(user_id, lang_id, dialogue.content_id)
        stats = stats_map.get(dialogue.content_id)
        if stats is None or stats.is_new:
            return (0, 0.0, tiebreaker)  # 미시도 주제 최우선

        last_studied = stats.last_studied
        if last_studied is not None and last_studied.tzinfo is not None:
            last_studied = last_studied.replace(tzinfo=None)
        days_since = max((now - last_studied).total_seconds() / 86400.0, 0.0) if last_studied else 0.0
        p_recall = estimate_recall_probability(stats.n_correct, stats.n_incorrect, days_since)
        return (1, p_recall, tiebreaker)  # 회상 확률이 낮을수록(망각 위험이 클수록) 먼저

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


@dataclass
class DialogueOpeningLineResult:
    content: str
    translation: str


def generate_dialogue_opening_line(
    db: Session, dialogue: Dialogue, language: str, user_id: str
) -> DialogueOpeningLineResult:
    '''대화 주제(subject)와 flow의 첫 단계에 맞는 대화 시작 문장(및 한국어 번역)을 LLM으로 생성한다.'''
    flow_stages = parse_flow_stages(dialogue.flow)
    target_words = _recommended_words_for_dialogue(db, user_id, dialogue.lang_id)
    result = gemini.generate_dialogue_opening(
        subject=dialogue.subject,
        language=language,
        flow_stages=flow_stages,
        target_words=target_words,
    )
    return DialogueOpeningLineResult(content=result.content, translation=result.translation)


@dataclass
class DialogueStepResult:
    content: str
    translation: str
    feedback: str
    flow: str
    is_end: bool


def generate_dialogue_step(
    db: Session, dialogue: Dialogue, language: str, current_flow: str, user_response: str, user_id: str,
    history: list | None = None,
) -> DialogueStepResult:
    '''
    사용자의 응답을 LLM으로 평가해 다음 대화 문장(content)과 한국어 피드백(feedback)을 생성하고,
    LLM의 advance_flow 판단(현재 flow 단계를 통과했는지)을 바탕으로 다음 flow 단계와 대화
    종료 여부(is_end)를 서버가 구조적으로 결정한다.

    - advance_flow=True 이고 다음 flow 단계가 있으면: 다음 단계로 진행 (is_end=False)
    - advance_flow=True 이고 다음 flow 단계가 없으면(마지막 단계 통과): 대화 종료 (is_end=True)
    - advance_flow=False 이면: 같은 flow 단계에 머무르며 재시도 (is_end=False)

    history는 이번 응답 이전까지의 대화 turn 목록(요청 스키마의 DialogueTurn)이다. 백엔드가
    turn 단위 대화를 저장하지 않으므로, LLM이 이미 오간 내용을 기억한 채 판단하도록 매 요청마다
    프론트가 함께 보낸 값을 그대로 gemini 호출에 전달한다.
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
        history=history,
    )

    next_flow = get_next_flow_stage(dialogue.flow, current_flow) if turn.advance_flow else current_flow
    is_end = turn.advance_flow and next_flow is None

    return DialogueStepResult(
        content=turn.content,
        translation=turn.translation,
        feedback=turn.feedback,
        flow=next_flow if next_flow is not None else current_flow,
        is_end=is_end,
    )


# ---------------------------------------------------------------------------
# 카테고리별(단어/문법/회화) 취약점 및 개선점 분석
#
# EventLog.type은 app/api/learning.py의 type_converter와 동일한 값을 쓴다:
#   1 = 단어(flash), 2 = 문법(grammar_quiz), 3 = 회화(dialogue)
# (Canale & Swain, 1980의 어휘/문법/의사소통 능력 구분에 대응)
# ---------------------------------------------------------------------------

_CATEGORY_BY_TYPE = {1: "단어", 2: "문법", 3: "회화"}

# 이력을 전반부/후반부로 나눠 "개선도"를 근사하기 위한 분할 비율
# (Newell & Rosenbloom, 1981의 연습 학습곡선을 단순화한 근사).
_TREND_SPLIT_RATIO = 0.5
# 개선도 비교에 필요한 카테고리별 최소 누적 시도 수.
_MIN_ATTEMPTS_FOR_TREND = 2

# event_log가 전혀 없는 신규 사용자에게 반환할 기본값.
# (언어 학습은 통상 단어 학습에서 시작하므로 "단어"를 기본 취약점/개선점으로 둔다.)
_DEFAULT_CATEGORY = "단어"


@dataclass
class CategoryTrend:
    category: str
    n_total: int
    accuracy: float
    early_accuracy: float
    recent_accuracy: float

    @property
    def improvement(self) -> float:
        return self.recent_accuracy - self.early_accuracy


def _category_event_history(db: Session, user_id: str, lang_id: int) -> dict[str, list[bool]]:
    '''사용자의 event_logs를 시간순으로 정렬해 카테고리(단어/문법/회화)별 정오답 리스트로 묶는다.'''
    rows = (
        db.query(EventLog.type, EventLog.is_correct)
        .filter(EventLog.user_id == user_id, EventLog.lang_id == lang_id)
        .order_by(EventLog.time_studied.asc())
        .all()
    )

    history: dict[str, list[bool]] = {label: [] for label in _CATEGORY_BY_TYPE.values()}
    for event_type, is_correct in rows:
        try:
            category = _CATEGORY_BY_TYPE.get(int(event_type))
        except (TypeError, ValueError):
            category = None
        if category is not None:
            history[category].append(bool(is_correct))
    return history


def _build_category_trends(history: dict[str, list[bool]]) -> list[CategoryTrend]:
    '''각 카테고리 이력을 전반부/후반부로 나누어 정답률과 개선도(improvement)를 계산한다.'''
    trends = []
    for category, results in history.items():
        n_total = len(results)
        if n_total == 0:
            continue
        split = max(1, round(n_total * _TREND_SPLIT_RATIO))
        early = results[:split]
        recent = results[split:] or early  # 데이터가 적어 후반부가 비면 초반부로 대체(개선도 0)
        trends.append(
            CategoryTrend(
                category=category,
                n_total=n_total,
                accuracy=sum(results) / n_total,
                early_accuracy=sum(early) / len(early),
                recent_accuracy=sum(recent) / len(recent),
            )
        )
    return trends


def find_weakest_category(db: Session, user_id: str, lang_id: int) -> str:
    '''
    "단어", "문법", "회화" 중 사용자가 가장 취약한 범주를 하나 반환한다.

    - 한 번도 시도하지 않은 범주가 있으면(단, 셋 다 미시도는 제외) 가장 우선적으로 취약점으로
      간주한다 — 전혀 연습하지 않은 영역이 가장 뒤처져 있다고 보는 것이 합리적이다.
    - 그렇지 않으면 최근 정답률(recent_accuracy)이 가장 낮은 범주를 반환한다
      (Bloom, 1984의 mastery learning — 목표 숙달에 못 미치는 영역을 우선 노출).
    - event_log가 전혀 없으면 기본값(_DEFAULT_CATEGORY)을 반환한다.
    '''
    history = _category_event_history(db, user_id, lang_id)

    untried = [category for category, results in history.items() if not results]
    if untried and len(untried) < len(history):
        return untried[0]

    trends = _build_category_trends(history)
    if not trends:
        return _DEFAULT_CATEGORY

    return min(trends, key=lambda t: t.recent_accuracy).category


def find_most_improved_category(db: Session, user_id: str, lang_id: int) -> str:
    '''
    "단어", "문법", "회화" 중 학습 초반 대비 최근 정답률이 가장 크게 오른 범주를 반환한다
    (Newell & Rosenbloom, 1981의 연습 학습곡선을 전반부/후반부 비교로 근사).

    - 추세 비교에 필요한 최소 시도 수(_MIN_ATTEMPTS_FOR_TREND)를 채운 범주 중에서 고른다.
    - 그런 범주가 없으면(데이터가 너무 적으면) 정답률이 가장 높은 범주로 대체한다.
    - event_log가 전혀 없으면 기본값(_DEFAULT_CATEGORY)을 반환한다.
    '''
    history = _category_event_history(db, user_id, lang_id)
    all_trends = _build_category_trends(history)

    eligible = [t for t in all_trends if t.n_total >= _MIN_ATTEMPTS_FOR_TREND]
    if eligible:
        return max(eligible, key=lambda t: t.improvement).category

    if all_trends:
        return max(all_trends, key=lambda t: t.accuracy).category

    return _DEFAULT_CATEGORY


def analyze_category_performance(db: Session, user_id: str, lang_id: int) -> dict[str, str]:
    '''대시보드에 노출할 취약점(weakness)과 가장 개선된 범주(most_improved)를 함께 반환한다.'''
    return {
        "weakness": find_weakest_category(db, user_id, lang_id),
        "most_improved": find_most_improved_category(db, user_id, lang_id),
    }


# ---------------------------------------------------------------------------
# 오답률 추이(error trend) — 대시보드의 "voca"/"grammar"/"dialogue" 배열 필드
#
# _CATEGORY_BY_TYPE의 한국어 라벨과 달리, UserDashboardResponse.error_trend는 기존
# 스키마가 이미 "voca"/"grammar"/"dialogue"라는 영문 key를 쓰고 있으므로 이를 그대로 따른다.
# ---------------------------------------------------------------------------

_CATEGORY_KEY_BY_TYPE = {1: "voca", 2: "grammar", 3: "dialogue"}

# 최근 28일을 4일 단위 7구간으로 나누어 오답률 추이를 계산한다.
_ERROR_TREND_BUCKET_DAYS = 4
_ERROR_TREND_BUCKET_COUNT = 7


def get_error_trend(db: Session, user_id: str, lang_id: int) -> dict[str, list[float | None]]:
    '''
    최근 28일간의 오답률 추이를 "voca"/"grammar"/"dialogue" 각각 길이 7의 배열로 반환한다
    (4일 단위 7구간, 배열의 앞쪽이 과거·뒤쪽이 최근). 특정 구간에 학습 기록이 전혀 없으면
    "학습 안 함"과 "전부 정답(오답률 0)"을 구분하기 위해 해당 값을 None(=null)으로 둔다.
    '''
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_start = now - timedelta(days=_ERROR_TREND_BUCKET_DAYS * _ERROR_TREND_BUCKET_COUNT)

    rows = (
        db.query(EventLog.type, EventLog.is_correct, EventLog.time_studied)
        .filter(
            EventLog.user_id == user_id,
            EventLog.lang_id == lang_id,
            EventLog.time_studied >= window_start,
        )
        .all()
    )

    # bucket_stats[category][bucket_index] = [n_total, n_incorrect]
    bucket_stats: dict[str, list[list[int]]] = {
        key: [[0, 0] for _ in range(_ERROR_TREND_BUCKET_COUNT)] for key in _CATEGORY_KEY_BY_TYPE.values()
    }

    for event_type, is_correct, time_studied in rows:
        try:
            category = _CATEGORY_KEY_BY_TYPE.get(int(event_type))
        except (TypeError, ValueError):
            category = None
        if category is None or time_studied is None:
            continue

        elapsed_days = (now - time_studied).total_seconds() / 86400.0
        offset_from_recent = int(elapsed_days // _ERROR_TREND_BUCKET_DAYS)
        bucket_index = _ERROR_TREND_BUCKET_COUNT - 1 - offset_from_recent
        if not (0 <= bucket_index < _ERROR_TREND_BUCKET_COUNT):
            continue  # 창(window) 경계를 벗어난 이벤트(시계 오차 등)는 무시

        totals = bucket_stats[category][bucket_index]
        totals[0] += 1
        if not is_correct:
            totals[1] += 1

    return {
        category: [(n_incorrect / n_total) if n_total > 0 else None for n_total, n_incorrect in buckets]
        for category, buckets in bucket_stats.items()
    }


# ---------------------------------------------------------------------------
# 주간 학습 피드백 — Gemini 연동 (app/api/gemini.py의 generate_feedback)
#
# DB 조회(event_logs/vocabularies/grammars/grammar_quizzes)는 이 모듈이 맡고, 그 결과를
# 순수 데이터로 gemini.py에 넘겨 LLM 호출만 위임한다 (회화 문장 생성과 동일한 역할 분담).
# ---------------------------------------------------------------------------

_FEEDBACK_WINDOW_DAYS = 7


def _gather_recent_feedback_data(
    db: Session, user_id: str, lang_id: int
) -> tuple[list[tuple[str, bool]], list[tuple[str, str, bool]], list[bool]]:
    '''
    최근 1주일(_FEEDBACK_WINDOW_DAYS)간의 event_logs를 단어/문법/회화 세 분야의 LLM 피드백
    입력 형식으로 가공한다.
      - 단어: (단어, 정답 여부) 목록
      - 문법: (퀴즈 문제, 문법 개념(subject), 정답 여부) 목록
      - 회화: 정답 여부 목록
    '''
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=_FEEDBACK_WINDOW_DAYS)

    rows = (
        db.query(EventLog.content_id, EventLog.type, EventLog.is_correct)
        .filter(
            EventLog.user_id == user_id,
            EventLog.lang_id == lang_id,
            EventLog.time_studied >= since,
        )
        .all()
    )

    def _category(event_type) -> str | None:
        try:
            return _CATEGORY_BY_TYPE.get(int(event_type))
        except (TypeError, ValueError):
            return None

    vocab_ids = {content_id for content_id, event_type, _ in rows if _category(event_type) == "단어"}
    quiz_ids = {content_id for content_id, event_type, _ in rows if _category(event_type) == "문법"}

    word_by_id: dict[int, str] = dict(
        db.query(Vocabulary.content_id, Vocabulary.word).filter(Vocabulary.content_id.in_(vocab_ids)).all()
    ) if vocab_ids else {}

    quiz_info_by_id: dict[int, tuple[str, str]] = {
        content_id: (problem, subject)
        for content_id, problem, subject in (
            db.query(GrammarQuiz.content_id, GrammarQuiz.problem, Grammar.subject)
            .join(Grammar, Grammar.content_id == GrammarQuiz.grammar_content_id)
            .filter(GrammarQuiz.content_id.in_(quiz_ids))
            .all()
        )
    } if quiz_ids else {}

    voca_results: list[tuple[str, bool]] = []
    grammar_results: list[tuple[str, str, bool]] = []
    dialogue_results: list[bool] = []

    for content_id, event_type, is_correct in rows:
        category = _category(event_type)
        if category == "단어":
            word = word_by_id.get(content_id)
            if word is not None:
                voca_results.append((word, bool(is_correct)))
        elif category == "문법":
            info = quiz_info_by_id.get(content_id)
            if info is not None:
                problem, subject = info
                grammar_results.append((problem, subject, bool(is_correct)))
        elif category == "회화":
            dialogue_results.append(bool(is_correct))

    return voca_results, grammar_results, dialogue_results


def generate_weekly_feedback(db: Session, user_id: str, lang_id: int) -> dict[str, str]:
    '''
    최근 1주일간의 단어/문법/회화 학습 기록을 모아 LLM(app/api/gemini.py의 generate_feedback)에
    한 번에 넘기고, {"voca": ..., "grammar": ..., "dialogue": ...} 형태의 피드백 텍스트를 반환한다.
    '''
    voca_results, grammar_results, dialogue_results = _gather_recent_feedback_data(db, user_id, lang_id)
    result = gemini.generate_feedback(voca_results, grammar_results, dialogue_results)
    return {
        "voca": result.feedback_voca,
        "grammar": result.feedback_grammar,
        "dialogue": result.feedback_dialogue,
    }
