'''
Gemini API 연동 모듈입니다.

app/utils/learning.py의 회화(Dialogue) 문장/피드백 생성 로직이 이 모듈을 통해 Gemini를
호출한다. 대화 진행(flow가 다음 단계로 넘어갈지 여부)과 종료 여부(is_end)는 flow 목록 위치를
기준으로 서버(app/utils/learning.py)가 구조적으로 판단하므로, 이 모듈은 다음 두 가지만
LLM에게 맡긴다.

  1) 사용자의 응답을 평가해 현재 flow 단계를 통과시킬지(advance_flow) 판단
  2) 그 판단에 맞는 다음 대화 문장(content)과 한국어 피드백(feedback) 생성

주제(subject)에서 벗어나지 않도록 하는 것, 학습 언어로 문장을 작성하는 것, 추천 단어를
자연스럽게 사용하는 것 등은 system_instruction의 제약 조건으로 명시한다.
'''

import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

client = genai.Client()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


class DialogueOpeningResult(BaseModel):
    content: str = Field(description="사용자에게 보여줄 대화 시작 문장. 반드시 학습 언어(language)로 작성한다.")
    translation: str = Field(description="content를 자연스러운 한국어로 옮긴 번역문.")


class DialogueTurnResult(BaseModel):
    advance_flow: bool = Field(
        description="사용자의 직전 응답이 현재 flow 단계를 통과할 만큼 문법/의미상 충분히 자연스러웠는지 여부. "
                    "true면 다음 flow 단계로 진행하는 문장을, false면 같은 flow 단계에 머무르며 사용자가 "
                    "다시 시도하도록 유도하는 문장을 생성해야 한다."
    )
    content: str = Field(description="사용자에게 보여줄 다음 대화 문장. 반드시 학습 언어(language)로 작성한다.")
    translation: str = Field(description="content를 자연스러운 한국어로 옮긴 번역문.")
    feedback: str = Field(description="사용자의 직전 응답에 대한 한국어 피드백. 간결하고 구체적으로 작성한다.")


_HANGUL_RE = re.compile(r"[가-힣]")


def _sanitize_translation(translation: str) -> str:
    '''
    system_instruction으로 한국어 번역을 명시해도, 모델이 종종 content를 학습 언어로
    한 번 더 바꿔 쓴("번역"이 아닌 같은 언어의 다른 표현) 문장을 translation에 채워 넣는다.
    이 경우 프론트에서 content 아래에 같은 언어 문장이 중복 표시되므로, 한글이 전혀
    없는 translation은 신뢰하지 않고 빈 문자열로 대체한다(프론트는 빈 translation은 표시하지 않음).
    '''
    return translation if _HANGUL_RE.search(translation) else ""


def _build_system_instruction(
    subject: str,
    language: str,
    flow_stages: list[str],
    target_words: Optional[list[str]] = None,
) -> str:
    flow_text = " -> ".join(flow_stages)
    lines = [
        f"당신은 {language} 회화 학습 앱에서 사용자와 대화하는 상대(NPC) 역할을 맡는다.",
        f"대화 주제(subject)는 반드시 \"{subject}\"이며, 이 주제와 무관한 방향으로 절대 벗어나서는 안 된다.",
        f"전체 대화는 다음 단계 순서(flow)를 따라 진행된다: {flow_text}.",
        f"생성하는 대화 문장(content)은 항상 {language}로 작성한다.",
        "translation은 content를 자연스러운 한국어로 옮긴 번역문이다 (직역이 아닌 의역 가능). "
        "translation에 content를 그대로 복사해 넣으면 안 되며, 반드시 한국어 문장으로 새로 작성한다.",
        "피드백(feedback)은 항상 한국어로, 사용자가 방금 작성한 문장의 문법/자연스러움/어휘 선택에 "
        "대해서만 구체적으로 작성한다 (예: \"의미는 통하지만 목적어가 빠졌습니다.\"). NPC인 당신이 "
        "다음에 무엇을 할지, 어떤 전략으로 대화를 이끌지는 feedback에 쓰지 않는다.",
        "대화 기록(history)이 함께 주어지면, 그 안에서 이미 물어보거나 답한 내용을 다시 묻지 않는다 "
        "— 예를 들어 이름을 이미 받았다면 같은 flow 단계 안에서 다시 이름을 묻지 않는다.",
    ]
    if target_words:
        words_text = ", ".join(target_words)
        lines.append(
            f"자연스럽게 어울리는 경우 다음 학습 단어들을 대화 문장에 포함시킨다 (억지로 모두 넣지는 않는다): {words_text}."
        )
    return "\n".join(lines)


