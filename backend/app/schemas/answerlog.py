from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AnswerResponse(BaseModel):
  content_id: int
  type: str
  response_time: float
  is_correct: bool
  time: datetime