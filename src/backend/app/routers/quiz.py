from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["quiz"])


class QuizGenerateRequest(BaseModel):
    grade: str
    semester: str
    genre: str
    importance: str
    count: int = 10


class QuizQuestion(BaseModel):
    question: str
    answer: str
    source: str


class QuizGenerateResponse(BaseModel):
    questions: List[QuizQuestion]


@router.post("/quiz/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    # TODO: 接入 LLM 服务生成题目
    return QuizGenerateResponse(
        questions=[
            QuizQuestion(
                question="____，志在千里。（《龟虽寿》曹操）",
                answer="老骥伏枥",
                source="《龟虽寿》",
            )
        ]
    )