def generate_dialogue_opening(
    subject: str,
    language: str,
    flow_stages: list[str],
    target_words: Optional[list[str]] = None,
) -> DialogueOpeningResult:
    '''대화 주제/흐름만 주어졌을 때, 첫 flow 단계에 맞는 대화 시작 문장(및 한국어 번역)을 생성한다.'''
    system_instruction = _build_system_instruction(subject, language, flow_stages, target_words)
    contents = (
        f"대화를 시작하는 첫 문장을 생성해라. 지금은 \"{flow_stages[0]}\" 단계이다."
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=DialogueOpeningResult,
        ),
    )
    return response.parsed


# 매 턴마다 모델에 함께 보낼 과거 대화 turn 수 상한. 대화가 길어져도(재시도가 잦아도) 토큰 사용량이
# 무한정 늘어나지 않도록 최근 turn만 잘라서 보낸다 — "이미 물어본 걸 다시 묻지 않는" 데는
# 오래된 turn보다 최근 turn이 훨씬 중요하다.
_MAX_HISTORY_TURNS = 8


def _history_to_contents(history: Optional[list]) -> list[types.Content]:
    '''(role, content) 쌍의 대화 기록을 Gemini 멀티턴 contents로 변환한다. 최근 _MAX_HISTORY_TURNS개만 사용.'''
    if not history:
        return []
    trimmed = history[-_MAX_HISTORY_TURNS:]
    return [
        types.Content(
            role="model" if turn.role == "ai" else "user",
            parts=[types.Part(text=turn.content)],
        )
        for turn in trimmed
    ]


def generate_dialogue_turn(
    subject: str,
    language: str,
    flow_stages: list[str],
    current_flow: str,
    user_response: str,
    target_words: Optional[list[str]] = None,
    history: Optional[list] = None,
) -> DialogueTurnResult:
    '''
    사용자의 응답을 평가해 advance_flow(다음 단계로 넘어갈지)와, 그에 맞는 다음 대화
    문장(content) 및 한국어 피드백(feedback)을 생성한다.

    사용자의 응답이 지나치게 부정확하거나 문법적으로는 맞아도 문맥/의미상 현재 flow 단계에
    어울리지 않으면 advance_flow=False로, 그 외에는 advance_flow=True로 판단하도록
    system_instruction에 명시되어 있다. 실제 flow 진행/종료 여부는 이 값을 바탕으로
    app/utils/learning.py가 결정한다 (LLM이 flow 위치를 직접 세다가 오판하는 것을 방지).

    history는 지금까지 실제로 오간 대화 turn들(요청 프론트가 함께 보냄)이다. 이를 함께 넘기지
    않으면 매 호출이 완전히 기억 없는 상태로 판단하게 되어, 이미 받은 답(예: 이름)을 같은 flow
    단계 안에서 다시 묻는 등 대화가 앞뒤가 안 맞게 된다.
    '''
    system_instruction = _build_system_instruction(subject, language, flow_stages, target_words)
    contents = _history_to_contents(history)
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=(
            f"지금은 \"{current_flow}\" 단계이다.\n"
            f"사용자의 응답: \"{user_response}\"\n"
            "위 대화 기록을 참고해서, 이 응답이 현재 단계를 통과할 만큼 충분한지 평가한 뒤, "
            "advance_flow를 결정하고 그에 맞는 다음 대화 문장과 피드백을 생성해라."
        ))],
    ))

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=DialogueTurnResult,
        ),
    )
    return response.parsed

