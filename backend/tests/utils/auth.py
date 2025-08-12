"""
Authentication utilities for testing.
"""
from typing import Optional, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import create_access_token, verify_password
from tests.utils.factories import UserFactory


class AuthHelper:
    """Helper class for authentication in tests."""
    
    def __init__(self, client: TestClient, db_session: Session):
        self.client = client
        self.db_session = db_session
    
    def create_user(
        self,
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: str = "TestPass123!",
        **kwargs
    ) -> User:
        """
        Create a user and add to database.
        
        Args:
            email: User email
            username: Username
            password: Plain text password
            **kwargs: Additional user attributes
        
        Returns:
            Created user object
        """
        user = UserFactory.create_with_password(
            password=password,
            email=email or f"user_{UserFactory._counter}@test.com",
            username=username or f"user_{UserFactory._counter}",
            **kwargs
        )
        
        self.db_session.add(user)
        self.db_session.commit()
        self.db_session.refresh(user)
        
        return user
    
    def login(
        self,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Login and get token.
        
        Args:
            username: Username or email
            password: Password
        
        Returns:
            Response data including token
        """
        response = self.client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password
            }
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()
    
    def register_and_login(
        self,
        email: str = "newuser@test.com",
        username: str = "newuser",
        password: str = "TestPass123!"
    ) -> tuple:
        """
        Register a new user and login.
        
        Args:
            email: User email
            username: Username
            password: Password
        
        Returns:
            Tuple of (user_data, token)
        """
        # Register
        register_response = self.client.post(
            "/api/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
        user_data = register_response.json()
        
        # Login
        login_data = self.login(username, password)
        
        return user_data, login_data["access_token"]
    
    def get_auth_headers(self, user: User) -> Dict[str, str]:
        """
        Get authorization headers for a user.
        
        Args:
            user: User object
        
        Returns:
            Dict with Authorization header
        """
        token = create_access_token(data={"sub": user.id})
        return {"Authorization": f"Bearer {token}"}
    
    def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user info using token.
        
        Args:
            token: Access token
        
        Returns:
            User data
        """
        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        return response.json()
    
    def create_authenticated_client(
        self,
        user: Optional[User] = None
    ) -> TestClient:
        """
        Create a test client with authentication.
        
        Args:
            user: User to authenticate as (creates new if None)
        
        Returns:
            Authenticated TestClient
        """
        if user is None:
            user = self.create_user()
        
        headers = self.get_auth_headers(user)
        self.client.headers.update(headers)
        
        return self.client