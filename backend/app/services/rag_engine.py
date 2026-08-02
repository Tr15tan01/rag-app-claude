import uuid
import logging
import httpx
from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Chunk, Document
from app.services.embeddings import embed_query
from app.guardrails import build_safe_prompt, scrub_output

# Created lazily so the app doesn't require an Anthropic key when
# GENERATION_PROVIDER=gemini.
_anthropic_client: AsyncAnthropic | None = None


def _get_anthropic_client() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


async def _generate_anthropic(prompt: str) -> str:
    response = await _get_anthropic_client().messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


async def _generate_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024},
    }
    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.is_error:
            logging.getLogger(__name__).error("Gemini API error %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        data = resp.json()
        candidate = data["candidates"][0]
        return "".join(part.get("text", "") for part in candidate["content"]["parts"])


async def _generate(prompt: str) -> str:
    if settings.GENERATION_PROVIDER == "gemini":
        return await _generate_gemini(prompt)
    return await _generate_anthropic(prompt)


async def retrieve(
    db: AsyncSession,
    owner_id: uuid.UUID,
    query: str,
    top_k: int = 5,
    document_ids: list[uuid.UUID] | None = None,
):
    """Vector similarity search scoped to the current user's documents only
    -- this is the row-level access control that keeps User A from ever
    retrieving User B's document chunks, enforced at the query level."""
    query_vec = await embed_query(query)

    stmt = (
        select(
            Chunk,
            Document.filename,
            Chunk.embedding.cosine_distance(query_vec).label("distance"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.owner_id == owner_id)
    )
    if document_ids:
        stmt = stmt.where(Chunk.document_id.in_(document_ids))

    stmt = stmt.order_by("distance").limit(top_k)
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "chunk": chunk,
            "filename": filename,
            "score": 1 - distance,  # convert cosine distance -> similarity
        }
        for chunk, filename, distance in rows
    ]


async def answer_query(
    db: AsyncSession,
    owner_id: uuid.UUID,
    query: str,
    document_ids: list[uuid.UUID] | None = None,
) -> dict:
    retrieved = await retrieve(db, owner_id, query, document_ids=document_ids)

    if not retrieved:
        return {
            "answer": "I couldn't find anything relevant in your uploaded documents to answer that.",
            "sources": [],
        }

    prompt = build_safe_prompt(query, [r["chunk"].text for r in retrieved])
    raw_answer = await _generate(prompt)
    answer = scrub_output(raw_answer)

    sources = [
        {
            "document_id": r["chunk"].document_id,
            "filename": r["filename"],
            "page_number": r["chunk"].page_number,
            "text": r["chunk"].text,
            "score": round(float(r["score"]), 4),
        }
        for r in retrieved
    ]
    return {"answer": answer, "sources": sources}