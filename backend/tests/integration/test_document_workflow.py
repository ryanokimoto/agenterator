"""
Integration tests for document workflow.
"""
import pytest
from pathlib import Path
import io

from tests.utils.helpers import create_test_file, assert_response_ok, assert_response_error
from tests.utils.factories import UserFactory, DocumentFactory


class TestDocumentWorkflow:
    """Test complete document workflow from upload to deletion."""
    
    @pytest.mark.asyncio
    async def test_complete_document_lifecycle(
        self,
        authenticated_client,
        test_user,
        mock_file_upload
    ):
        """Test full document lifecycle: upload, retrieve, update, delete."""
        client = authenticated_client
        
        # Step 1: Upload document
        file = create_test_file("lifecycle_test.pdf", b"PDF content for lifecycle test")
        
        response = client.post(
            "/api/documents/upload",
            files={"file": ("lifecycle_test.pdf", file, "application/pdf")}
        )
        
        upload_data = assert_response_ok(response, 200)
        assert "document" in upload_data
        doc_id = upload_data["document"]["id"]
        
        # Step 2: Retrieve document
        response = client.get(f"/api/documents/{doc_id}")
        doc_data = assert_response_ok(response)
        
        assert doc_data["id"] == doc_id
        assert doc_data["original_filename"] == "lifecycle_test.pdf"
        assert doc_data["status"] == "pending"
        
        # Step 3: List documents
        response = client.get("/api/documents/")
        list_data = assert_response_ok(response)
        
        assert list_data["total"] >= 1
        assert any(d["id"] == doc_id for d in list_data["documents"])
        
        # Step 4: Delete document
        response = client.delete(f"/api/documents/{doc_id}")
        assert_response_ok(response)
        
        # Step 5: Verify deletion
        response = client.get(f"/api/documents/{doc_id}")
        assert_response_error(response, 404, "Document not found")
    
    @pytest.mark.asyncio
    async def test_document_isolation_between_users(
        self,
        client,
        db_session,
        mock_file_upload
    ):
        """Test that users can only access their own documents."""
        # Create two users
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # User 1 uploads a document
        from app.core.security import create_access_token
        
        token1 = create_access_token(data={"sub": user1.id})
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        file = create_test_file("user1_doc.pdf", b"User 1 document")
        response = client.post(
            "/api/documents/upload",
            headers=headers1,
            files={"file": ("user1_doc.pdf", file, "application/pdf")}
        )
        
        doc_data = assert_response_ok(response)
        doc_id = doc_data["document"]["id"]
        
        # User 2 tries to access User 1's document
        token2 = create_access_token(data={"sub": user2.id})
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response = client.get(f"/api/documents/{doc_id}", headers=headers2)
        assert_response_error(response, 404)
        
        # User 2's document list should be empty
        response = client.get("/api/documents/", headers=headers2)
        list_data = assert_response_ok(response)
        assert list_data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(
        self,
        authenticated_client,
        mock_file_upload
    ):
        """Test handling of concurrent document uploads."""
        import asyncio
        
        client = authenticated_client
        
        async def upload_document(index: int):
            """Upload a single document."""
            file = create_test_file(f"concurrent_{index}.txt", f"Content {index}".encode())
            
            response = client.post(
                "/api/documents/upload",
                files={"file": (f"concurrent_{index}.txt", file, "text/plain")}
            )
            
            return assert_response_ok(response)
        
        # Upload 5 documents concurrently
        tasks = [upload_document(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all uploads succeeded
        assert len(results) == 5
        for result in results:
            assert "document" in result
            assert result["document"]["status"] == "pending"
        
        # Verify all documents are in the list
        response = client.get("/api/documents/")
        list_data = assert_response_ok(response)
        assert list_data["total"] >= 5
    
    def test_document_pagination(
        self,
        authenticated_client,
        db_session,
        test_user
    ):
        """Test document list pagination."""
        client = authenticated_client
        
        # Create 15 documents
        documents = DocumentFactory.create_batch(15, user_id=test_user.id)
        for doc in documents:
            db_session.add(doc)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/documents/?skip=0&limit=5")
        page1 = assert_response_ok(response)
        
        assert len(page1["documents"]) == 5
        assert page1["total"] == 15
        
        # Test second page
        response = client.get("/api/documents/?skip=5&limit=5")
        page2 = assert_response_ok(response)
        
        assert len(page2["documents"]) == 5
        
        # Test last page
        response = client.get("/api/documents/?skip=10&limit=5")
        page3 = assert_response_ok(response)
        
        assert len(page3["documents"]) == 5
        
        # Verify no duplicate documents across pages
        all_ids = set()
        for page in [page1, page2, page3]:
            for doc in page["documents"]:
                assert doc["id"] not in all_ids
                all_ids.add(doc["id"])
    
    def test_document_file_type_handling(
        self,
        authenticated_client,
        mock_file_upload
    ):
        """Test handling of different file types."""
        client = authenticated_client
        
        test_files = [
            ("test.pdf", b"PDF content", "application/pdf"),
            ("test.txt", b"Text content", "text/plain"),
            ("test.docx", b"DOCX content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ]
        
        uploaded_docs = []
        
        for filename, content, mime_type in test_files:
            file = create_test_file(filename, content)
            
            response = client.post(
                "/api/documents/upload",
                files={"file": (filename, file, mime_type)}
            )
            
            # Mock the magic mime type detection
            with patch('magic.from_buffer', return_value=mime_type):
                data = assert_response_ok(response)
                uploaded_docs.append(data["document"])
        
        # Verify all file types were handled correctly
        assert len(uploaded_docs) == 3
        
        file_types = [doc["file_type"] for doc in uploaded_docs]
        assert "pdf" in file_types
        assert "txt" in file_types
        assert "docx" in file_types