class CategoryFeedbackResult(BaseModel):
    feedback_voca: str = Field(
        description="최근 1주일간의 단어 학습 기록을 바탕으로, 가장 눈에 띄는 피드백 사항을 "
                    "두 줄 이내의 한국어로 작성한다. 학습 기록이 없으면 그 사실을 언급한다."
    )
    feedback_grammar: str = Field(
        description="최근 1주일간의 문법 학습 기록을 바탕으로, 가장 눈에 띄는 피드백 사항을 "
                    "두 줄 이내의 한국어로 작성한다. 학습 기록이 없으면 그 사실을 언급한다."
    )
    feedback_dialogue: str = Field(
        description="최근 1주일간의 회화 학습 기록을 바탕으로, 가장 눈에 띄는 피드백 사항을 "
                    "두 줄 이내의 한국어로 작성한다. 학습 기록이 없으면 그 사실을 언급한다."
    )


def _format_voca_results(results: list[tuple[str, bool]]) -> str:
    if not results:
        return "(최근 1주일간 학습 기록 없음)"
    return "\n".join(f"- {word}: {'정답' if is_correct else '오답'}" for word, is_correct in results)


def _format_grammar_results(results: list[tuple[str, str, bool]]) -> str:
    if not results:
        return "(최근 1주일간 학습 기록 없음)"
    return "\n".join(
        f"- [{subject}] {problem}: {'정답' if is_correct else '오답'}"
        for problem, subject, is_correct in results
    )


def _format_dialogue_results(results: list[bool]) -> str:
    if not results:
        return "(최근 1주일간 학습 기록 없음)"
    n_total = len(results)
    n_correct = sum(results)
    return f"총 {n_total}회 대화 중 {n_correct}회 통과, {n_total - n_correct}회 미통과."


def generate_feedback(
    voca_results: list[tuple[str, bool]],
    grammar_results: list[tuple[str, str, bool]],
    dialogue_results: list[bool],
) -> CategoryFeedbackResult:
    '''
    요청 시간 기준 최근 1주일간의 단어/문법/회화 학습 기록(app/utils/learning.py의
    _gather_recent_feedback_data가 수집)을 한 번에 LLM에 투입해, 세 분야 각각에서 가장
    눈에 띄는 피드백 사항을 두 줄 이내의 한국어로 생성한다 (API 호출 1회로 세 필드를 함께 반환).

    - voca_results: (단어, 정답 여부) 목록
    - grammar_results: (퀴즈 문제, 문법 개념, 정답 여부) 목록
    - dialogue_results: 정답 여부 목록 (회화는 아직 문항 단위 정답 여부만 기록됨)
    '''
    contents = (
        "다음은 한 사용자의 최근 1주일 외국어 학습 기록이다.\n\n"
        f"[단어]\n{_format_voca_results(voca_results)}\n\n"
        f"[문법]\n{_format_grammar_results(grammar_results)}\n\n"
        f"[회화]\n{_format_dialogue_results(dialogue_results)}\n\n"
        "위 기록을 단어/문법/회화 세 분야 각각에 대해 분석해서, 분야마다 가장 눈에 띄는 "
        "피드백 사항을 두 줄 이내의 한국어로 작성해라."
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=(
                "당신은 외국어 학습 앱의 학습 코치이다. 사용자의 최근 학습 기록을 분석해 "
                "단어/문법/회화 세 분야 각각에 대해 간결하고 구체적인 한국어 피드백을 제공한다. "
                "칭찬만 하거나 뭉뚱그리지 말고, 데이터에서 드러나는 구체적인 패턴(자주 틀리는 "
                "부분, 최근 나아진 부분 등)을 짚어라."
            ),
            response_mime_type="application/json",
            response_schema=CategoryFeedbackResult,
        ),
    )
    return response.parsed
