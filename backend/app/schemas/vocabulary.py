from pydantic import BaseModel, ConfigDict

class VocabularyItem(BaseModel):
    number: int
    content_id: int
    word: str
    meaning: str
    example: str | None = None

    model_config = ConfigDict(from_attributes=True)

class VocabularyResponse(BaseModel):
    vocabularies: list[VocabularyItem]
