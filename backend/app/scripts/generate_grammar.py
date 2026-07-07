"""LLM(Gemini)으로 문법 subject grid를 기반으로 문법 설명 + 퀴즈를 생성해 CSV로 저장하는
1회성 배치 스크립트. 앱 런타임에는 관여하지 않으며, 여기서 만든 CSV를 이후 seed 스크립트가
DB에 채워 넣는다 (seed_vocabulary.py와 동일한 흐름).

입력: backend/data/grammar/subjects/{lang}.csv (columns: level, subject)
출력:
    backend/data/grammar/seed/{lang}.csv       (columns: lang_id, level, subject, grammar_expl)
    backend/data/grammar/seed/{lang}_quiz.csv  (columns: level, subject, problem, answer)

실행 (backend/ 디렉토리에서):
    python -m app.scripts.generate_grammar --lang en

subject 단위로 생성 즉시 CSV에 반영하므로, 중간에 실패해도 같은 명령을 다시 실행하면
이미 생성된 subject는 건너뛰고 나머지만 이어서 생성한다.
"""
import argparse
import csv
from pathlib import Path

from google.genai import types
from pydantic import BaseModel, Field

from app.api.gemini import client, GEMINI_MODEL

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "grammar"
SUBJECTS_DIR = DATA_DIR / "subjects"
SEED_DIR = DATA_DIR / "seed"

LANG_ID = {"en": 1, "ja": 2, "zh": 3, "es": 4, "fr": 5, "de": 6, "it": 7, "vi": 8}
LANG_NAME = {
    "en": "영어", "ja": "일본어", "zh": "중국어", "es": "스페인어",
    "fr": "프랑스어", "de": "독일어", "it": "이탈리아어", "vi": "베트남어",
}
CEFR_BY_LEVEL = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
QUIZ_PER_SUBJECT = 3


class QuizItem(BaseModel):
    problem: str = Field(description="빈칸 채우기 형식의 퀴즈 문제. 학습 언어 문장 안에 빈칸(___)을 정확히 하나 포함한다.")
    answer: str = Field(description="빈칸에 들어갈 정답. 학습 언어로 작성한다.")


class GrammarContentResult(BaseModel):
    grammar_expl: str = Field(
        description="이 문법 포인트에 대한 한국어 설명. 개념, 형태(구조), 예문을 포함해 200~400자 내외로 작성한다."
    )
    quizzes: list[QuizItem] = Field(description=f"이 문법 포인트를 연습하는 빈칸 채우기 퀴즈 {QUIZ_PER_SUBJECT}개.")


def _build_prompt(language: str, cefr: str, subject: str) -> str:
    return (
        f"{language} 학습자를 위한 문법 학습 콘텐츠를 만든다.\n"
        f"레벨: CEFR {cefr}\n"
        f"문법 주제: \"{subject}\"\n"
        "이 레벨의 학습자가 이해할 수 있는 난이도로, 한국어 설명(grammar_expl)과 "
        f"{QUIZ_PER_SUBJECT}개의 빈칸 채우기 퀴즈(quizzes)를 생성해라.\n"
        f"퀴즈의 problem은 반드시 {language} 문장이어야 하며, 이 문법 포인트를 연습하는 빈칸(___)을 "
        "정확히 하나 포함해야 한다. answer는 그 빈칸에 들어갈 정답이다."
    )


def generate_one(language: str, cefr: str, subject: str) -> GrammarContentResult:
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=_build_prompt(language, cefr, subject),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GrammarContentResult,
        ),
    )
    return response.parsed


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True, choices=sorted(LANG_ID.keys()))
    args = parser.parse_args()

    lang = args.lang
    lang_id = LANG_ID[lang]
    language = LANG_NAME[lang]

    grid = _read_csv(SUBJECTS_DIR / f"{lang}.csv")
    if not grid:
        print(f"grid가 없습니다: {SUBJECTS_DIR / f'{lang}.csv'}")
        return

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    grammar_csv = SEED_DIR / f"{lang}.csv"
    quiz_csv = SEED_DIR / f"{lang}_quiz.csv"

    grammar_rows = _read_csv(grammar_csv)
    quiz_rows = _read_csv(quiz_csv)
    done = {(row["level"], row["subject"]) for row in grammar_rows}

    for row in grid:
        level = row["level"].strip()
        subject = row["subject"].strip()
        if (level, subject) in done:
            continue

        cefr = CEFR_BY_LEVEL[int(level)]
        print(f"생성 중: level={level}({cefr}) subject={subject}")
        try:
            result = generate_one(language, cefr, subject)
        except Exception as e:
            print(f"  [실패] {subject}: {e}")
            continue

        grammar_rows.append({
            "lang_id": lang_id,
            "level": level,
            "subject": subject,
            "grammar_expl": result.grammar_expl.strip(),
        })
        for quiz in result.quizzes:
            quiz_rows.append({
                "level": level,
                "subject": subject,
                "problem": quiz.problem.strip(),
                "answer": quiz.answer.strip(),
            })

        # subject 단위로 즉시 저장 -> 중간에 실패해도 재실행 시 이어서 생성 가능
        _write_csv(grammar_csv, grammar_rows, ["lang_id", "level", "subject", "grammar_expl"])
        _write_csv(quiz_csv, quiz_rows, ["level", "subject", "problem", "answer"])

    print(f"완료: {grammar_csv} ({len(grammar_rows)}개), {quiz_csv} ({len(quiz_rows)}개)")


if __name__ == "__main__":
    main()
