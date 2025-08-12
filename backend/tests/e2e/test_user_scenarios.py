"""
End-to-end tests for complete user scenarios.
"""
import pytest
from pathlib import Path

from tests.utils.helpers import create_test_file, assert_response_ok
from tests.utils.factories import UserFactory, DocumentFactory


class TestUserScenarios:
    """Test realistic user scenarios end-to-end."""
    
    def test_new_user_onboarding(self, client, mock_file_upload):
        """Test complete new user onboarding flow."""
        # Step 1: User visits the platform and registers
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePassword123!"
        }
        
        response = client.post("/api/auth/register", json=registration_data)
        user_data = assert_response_ok(response)
        
        assert user_data["email"] == registration_data["email"]
        assert user_data["username"] == registration_data["username"]
        
        # Step 2: User logs in
        response = client.post(
            "/api/auth/login",
            data={
                "username": registration_data["username"],
                "password": registration_data["password"]
            }
        )
        
        login_data = assert_response_ok(response)
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: User checks their profile
        response = client.get("/api/auth/me", headers=headers)
        profile = assert_response_ok(response)
        
        assert profile["email"] == registration_data["email"]
        
        # Step 4: User uploads their first document
        file = create_test_file("onboarding_doc.pdf", b"My first document")
        
        response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={"file": ("onboarding_doc.pdf", file, "application/pdf")}
        )
        
        upload_data = assert_response_ok(response)
        doc_id = upload_data["document"]["id"]
        
        # Step 5: User views their document list
        response = client.get("/api/documents/", headers=headers)
        docs = assert_response_ok(response)
        
        assert docs["total"] == 1
        assert docs["documents"][0]["id"] == doc_id
    
    def test_researcher_workflow(self, client, db_session, mock_file_upload):
        """Test a researcher uploading and managing multiple documents."""
        # Setup: Create researcher account
        researcher = UserFactory.create(
            email="researcher@university.edu",
            username="researcher"
        )
        db_session.add(researcher)
        db_session.commit()
        
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": researcher.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Researcher uploads multiple research papers
        papers = [
            ("ML_Research_2024.pdf", b"Machine Learning Research Content"),
            ("AI_Ethics_Paper.pdf", b"AI Ethics Discussion"),
            ("Data_Analysis_Results.pdf", b"Statistical Analysis"),
        ]
        
        uploaded_ids = []
        
        for filename, content in papers:
            file = create_test_file(filename, content)
            
            response = client.post(
                "/api/documents/upload",
                headers=headers,
                files={"file": (filename, file, "application/pdf")}
            )
            
            data = assert_response_ok(response)
            uploaded_ids.append(data["document"]["id"])
        
        # Researcher searches through their documents
        response = client.get("/api/documents/", headers=headers)
        all_docs = assert_response_ok(response)
        
        assert all_docs["total"] == 3
        
        # Researcher reviews a specific document
        response = client.get(f"/api/documents/{uploaded_ids[0]}", headers=headers)
        doc = assert_response_ok(response)
        
        assert doc["original_filename"] == "ML_Research_2024.pdf"
        
        # Researcher deletes an old document
        response = client.delete(f"/api/documents/{uploaded_ids[2]}", headers=headers)
        assert_response_ok(response)
        
        # Verify deletion
        response = client.get("/api/documents/", headers=headers)
        remaining_docs = assert_response_ok(response)
        
        assert remaining_docs["total"] == 2
    
    def test_team_collaboration_scenario(self, client, db_session, mock_file_upload):
        """Test team members working with shared documents."""
        # Create team members
        team_lead = UserFactory.create(username="team_lead")
        member1 = UserFactory.create(username="member1")
        member2 = UserFactory.create(username="member2")
        
        db_session.add_all([team_lead, member1, member2])
        db_session.commit()
        
        from app.core.security import create_access_token
        
        # Each team member uploads their documents
        team_docs = {}
        
        for user in [team_lead, member1, member2]:
            token = create_access_token(data={"sub": user.id})
            headers = {"Authorization": f"Bearer {token}"}
            
            # Upload a document
            file = create_test_file(
                f"{user.username}_report.pdf",
                f"Report by {user.username}".encode()
            )
            
            response = client.post(
                "/api/documents/upload",
                headers=headers,
                files={"file": (f"{user.username}_report.pdf", file, "application/pdf")}
            )
            
            data = assert_response_ok(response)
            team_docs[user.username] = data["document"]["id"]
        
        # Verify each user can only see their own documents
        for user in [team_lead, member1, member2]:
            token = create_access_token(data={"sub": user.id})
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/api/documents/", headers=headers)
            docs = assert_response_ok(response)
            
            # Each user should only see their own document
            assert docs["total"] == 1
            assert docs["documents"][0]["original_filename"] == f"{user.username}_report.pdf"
    
    def test_error_recovery_scenario(self, client, mock_file_upload):
        """Test how the system handles and recovers from errors."""
        # Register user
        response = client.post(
            "/api/auth/register",
            json={
                "email": "errortest@example.com",
                "username": "errortest",
                "password": "TestPass123!"
            }
        )
        assert_response_ok(response)
        
        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            data={
                "username": "errortest",
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
        
        # Login with correct password
        response = client.post(
            "/api/auth/login",
            data={
                "username": "errortest",
                "password": "TestPass123!"
            }
        )
        login_data = assert_response_ok(response)
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to upload invalid file
        file = create_test_file("invalid.exe", b"Invalid content")
        
        response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={"file": ("invalid.exe", file, "application/x-msdownload")}
        )
        assert response.status_code == 400
        
        # Upload valid file after error
        file = create_test_file("valid.pdf", b"Valid content")
        
        response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={"file": ("valid.pdf", file, "application/pdf")}
        )
        
        data = assert_response_ok(response)
        doc_id = data["document"]["id"]
        
        # Try to access non-existent document
        response = client.get(
            "/api/documents/nonexistent-id",
            headers=headers
        )
        assert response.status_code == 404
        
        # Access valid document after error
        response = client.get(f"/api/documents/{doc_id}", headers=headers)
        assert_response_ok(response)