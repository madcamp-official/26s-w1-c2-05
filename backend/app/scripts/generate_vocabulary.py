"""LLM(Gemini)으로 레벨별 어휘 목록(단어 + 한국어 뜻 + 예문)을 생성해 CSV로 저장하는
1회성 배치 스크립트. 앱 런타임에는 관여하지 않으며, 여기서 만든 CSV를 이후 seed_vocabulary.py가
DB에 채워 넣는다 (generate_grammar.py와 동일한 흐름).

출력: backend/data/vocabulary/seed/{lang}.csv (columns: lang_id, level, word, meaning, example)

실행 (backend/ 디렉토리에서):
    python -m app.scripts.generate_vocabulary --lang vi

레벨 단위로 생성 즉시 CSV에 반영하므로, 중간에 실패해도 같은 명령을 다시 실행하면
이미 목표 개수를 채운 레벨은 건너뛰고 나머지만 이어서 생성한다.
"""
import argparse
import csv
from pathlib import Path

from google.genai import types
from pydantic import BaseModel, Field

from app.api.gemini import client, GEMINI_MODEL

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "vocabulary" / "seed"

LANG_ID = {"en": 1, "ja": 2, "zh": 3, "es": 4, "fr": 5, "de": 6, "it": 7, "vi": 8}
LANG_NAME = {
    "en": "영어", "ja": "일본어", "zh": "중국어", "es": "스페인어",
    "fr": "프랑스어", "de": "독일어", "it": "이탈리아어", "vi": "베트남어",
}
CEFR_BY_LEVEL = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
WORDS_PER_LEVEL = 50
MAX_ATTEMPTS_PER_LEVEL = 6


class VocabItem(BaseModel):
    word: str = Field(description="학습 언어 단어 (원어 표기 그대로).")
    meaning: str = Field(description="한국어 뜻. 뜻이 여러 개면 쉼표로 구분.")
    example: str = Field(description="이 단어를 사용한 학습 언어 예문 한 문장.")


class VocabBatchResult(BaseModel):
    items: list[VocabItem] = Field(description="생성된 단어 목록.")


def _build_prompt(language: str, cefr: str, count: int, existing_words: list[str]) -> str:
    lines = [
        f"{language} 학습자를 위한 어휘 학습 콘텐츠를 만든다.",
        f"레벨: CEFR {cefr}",
        f"이 레벨의 학습자에게 적합하고 실생활에서 자주 쓰이는 {language} 단어 {count}개를 선정해서, "
        "각 단어의 한국어 뜻(meaning)과 그 단어를 사용한 예문(example, 반드시 학습 언어 문장)을 함께 생성해라.",
        "단어는 서로 중복되지 않아야 한다.",
    ]
    if existing_words:
        lines.append(
            "다음 단어들은 이미 선정되었으니 절대 다시 포함하지 마라: " + ", ".join(existing_words)
        )
    return "\n".join(lines)


def generate_batch(language: str, cefr: str, count: int, existing_words: list[str]) -> list[VocabItem]:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=_build_prompt(language, cefr, count, existing_words),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VocabBatchResult,
        ),
    )
    return response.parsed.items


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["lang_id", "level", "word", "meaning", "example"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True, choices=sorted(LANG_ID.keys()))
    parser.add_argument("--count", type=int, default=WORDS_PER_LEVEL, help="레벨당 목표 단어 수")
    args = parser.parse_args()

    lang = args.lang
    lang_id = LANG_ID[lang]
    language = LANG_NAME[lang]
    target = args.count

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = SEED_DIR / f"{lang}.csv"
    rows = _read_csv(csv_path)

    # 단어는 레벨을 넘나들며 전역으로 유일해야 한다 — seed_vocabulary.py가 (lang_id, word)
    # 기준으로 중복을 걸러내므로, 레벨별로만 중복을 막으면 다른 레벨에 이미 나온 단어가 그
    # 레벨의 자리를 채우지 못하고 스킵되어 해당 레벨이 목표 개수보다 적게 채워진다.
    existing_words = {r["word"] for r in rows}

    for level in range(1, 7):
        level_str = str(level)
        cefr = CEFR_BY_LEVEL[level]
        level_rows = [r for r in rows if r["level"] == level_str]

        if len(level_rows) >= target:
            print(f"level={level}({cefr}) 이미 {len(level_rows)}개 있음, 건너뜀")
            continue

        print(f"생성 중: level={level}({cefr}), 현재 {len(level_rows)}/{target}")
        attempts = 0
        while len(level_rows) < target and attempts < MAX_ATTEMPTS_PER_LEVEL:
            attempts += 1
            need = target - len(level_rows)
            try:
                items = generate_batch(language, cefr, need, sorted(existing_words))
            except Exception as e:
                print(f"  [실패] attempt {attempts}: {e}")
                continue

            for item in items:
                word = item.word.strip()
                if not word or word in existing_words:
                    continue
                existing_words.add(word)
                row = {
                    "lang_id": lang_id,
                    "level": level_str,
                    "word": word,
                    "meaning": item.meaning.strip(),
                    "example": item.example.strip(),
                }
                level_rows.append(row)
                rows.append(row)
                if len(level_rows) >= target:
                    break

            # 레벨 하나가 끝날 때마다 즉시 저장 -> 중간에 실패해도 재실행 시 이어서 생성 가능
            _write_csv(csv_path, rows)

        print(f"  완료: level={level} {len(level_rows)}/{target}개")

    print(f"완료: {csv_path} (총 {len(rows)}개)")


if __name__ == "__main__":
    main()
