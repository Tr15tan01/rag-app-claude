from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

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

        # Embed in batches to keep individual API requests reasonably sized
        batch_size = 64
        texts = [c["text"] for c in chunks]
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            all_embeddings.extend(await embed_texts(texts[i : i + batch_size]))

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