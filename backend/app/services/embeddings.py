"""
Embedding generation. Anthropic doesn't offer an embeddings endpoint, so
this uses Voyage AI (Anthropic's recommended embedding partner) by default,
with OpenAI as an alternative -- switch via EMBEDDING_PROVIDER in .env.
"""
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _embed_voyage(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.VOYAGE_API_KEY}"},
            json={"input": texts, "model": "voyage-4"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _embed_openai(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"input": texts, "model": "text-embedding-3-small"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _embed_gemini(texts: list[str]) -> list[list[float]]:
    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:batchEmbedContents"
    requests = [
        {"model": "models/text-embedding-004", "content": {"parts": [{"text": t}]}}
        for t in texts
    ]
    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json={"requests": requests})
        resp.raise_for_status()
        data = resp.json()
        return [item["values"] for item in data["embeddings"]]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.EMBEDDING_PROVIDER == "openai":
        return await _embed_openai(texts)
    if settings.EMBEDDING_PROVIDER == "gemini":
        return await _embed_gemini(texts)
    return await _embed_voyage(texts)


async def embed_query(text: str) -> list[float]:
    result = await embed_texts([text])
    return result[0]