from pydantic import BaseModel, Field
from typing import List, Optional

class ChatAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500, description="Nội dung câu hỏi của du khách")
    lang: str = Field("vi", max_length=10, description="Mã ngôn ngữ ISO (vi, en, zh, ja,...)")

class SourceItem(BaseModel):
    poi_id: int
    title: str
    score: float

class ChatAskResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = Field(default_factory=list)
    cached: bool = False
    lang: str = "vi"
