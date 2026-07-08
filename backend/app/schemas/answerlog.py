from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal

class AnswerResponse(BaseModel):
  content_id: int
  type: str
  response_time: float
  is_correct: bool
  time: datetime

class DialogueTurn(BaseModel):
  role: Literal["user", "ai"]
  content: str

class DialogueResponse(BaseModel):
  content_id: int
  flow: str
  response: str
  response_time: float
  time: datetime
  # 이번 응답 이전까지의 대화. LLM이 turn마다 기억 없이 판단하다가 이미 물어본 것을 다시
  # 묻는 문제(예: 이름을 두 번 받고도 또 물어보는 경우)를 막기 위해 프론트가 매번 함께 보낸다.
  # 백엔드가 turn 단위 대화 내용을 별도 저장하지 않기 때문 (app/api/gemini.py 참고).
  history: list[DialogueTurn] = []
