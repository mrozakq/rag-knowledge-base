import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pipeline.query import answer
from .auth import require_api_key

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    language: str = "pl"


@router.post("/query")
async def query(req: QueryRequest, _=Depends(require_api_key)):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, answer, req.question)
    return result
