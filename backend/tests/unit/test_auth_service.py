"""
Unit tests for authentication service.
"""
import pytest
from datetime import timedelta
from unittest.mock import Mock, patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from tests.utils.factories import UserFactory


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing works."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_decode_access_token_valid(self):
        """Test decoding a valid token."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_decode_access_token_expired(self):
        """Test decoding an expired token."""
        user_id = "test-user-123"
        # Create token that expires immediately
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-1)
        )
        
        payload = decode_access_token(token)
        
        assert payload is None
    
    def test_decode_access_token_invalid(self):
        """Test decoding an invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = decode_access_token(invalid_token)
        
        assert payload is None
    
    def test_token_with_additional_claims(self):
        """Test token with additional claims."""
        data = {
            "sub": "user-123",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        
        token = create_access_token(data=data)
        payload = decode_access_token(token)
        
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()
    
    def test_user_registration_flow(self, mock_db_session):
        """Test user registration process."""
        from app.schemas.user import UserCreate
        
        user_data = UserCreate(
            email="newuser@test.com",
            username="newuser",
            password="SecurePass123!"
        )
        
        # Simulate registration
        hashed_pw = hash_password(user_data.password)
        
        assert hashed_pw != user_data.password
        assert verify_password(user_data.password, hashed_pw)
    
    def test_user_login_flow(self, mock_db_session):
        """Test user login process."""
        # Create test user
        user = UserFactory.create()
        password = "TestPassword123!"
        user.hashed_password = hash_password(password)
        
        # Simulate login
        assert verify_password(password, user.hashed_password)
        
        # Create token
        token = create_access_token(data={"sub": user.id})
        assert token is not None
        
        # Verify token
        payload = decode_access_token(token)
        assert payload["sub"] == user.id
    
    @patch('app.core.security.settings')
    def test_token_with_custom_expiration(self, mock_settings):
        """Test token with custom expiration time."""
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        
        user_id = "test-user"
        token = create_access_token(data={"sub": user_id})
        
        payload = decode_access_token(token)
        assert payload is not None
        
        # Check expiration is set
        import jwt
        from datetime import datetime
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        
        # Should expire in approximately 60 minutes
        time_diff = (exp_time - now).total_seconds()
        assert 3500 < time_diff < 3700  # Allow some variance