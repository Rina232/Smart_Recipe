"""The only place that imports Katya's module.

Works with either a synchronous or an asynchronous answer_question function.
"""
import inspect
import logging

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.schemas import RagAnswer
from rag.pipeline import answer_question

logger = logging.getLogger(__name__)


async def invoke_rag(question: str) -> RagAnswer:
    try:
        if inspect.iscoroutinefunction(answer_question):
            raw = await answer_question(question)
        else:
            raw = await run_in_threadpool(answer_question, question)
            if inspect.isawaitable(raw):
                raw = await raw
        return RagAnswer.model_validate(raw)
    except (ValidationError, TypeError, ValueError):
        logger.exception("RAG returned an invalid response")
        raise HTTPException(status_code=502, detail="Неверный формат ответа RAG") from None
    except HTTPException:
        raise
    except Exception:
        logger.exception("RAG execution failed")
        raise HTTPException(status_code=503, detail="Сервис подбора рецептов временно недоступен") from None
