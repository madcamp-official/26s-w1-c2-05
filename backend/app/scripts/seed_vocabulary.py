"""CSV(backend/data/vocabulary/seed/*.csv)를 읽어 contents/vocabularies 테이블에 채워 넣는다.

실행 (backend/ 디렉토리에서):
    python -m app.scripts.seed_vocabulary
"""
import csv
from pathlib import Path

from app.database import SessionLocal
from app.models.content import Content
from app.models.vocabulary import Vocabulary
# Content의 relationship()이 문자열로 Grammar/GrammarQuiz/Dialogue를 참조하므로,
# 매퍼 설정 시점에 registry에 등록돼 있도록 함께 import 해야 한다.
from app.models.grammar import Grammar  # noqa: F401
from app.models.grammar_quiz import GrammarQuiz  # noqa: F401
from app.models.dialogue import Dialogue  # noqa: F401

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "vocabulary" / "seed"
VOCAB_CONTENT_TYPE = 1
VALID_LANG_IDS = set(range(1, 9))  # languages 테이블: 1~8 고정
VALID_LEVELS = set(range(1, 7))    # A1~C2 -> 1~6
COMMIT_EVERY = 500


def load_rows(csv_path: Path):
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            yield row


def seed_file(db, csv_path: Path, existing: set[tuple[int, str]]) -> tuple[int, int]:
    inserted = skipped = 0
    for row in load_rows(csv_path):
        lang_id = int(row["lang_id"])
        level = int(row["level"])
        word = row["word"].strip()
        meaning = row["meaning"].strip()
        example = (row.get("example") or "").strip() or None

        if lang_id not in VALID_LANG_IDS or level not in VALID_LEVELS or not word or not meaning:
            print(f"  [skip:invalid] {csv_path.name}: {row}")
            skipped += 1
            continue

        key = (lang_id, word)
        if key in existing:
            skipped += 1
            continue

        content = Content(type=VOCAB_CONTENT_TYPE, lang_id=lang_id)
        db.add(content)
        db.flush()  # content.content_id 발급

        db.add(Vocabulary(
            content_id=content.content_id,
            level=level,
            word=word,
            meaning=meaning,
            example=example,
        ))
        existing.add(key)
        inserted += 1

        if inserted % COMMIT_EVERY == 0:
            db.commit()

    db.commit()
    return inserted, skipped


def main():
    csv_files = sorted(SEED_DIR.glob("*.csv"))
    if not csv_files:
        print(f"시딩할 CSV가 없습니다: {SEED_DIR}")
        return

    db = SessionLocal()
    try:
        existing = {
            (lang_id, word)
            for lang_id, word in db.query(Content.lang_id, Vocabulary.word)
            .join(Vocabulary, Vocabulary.content_id == Content.content_id)
        }
        total_inserted = total_skipped = 0
        for csv_path in csv_files:
            inserted, skipped = seed_file(db, csv_path, existing)
            print(f"{csv_path.name}: {inserted}개 추가, {skipped}개 건너뜀")
            total_inserted += inserted
            total_skipped += skipped
        print(f"완료: 총 {total_inserted}개 추가, {total_skipped}개 건너뜀")
    finally:
        db.close()


if __name__ == "__main__":
    main()
