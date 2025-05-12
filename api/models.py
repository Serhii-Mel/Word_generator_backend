from pydantic import BaseModel
from typing import List, Optional

class ScriptRequest(BaseModel):
    title: str
    inspirational_transcript: Optional[str] = None
    word_count: int
    forbidden_words: List[str] = []
    structure_prompt: str = ''

class ScriptResponse(BaseModel):
    paragraphs: List[str]
    total_words: int

class ParagraphRequest(BaseModel):
    paragraph_index: int
    context: str
    old_paragraph: str 