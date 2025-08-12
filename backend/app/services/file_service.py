import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional BinaryIO
from datetime import datetime
import magic
import PyPDF2
from fastapi import UploadFile, HTTPException, status

class FileService:
    UPLOAD_DIR = Path("uploads")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".pptx"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        for subdir in ["pdf", "docx", "txt", "pptx"]:
            (self.UPLOAD_DIR / subdir).mkdir(exist_ok=True)
    
    async def validate_file(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided",
            )
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types are: {', '.join(self.ALLOWED_EXTENSIONS)}",
            )
        
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the maximum limit of {self.MAX_FILE_SIZE / (1024 * 1024)} MB",
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )
        
        await file.seek(0)

        mime = magic.from_buffer(file_content[:2048], mime=True)
        if mime not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Detected: {mime}",
            )
        
        await file.seek(0)

    def generate_unique_filename(self, filename: str, user_id: str) -> str:
        file_ext = Path(filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_hash = hashlib.md5(f"{filename}{user_id}{timestamp}".encode()).hexdigest()[:8]
        unique_filename = f"{timestamp}_{user_id[:8]}_{filehash}{file_ext}"

        return unique_filename

    async def save_file(self, file: UploadFile, unique_filename: str) -> tuple[str, int]:
        file_ext = Path(file.filename).suffix.lower().strip(".")
        file_dir = self.UPLOAD_DIR / file_ext
        file_path = file_dir / unique_filename

        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            return str(file_path), len(content)
    
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )
        
    def extract_pdf_metadata(self, file_path: str) -> dict:
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "is_encrypted": pdf_reader.is_encrypted,
                }
                
                text = ""
                for page in pdf_reader.pages[:5]:
                    text += page.extract_text()
                word_count = len(text.split()) if text else 0
                metadata["word_count"] = word_count

                if pdf_reader.metadata:
                    metadata["title"] = pdf_reader.metadata.get('/Title', 'Unknown')
                    metadata["author"] = pdf_reader.metadata.get('/Author', 'Unknown')
                    metadata["subject"] = pdf_reader.metadata.get('/Subject', 'Unknown')
                return metadata
        except Exception as e:
            print(f"Error extracting PDF metadata: {str(e)}")
            return {
                "page_count": None,
                "word_count": None,
            }

        def delete_file(self, file_path: str) -> bool:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    return True
                return False
            except Exception as e:
                print(f"Error deleting file {file_path}: {str(e)}")
                return False

file_service = FileService()