"""CSV(backend/data/dialogue/seed/{lang}.csv)를 읽어 contents/dialogues 테이블에
채워 넣는다 (seed_grammar.py와 동일한 흐름).

실행 (backend/ 디렉토리에서):
    python -m app.scripts.seed_dialogue
"""
import csv
from pathlib import Path

from app.database import SessionLocal
from app.models.content import Content
from app.models.dialogue import Dialogue
# Content의 relationship()이 문자열로 Vocabulary/Grammar/GrammarQuiz를 참조하므로,
# 매퍼 설정 시점에 registry에 등록돼 있도록 함께 import 해야 한다.
from app.models.vocabulary import Vocabulary  # noqa: F401
from app.models.grammar import Grammar  # noqa: F401
from app.models.grammar_quiz import GrammarQuiz  # noqa: F401

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "dialogue" / "seed"
DIALOGUE_CONTENT_TYPE = 3  # eventlog의 "dialogue" 활동과 동일 범주 (app/api/learning.py의 type_converter)
VALID_LANG_IDS = set(range(1, 9))  # languages 테이블: 1~8 고정
COMMIT_EVERY = 200


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def seed_dialogue_file(
    db, csv_path: Path, existing: set[tuple[int, str]]
) -> tuple[int, int]:
    inserted = skipped = 0
    for row in _read_csv(csv_path):
        lang_id = int(row["lang_id"])
        subject = row["subject"].strip()
        flow = row["flow"].strip()

        if lang_id not in VALID_LANG_IDS or not subject or not flow:
            print(f"  [skip:invalid] {csv_path.name}: {row}")
            skipped += 1
            continue

        key = (lang_id, subject)
        if key in existing:
            skipped += 1
            continue

        content = Content(type=DIALOGUE_CONTENT_TYPE, lang_id=lang_id)
        db.add(content)
        db.flush()  # content.content_id 발급

        db.add(Dialogue(
            content_id=content.content_id,
            subject=subject,
            flow=flow,
            lang_id=lang_id,
        ))
        existing.add(key)
        inserted += 1

        if inserted % COMMIT_EVERY == 0:
            db.commit()

    db.commit()
    return inserted, skipped


def main():
    dialogue_csvs = sorted(SEED_DIR.glob("*.csv"))
    if not dialogue_csvs:
        print(f"시딩할 CSV가 없습니다: {SEED_DIR}")
        return

    db = SessionLocal()
    try:
        existing = {
            (lang_id, subject)
            for lang_id, subject in db.query(Dialogue.lang_id, Dialogue.subject)
        }

        total_inserted = total_skipped = 0
        for csv_path in dialogue_csvs:
            inserted, skipped = seed_dialogue_file(db, csv_path, existing)
            print(f"{csv_path.name}: 회화 {inserted}개 추가, {skipped}개 건너뜀")
            total_inserted += inserted
            total_skipped += skipped

        print(f"완료: 회화 {total_inserted}개 추가, {total_skipped}개 건너뜀")
    finally:
        db.close()


if __name__ == "__main__":
    main()
