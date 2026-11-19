"""TEMPORARY RAG STUB — Katya replaces this implementation.

Stable integration contract (do not change without coordinating the team):
    answer_question(question: str) -> {"answer": str, "sources": list[str]}
The function may also be declared `async def`. Both are accepted by the adapter.
No recipes, BM25 or LLM are implemented here yet.
"""


def answer_question(question: str) -> dict:
    return {
        "answer": "[ЗАГЛУШКА RAG] Запрос принят. Поиск рецептов и LLM ещё не подключены.",
        "sources": [],
    }
