from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import magic

from app.api.dependencies import get_db
from app.api.endpoints.auth import get_current_user
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentList
from app.services.file_service import file_service

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await file_service.validate_file(file)
    unique_filename = file_service.generate_unique_filename(
        file.filename, 
        current_user.id
    )
    file_path, file_size = await file_service.save_file(file, unique_filename)

    try:
        file_ext = file.filename.split('.')[-1].lower()
        doc_type_map = {
            "pdf": DocumentType.PDF,
            "docx": DocumentType.DOCX,
            "txt": DocumentType.TXT,
            "pptx": DocumentType.PPTX
        }
        doc_type = doc_type_map.get(file_ext, DocumentType.PDF)

        await file.seek(0)
        file_content = await file.read(2048)
        mime_type = magic.from_buffer(file_content, mime=True)

        metadata = {}
        if doc_type == DocumentType.PDF:
            metadata = file_service.extract_pdf_metadata(file_path)
        
        document = Document{
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=doc_type,
            mime_type=mime_type,
            status=DocumentStatus.PENDING,
            page_count=metadata.get("page_count"),
            word_count=metadata.get("word_count"),
        }
        db.add(document)
        db.commit()
        db.refresh(document)

        return DocumentUploadResponse(
            message="Document uploaded successfully. Processing will start shortly.",
            document=DocumentResponse.model_validate(document)
        )
    except Exception as e:  
        file_service.delete_file(file_path)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.get("/", response_model=DocumentList)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(Document).filter(Document.user_id == current_user.id).count()
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return DocumentList(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total_count=total
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return DocumentResponse.model_validate(document)

@router.delete("/{document_id")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    file_service.delete_file(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}