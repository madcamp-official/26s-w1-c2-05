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


class DialogueTurnResult(BaseModel):
    advance_flow: bool = Field(
        description="사용자의 직전 응답이 현재 flow 단계를 통과할 만큼 문법/의미상 충분히 자연스러웠는지 여부. "
                    "true면 다음 flow 단계로 진행하는 문장을, false면 같은 flow 단계에 머무르며 사용자가 "
                    "다시 시도하도록 유도하는 문장을 생성해야 한다."
    )
    content: str = Field(description="사용자에게 보여줄 다음 대화 문장. 반드시 학습 언어(language)로 작성한다.")
    feedback: str = Field(description="사용자의 직전 응답에 대한 한국어 피드백. 간결하고 구체적으로 작성한다.")


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
        "피드백(feedback)은 항상 한국어로, 무엇이 맞았고 무엇이 부족했는지 구체적으로 작성한다 "
        "(예: \"의미는 통하지만 목적어가 빠졌습니다.\").",
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
) -> str:
    '''대화 주제/흐름만 주어졌을 때, 첫 flow 단계에 맞는 대화 시작 문장을 생성한다.'''
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
    result: DialogueOpeningResult = response.parsed
    return result.content


def generate_dialogue_turn(
    subject: str,
    language: str,
    flow_stages: list[str],
    current_flow: str,
    user_response: str,
    target_words: Optional[list[str]] = None,
) -> DialogueTurnResult:
    '''
    사용자의 응답을 평가해 advance_flow(다음 단계로 넘어갈지)와, 그에 맞는 다음 대화
    문장(content) 및 한국어 피드백(feedback)을 생성한다.

    사용자의 응답이 지나치게 부정확하거나 문법적으로는 맞아도 문맥/의미상 현재 flow 단계에
    어울리지 않으면 advance_flow=False로, 그 외에는 advance_flow=True로 판단하도록
    system_instruction에 명시되어 있다. 실제 flow 진행/종료 여부는 이 값을 바탕으로
    app/utils/learning.py가 결정한다 (LLM이 flow 위치를 직접 세다가 오판하는 것을 방지).
    '''
    system_instruction = _build_system_instruction(subject, language, flow_stages, target_words)
    contents = (
        f"지금은 \"{current_flow}\" 단계이다.\n"
        f"사용자의 응답: \"{user_response}\"\n"
        "이 응답이 현재 단계를 통과할 만큼 충분한지 평가한 뒤, advance_flow를 결정하고 "
        "그에 맞는 다음 대화 문장과 피드백을 생성해라."
    )

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
