"""CSV(backend/data/grammar/seed/{lang}.csv, {lang}_quiz.csv)를 읽어
contents/grammars/grammar_quizzes 테이블에 채워 넣는다.

실행 (backend/ 디렉토리에서):
    python -m app.scripts.seed_grammar
"""
import csv
from pathlib import Path

from app.database import SessionLocal
from app.models.content import Content
from app.models.grammar import Grammar
from app.models.grammar_quiz import GrammarQuiz
# Content의 relationship()이 문자열로 Vocabulary/Dialogue를 참조하므로,
# 매퍼 설정 시점에 registry에 등록돼 있도록 함께 import 해야 한다.
from app.models.vocabulary import Vocabulary  # noqa: F401
from app.models.dialogue import Dialogue  # noqa: F401

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "grammar" / "seed"
GRAMMAR_CONTENT_TYPE = 2  # eventlog의 "grammar" 활동과 동일 범주 (app/api/learning.py의 type_converter)
VALID_LANG_IDS = set(range(1, 9))  # languages 테이블: 1~8 고정
VALID_LEVELS = set(range(1, 7))    # A1~C2 -> 1~6
COMMIT_EVERY = 200

LANG_ID = {"en": 1, "ja": 2, "zh": 3, "es": 4, "fr": 5, "de": 6, "it": 7, "vi": 8}


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def seed_grammar_file(
    db, csv_path: Path, grammar_lookup: dict[tuple[int, int, str], int]
) -> tuple[int, int]:
    inserted = skipped = 0
    for row in _read_csv(csv_path):
        lang_id = int(row["lang_id"])
        level = int(row["level"])
        subject = row["subject"].strip()
        grammar_expl = row["grammar_expl"].strip()

        if lang_id not in VALID_LANG_IDS or level not in VALID_LEVELS or not subject or not grammar_expl:
            print(f"  [skip:invalid] {csv_path.name}: {row}")
            skipped += 1
            continue

        key = (lang_id, level, subject)
        if key in grammar_lookup:
            skipped += 1
            continue

        content = Content(type=GRAMMAR_CONTENT_TYPE, lang_id=lang_id)
        db.add(content)
        db.flush()  # content.content_id 발급

        db.add(Grammar(
            content_id=content.content_id,
            lang_id=lang_id,
            level=level,
            subject=subject,
            grammar_expl=grammar_expl,
        ))
        grammar_lookup[key] = content.content_id
        inserted += 1

        if inserted % COMMIT_EVERY == 0:
            db.commit()

    db.commit()
    return inserted, skipped


def seed_quiz_file(
    db,
    csv_path: Path,
    lang_id: int,
    grammar_lookup: dict[tuple[int, int, str], int],
    existing_quizzes: set[tuple[int, str]],
) -> tuple[int, int]:
    inserted = skipped = 0
    for row in _read_csv(csv_path):
        level = int(row["level"])
        subject = row["subject"].strip()
        problem = row["problem"].strip()
        answer = row["answer"].strip()

        grammar_content_id = grammar_lookup.get((lang_id, level, subject))
        if grammar_content_id is None or not problem or not answer:
            print(f"  [skip:invalid] {csv_path.name}: {row}")
            skipped += 1
            continue

        quiz_key = (grammar_content_id, problem)
        if quiz_key in existing_quizzes:
            skipped += 1
            continue

        content = Content(type=GRAMMAR_CONTENT_TYPE, lang_id=lang_id)
        db.add(content)
        db.flush()

        db.add(GrammarQuiz(
            content_id=content.content_id,
            grammar_content_id=grammar_content_id,
            problem=problem,
            answer=answer,
        ))
        existing_quizzes.add(quiz_key)
        inserted += 1

        if inserted % COMMIT_EVERY == 0:
            db.commit()

    db.commit()
    return inserted, skipped


def main():
    grammar_csvs = sorted(p for p in SEED_DIR.glob("*.csv") if not p.name.endswith("_quiz.csv"))
    if not grammar_csvs:
        print(f"시딩할 CSV가 없습니다: {SEED_DIR}")
        return

    db = SessionLocal()
    try:
        grammar_lookup = {
            (lang_id, level, subject): content_id
            for content_id, lang_id, level, subject in db.query(
                Grammar.content_id, Grammar.lang_id, Grammar.level, Grammar.subject
            )
        }
        existing_quizzes = {
            (grammar_content_id, problem)
            for grammar_content_id, problem in db.query(
                GrammarQuiz.grammar_content_id, GrammarQuiz.problem
            )
        }

        total_g_inserted = total_g_skipped = 0
        total_q_inserted = total_q_skipped = 0

        for csv_path in grammar_csvs:
            lang = csv_path.stem
            g_inserted, g_skipped = seed_grammar_file(db, csv_path, grammar_lookup)
            print(f"{csv_path.name}: 문법 {g_inserted}개 추가, {g_skipped}개 건너뜀")
            total_g_inserted += g_inserted
            total_g_skipped += g_skipped

            lang_id = LANG_ID.get(lang)
            quiz_path = SEED_DIR / f"{lang}_quiz.csv"
            if lang_id is None or not quiz_path.exists():
                continue

            q_inserted, q_skipped = seed_quiz_file(db, quiz_path, lang_id, grammar_lookup, existing_quizzes)
            print(f"{quiz_path.name}: 퀴즈 {q_inserted}개 추가, {q_skipped}개 건너뜀")
            total_q_inserted += q_inserted
            total_q_skipped += q_skipped

        print(
            f"완료: 문법 {total_g_inserted}개 추가/{total_g_skipped}개 건너뜀, "
            f"퀴즈 {total_q_inserted}개 추가/{total_q_skipped}개 건너뜀"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
