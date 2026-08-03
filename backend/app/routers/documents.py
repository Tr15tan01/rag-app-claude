import asyncio
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.guardrails import validate_upload
from app.models import User, Document, Chunk
from app.schemas import DocumentOut
from app.services.pdf_processor import extract_pages, chunk_pages
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    validate_upload(file.filename, file.content_type, len(file_bytes))

    document = Document(owner_id=current_user.id, filename=file.filename, status="processing")
    db.add(document)
    await db.commit()
    await db.refresh(document)

    try:
        pages = extract_pages(file_bytes)
        chunks = chunk_pages(pages)
        if not chunks:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No extractable text found in this PDF (it may be scanned/image-only).")

        # Embed in small batches with pacing so free-tier rate limits
        # (e.g. Voyage's 3 RPM / 10K TPM without a payment method) aren't
        # exceeded. ~4 chars/token is a safe rough estimate for English text.
        texts = [c["text"] for c in chunks]
        max_tokens_per_batch = 8000  # stay under a 10K TPM budget with margin
        max_chunks_per_batch = 20
        seconds_between_requests = 21  # keeps you under ~3 requests/minute

        batches, current_batch, current_tokens = [], [], 0
        for t in texts:
            est_tokens = max(1, len(t) // 4)
            if current_batch and (
                current_tokens + est_tokens > max_tokens_per_batch
                or len(current_batch) >= max_chunks_per_batch
            ):
                batches.append(current_batch)
                current_batch, current_tokens = [], 0
            current_batch.append(t)
            current_tokens += est_tokens
        if current_batch:
            batches.append(current_batch)

        all_embeddings = []
        for i, batch in enumerate(batches):
            if i > 0:
                await asyncio.sleep(seconds_between_requests)
            all_embeddings.extend(await embed_texts(batch))

        for c, emb in zip(chunks, all_embeddings):
            db.add(
                Chunk(
                    document_id=document.id,
                    owner_id=current_user.id,
                    page_number=c["page"],
                    chunk_index=c["chunk_index"],
                    text=c["text"],
                    embedding=emb,
                )
            )

        document.page_count = len(pages)
        document.status = "ready"
        await db.commit()
        await db.refresh(document)

    except HTTPException:
        document.status = "failed"
        await db.commit()
        raise
    except Exception:
        logger.exception("Document processing failed for %s", file.filename)
        document.status = "failed"
        await db.commit()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to process document.")

    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.owner_id == current_user.id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
    await db.delete(document)  # cascades to chunks
    await db.commit()