"""
Documents API Router.
Why this file exists: Exposes endpoints for uploading and listing enterprise documents.
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api import deps
from app.models.user import User
from app.models.document import Document as DBDocument
from app.schemas.document import DocumentResponse
from app.services.pdf_service import extract_text_from_pdf
from app.services.rag_service import process_and_index_document
import os

router = APIRouter()

# Temporary local storage for uploaded files before indexing
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Upload a PDF document, extract text, chunk, and index into ChromaDB.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()
    
    # Save physically (optional, but good for reference/downloads later)
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    db_doc = DBDocument(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(file_bytes),
        chunk_count=0
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    pages_data = extract_text_from_pdf(file_bytes)

    chunks_created = process_and_index_document(
        user_id=current_user.id,
        document_id=db_doc.id,
        filename=db_doc.filename,
        pages_data=pages_data
    )

    db_doc.chunk_count = chunks_created

    db.commit()
    db.refresh(db_doc)

    return db_doc

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    List all documents uploaded by the current user.
    """
    return db.query(DBDocument).filter(DBDocument.user_id == current_user.id).all()
