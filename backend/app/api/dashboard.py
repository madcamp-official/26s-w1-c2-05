from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.eventlog import EventLog
from app.models.grammar import Grammar
from app.models.language import Language
from app.models.learning_progress import LearningProgresses
from app.models.user import User
from app.models.vocabulary import Vocabulary

from app.utils.security import get_current_user

router = APIRouter()

# event_logs.type은 과거 버전에서 "flash"/"grammar"/"speaking" 문자열로 기록되다가
# app/api/learning.py의 type_converter 도입 이후 "1"/"2"/"3" 문자열로 바뀌었다.
# 기존 데이터와의 호환을 위해 두 표기를 모두 인정한다.
_CATEGORY_TYPES = {
    "voca": ("1", "flash"),
    "grammar": ("2", "grammar"),
    "dialogue": ("3", "speaking"),
}
_CATEGORY_LABELS = {"voca": "단어", "grammar": "문법", "dialogue": "회화"}
_TREND_DAYS = 8


def _accuracy(correct: int, total: int) -> float | None:
    return round(100 * correct / total) if total else None


def _bucket_by_day(events: list[EventLog], today: datetime) -> dict[int, list[EventLog]]:
    '''오늘로부터 며칠 전인지(0=오늘)를 key로 event들을 묶는다.'''
    buckets: dict[int, list[EventLog]] = {}
    for event in events:
        days_ago = (today.date() - event.time_studied.date()).days
        buckets.setdefault(days_ago, []).append(event)
    return buckets


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress = (
        db.query(LearningProgresses)
        .filter(LearningProgresses.learning_id == current_user.current_learning_id)
        .first()
    )
    lang_id = progress.lang_id
    language_name = db.query(Language.language).filter(Language.lang_id == lang_id).scalar()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    trend_start = now - timedelta(days=_TREND_DAYS - 1)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    all_events = (
        db.query(EventLog)
        .filter(EventLog.user_id == current_user.user_id, EventLog.lang_id == lang_id)
        .all()
    )
    language_total = len(all_events)

    this_week_events = [e for e in all_events if e.time_studied >= week_ago]
    prev_week_events = [e for e in all_events if two_weeks_ago <= e.time_studied < week_ago]

    week_total = len(this_week_events)
    week_correct = sum(1 for e in this_week_events if e.is_correct)
    accuracy_rate = _accuracy(week_correct, week_total) or 0

    def category_events(events: list[EventLog], key: str) -> list[EventLog]:
        types = _CATEGORY_TYPES[key]
        return [e for e in events if e.type in types]

    category_week_accuracy = {}
    category_prev_accuracy = {}
    for key in _CATEGORY_TYPES:
        cat_this_week = category_events(this_week_events, key)
        category_week_accuracy[key] = _accuracy(
            sum(1 for e in cat_this_week if e.is_correct), len(cat_this_week)
        )
        cat_prev_week = category_events(prev_week_events, key)
        category_prev_accuracy[key] = _accuracy(
            sum(1 for e in cat_prev_week if e.is_correct), len(cat_prev_week)
        )

    scored = {k: v for k, v in category_week_accuracy.items() if v is not None}
    most_weak_key = min(scored, key=scored.get) if scored else "dialogue"

    improved = {
        key: category_week_accuracy[key] - category_prev_accuracy[key]
        for key in _CATEGORY_TYPES
        if category_week_accuracy[key] is not None and category_prev_accuracy[key] is not None
    }
    most_improved_key = max(improved, key=improved.get) if improved else "voca"

    # 단어/문법은 이번 주 오답이 가장 많았던 콘텐츠를 짚어 피드백 문장을 만들고,
    # 회화는 문항 단위 채점이 없어 학습량 자체를 기준으로 안내한다.
    def worst_content_feedback(key: str) -> str | None:
        cat_events = category_events(this_week_events, key)
        wrong = [e for e in cat_events if not e.is_correct]
        if not cat_events:
            return f"이번 주 {_CATEGORY_LABELS[key]} 학습 기록이 없어요. 학습을 시작해보세요!"
        if not wrong:
            return f"이번 주 {_CATEGORY_LABELS[key]}에서 틀린 문제가 없었어요. 완벽해요!"

        content_id = max({e.content_id for e in wrong}, key=lambda cid: sum(1 for e in wrong if e.content_id == cid))
        if key == "voca":
            word = db.query(Vocabulary.word).filter(Vocabulary.content_id == content_id).scalar()
            return f"이번 주 가장 헷갈려 한 단어는 {word}예요." if word else None
        if key == "grammar":
            subject = db.query(Grammar.subject).filter(Grammar.content_id == content_id).scalar()
            return f"가장 많이 헷갈려하는 부분은 {subject}예요." if subject else None
        return f"회화 세션에서 오답이 {len(wrong)}건 있었어요. 복습을 추천해요."

    feedback_voca = worst_content_feedback("voca")
    feedback_grammar = worst_content_feedback("grammar")
    feedback_dialogue = worst_content_feedback("dialogue")

    trend_events = [e for e in all_events if e.time_studied >= trend_start]
    buckets = _bucket_by_day(trend_events, now)

    error_trend: dict[str, list[int]] = {key: [] for key in _CATEGORY_TYPES}
    last_known = {key: 0 for key in _CATEGORY_TYPES}
    for days_ago in range(_TREND_DAYS - 1, -1, -1):
        day_events = buckets.get(days_ago, [])
        for key in _CATEGORY_TYPES:
            cat_day_events = category_events(day_events, key)
            accuracy = _accuracy(sum(1 for e in cat_day_events if e.is_correct), len(cat_day_events))
            error_rate = last_known[key] if accuracy is None else 100 - accuracy
            last_known[key] = error_rate
            error_trend[key].append(error_rate)

    return {
        "language": language_name,
        "daily_streak": progress.daily_streak,
        "language_total": language_total,
        "accuracy_rate": accuracy_rate,
        "most_weak": _CATEGORY_LABELS[most_weak_key],
        "most_improved": _CATEGORY_LABELS[most_improved_key],
        "feedback_voca": feedback_voca,
        "feedback_grammar": feedback_grammar,
        "feedback_dialogue": feedback_dialogue,
        "error_trend": error_trend,
    }
