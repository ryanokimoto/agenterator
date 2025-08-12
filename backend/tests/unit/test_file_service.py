"""
Unit tests for file service.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

from fastapi import UploadFile, HTTPException
from app.services.file_service import FileService


class TestFileService:
    """Test file service functionality."""
    
    @pytest.fixture
    def file_service(self, temp_upload_dir):
        """Create file service with temp directory."""
        service = FileService()
        service.UPLOAD_DIR = Path(temp_upload_dir)
        return service
    
    @pytest.fixture
    def mock_upload_file(self):
        """Create mock upload file."""
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.content_type = "application/pdf"
        return file
    
    @pytest.mark.asyncio
    async def test_validate_file_success(self, file_service, mock_upload_file):
        """Test successful file validation."""
        # Setup mock file
        content = b"PDF content here" * 100
        mock_upload_file.read = Mock(return_value=content)
        mock_upload_file.seek = Mock()
        
        with patch('magic.from_buffer', return_value='application/pdf'):
            # Should not raise exception
            await file_service.validate_file(mock_upload_file)
        
        # Verify file was read and seek was called
        mock_upload_file.read.assert_called()
        mock_upload_file.seek.assert_called()
    
    @pytest.mark.asyncio
    async def test_validate_file_no_filename(self, file_service):
        """Test validation fails when no filename."""
        file = Mock(spec=UploadFile)
        file.filename = None
        
        with pytest.raises(HTTPException) as exc:
            await file_service.validate_file(file)
        
        assert exc.value.status_code == 400
        assert "No file provided" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_file_invalid_extension(self, file_service, mock_upload_file):
        """Test validation fails for invalid file extension."""
        mock_upload_file.filename = "test.exe"
        
        with pytest.raises(HTTPException) as exc:
            await file_service.validate_file(mock_upload_file)
        
        assert exc.value.status_code == 400
        assert "File type not allowed" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, file_service, mock_upload_file):
        """Test validation fails for oversized file."""
        # Create content larger than limit
        large_content = b"x" * (file_service.MAX_FILE_SIZE + 1)
        mock_upload_file.read = Mock(return_value=large_content)
        mock_upload_file.seek = Mock()
        
        with pytest.raises(HTTPException) as exc:
            await file_service.validate_file(mock_upload_file)
        
        assert exc.value.status_code == 400
        assert "File too large" in str(exc.value.detail)
    
    @pytest.mark.asyncio
    async def test_validate_file_empty(self, file_service, mock_upload_file):
        """Test validation fails for empty file."""
        mock_upload_file.read = Mock(return_value=b"")
        mock_upload_file.seek = Mock()
        
        with pytest.raises(HTTPException) as exc:
            await file_service.validate_file(mock_upload_file)
        
        assert exc.value.status_code == 400
        assert "File is empty" in str(exc.value.detail)
    
    def test_generate_unique_filename(self, file_service):
        """Test unique filename generation."""
        original = "document.pdf"
        user_id = "user-123-456"
        
        filename = file_service.generate_unique_filename(original, user_id)
        
        assert filename.endswith(".pdf")
        assert "user-123" in filename
        assert len(filename) > len(original)
        
        # Test uniqueness
        filename2 = file_service.generate_unique_filename(original, user_id)
        assert filename != filename2
    
    @pytest.mark.asyncio
    async def test_save_file_success(self, file_service, mock_upload_file, temp_upload_dir):
        """Test successful file save."""
        content = b"Test file content"
        mock_upload_file.read = Mock(return_value=content)
        
        unique_filename = "test_123.pdf"
        file_path, file_size = await file_service.save_file(mock_upload_file, unique_filename)
        
        # Verify file was saved
        assert Path(file_path).exists()
        assert file_size == len(content)
        
        # Verify content
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == content
    
    @pytest.mark.asyncio
    async def test_save_file_failure(self, file_service, mock_upload_file):
        """Test file save failure handling."""
        mock_upload_file.read = Mock(side_effect=Exception("Read error"))
        
        with pytest.raises(HTTPException) as exc:
            await file_service.save_file(mock_upload_file, "test.pdf")
        
        assert exc.value.status_code == 500
        assert "Failed to save file" in str(exc.value.detail)
    
    def test_extract_pdf_metadata(self, file_service):
        """Test PDF metadata extraction."""
        # Create a mock PDF file
        with patch('builtins.open', create=True) as mock_open:
            with patch('PyPDF2.PdfReader') as mock_reader:
                # Setup mock PDF reader
                mock_pdf = Mock()
                mock_pdf.pages = [Mock()] * 5  # 5 pages
                mock_pdf.is_encrypted = False
                mock_pdf.metadata = {
                    '/Title': 'Test Document',
                    '/Author': 'Test Author'
                }
                
                # Setup page text extraction
                for page in mock_pdf.pages:
                    page.extract_text.return_value = "Sample text " * 10
                
                mock_reader.return_value = mock_pdf
                
                metadata = file_service.extract_pdf_metadata("test.pdf")
        
        assert metadata["page_count"] == 5
        assert metadata["is_encrypted"] is False
        assert metadata["word_count"] > 0
    
    def test_delete_file_success(self, file_service, temp_upload_dir):
        """Test successful file deletion."""
        # Create a test file
        test_file = Path(temp_upload_dir) / "test.txt"
        test_file.write_text("test content")
        
        assert test_file.exists()
        
        result = file_service.delete_file(str(test_file))
        
        assert result is True
        assert not test_file.exists()
    
    def test_delete_file_not_exists(self, file_service):
        """Test deleting non-existent file."""
        result = file_service.delete_file("/path/to/nonexistent.txt")
        
        assert result is False