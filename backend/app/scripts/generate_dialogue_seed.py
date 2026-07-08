"""회화(Dialogue) 주제 마스터 목록을 8개 언어 seed CSV로 복제하는 1회성 스크립트.

grammar와 달리 회화는 실제 문장(content)을 LLM으로 미리 생성해두지 않는다 — 문장은
/dialogue, /dialoguelog 요청 시점에 app/utils/learning.py가 실시간으로 생성한다
(app/api/gemini.py). 이 스크립트가 다루는 subject/flow는 "설계도"일 뿐이고 언어와
무관하므로, 마스터 목록 하나를 언어별 lang_id만 바꿔 그대로 복제한다.

입력: backend/data/dialogue/subjects.csv (columns: tier, subject, flow)
출력: backend/data/dialogue/seed/{lang}.csv (columns: lang_id, subject, flow)

실행 (backend/ 디렉토리에서):
    python -m app.scripts.generate_dialogue_seed
"""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "dialogue"
SEED_DIR = DATA_DIR / "seed"

LANG_ID = {"en": 1, "ja": 2, "zh": 3, "es": 4, "fr": 5, "de": 6, "it": 7, "vi": 8}


def main():
    master_path = DATA_DIR / "subjects.csv"
    with master_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(f"마스터 목록이 비어 있습니다: {master_path}")
        return

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    for lang, lang_id in LANG_ID.items():
        seed_path = SEED_DIR / f"{lang}.csv"
        with seed_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["lang_id", "subject", "flow"])
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    "lang_id": lang_id,
                    "subject": row["subject"].strip(),
                    "flow": row["flow"].strip(),
                })
        print(f"작성 완료: {seed_path} ({len(rows)}개)")


if __name__ == "__main__":
    main()
