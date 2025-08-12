"""
Test helper functions for common testing operations.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import json
import io
from datetime import datetime, timedelta
import jwt
from fastapi import status
from fastapi.testclient import TestClient
import hashlib


def create_test_file(
    filename: str = "test.txt",
    content: Union[str, bytes] = "Test content",
    size_kb: Optional[int] = None
) -> io.BytesIO:
    """
    Create a test file for upload testing.
    
    Args:
        filename: Name of the file
        content: File content (str or bytes)
        size_kb: If specified, create file of this size in KB
    
    Returns:
        BytesIO object ready for upload
    """
    if size_kb:
        # Create file of specific size
        content = b"x" * (size_kb * 1024)
    elif isinstance(content, str):
        content = content.encode()
    
    file_obj = io.BytesIO(content)
    file_obj.name = filename
    return file_obj


def assert_response_ok(
    response,
    expected_status: int = status.HTTP_200_OK,
    check_json: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Assert that response is successful and optionally return JSON data.
    
    Args:
        response: The response object
        expected_status: Expected HTTP status code
        check_json: Whether to parse and return JSON
    
    Returns:
        Parsed JSON data if check_json is True
    """
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    
    if check_json:
        try:
            return response.json()
        except json.JSONDecodeError:
            raise AssertionError(f"Response is not valid JSON: {response.text}")
    
    return None


def assert_response_error(
    response,
    expected_status: int,
    expected_detail: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assert that response is an error with expected status and detail.
    
    Args:
        response: The response object
        expected_status: Expected HTTP error status code
        expected_detail: Expected error detail message (substring match)
    
    Returns:
        Error response data
    """
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    
    data = response.json()
    assert "detail" in data, f"No 'detail' in error response: {data}"
    
    if expected_detail:
        assert expected_detail in data["detail"], f"Expected '{expected_detail}' in '{data['detail']}'"
    
    return data


def compare_dict_subset(
    actual: Dict[str, Any],
    expected: Dict[str, Any],
    ignore_keys: Optional[list] = None
) -> bool:
    """
    Compare if expected dict is a subset of actual dict.
    
    Args:
        actual: The actual dictionary
        expected: The expected dictionary (subset)
        ignore_keys: Keys to ignore in comparison
    
    Returns:
        True if all expected keys/values are in actual
    """
    ignore_keys = ignore_keys or []
    
    for key, value in expected.items():
        if key in ignore_keys:
            continue
        
        assert key in actual, f"Key '{key}' not in actual dict"
        
        if isinstance(value, dict) and isinstance(actual[key], dict):
            assert compare_dict_subset(actual[key], value, ignore_keys)
        else:
            assert actual[key] == value, f"Value mismatch for '{key}': {actual[key]} != {value}"
    
    return True


def generate_test_token(
    user_id: str,
    secret_key: str = "test-secret",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a test JWT token.
    
    Args:
        user_id: User ID to encode in token
        secret_key: Secret key for signing
        expires_delta: Token expiration time
    
    Returns:
        JWT token string
    """
    payload = {"sub": user_id}
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        payload["exp"] = expire
    
    return jwt.encode(payload, secret_key, algorithm="HS256")


def generate_file_hash(file_content: bytes) -> str:
    """
    Generate SHA256 hash of file content.
    
    Args:
        file_content: File content as bytes
    
    Returns:
        Hex string of SHA256 hash
    """
    return hashlib.sha256(file_content).hexdigest()


def create_multipart_upload(files: Dict[str, tuple], data: Optional[Dict] = None) -> Dict:
    """
    Create multipart form data for file upload testing.
    
    Args:
        files: Dict of field_name -> (filename, file_content, content_type)
        data: Additional form data
    
    Returns:
        Dict suitable for requests/TestClient files parameter
    """
    upload_data = {}
    
    for field_name, (filename, content, content_type) in files.items():
        if isinstance(content, str):
            content = content.encode()
        upload_data[field_name] = (filename, io.BytesIO(content), content_type)
    
    if data:
        for key, value in data.items():
            upload_data[key] = (None, str(value))
    
    return upload_data


def paginate_results(
    items: list,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    Simulate pagination of results.
    
    Args:
        items: List of all items
        page: Current page number (1-indexed)
        page_size: Items per page
    
    Returns:
        Paginated response dict
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def mock_async_task_result(task_id: str, status: str = "SUCCESS", result: Any = None) -> Dict:
    """
    Create mock Celery task result.
    
    Args:
        task_id: Task ID
        status: Task status (PENDING, STARTED, SUCCESS, FAILURE)
        result: Task result data
    
    Returns:
        Mock task result dict
    """
    return {
        "task_id": task_id,
        "status": status,
        "result": result,
        "traceback": None if status != "FAILURE" else "Mock error traceback",
        "date_done": datetime.utcnow().isoformat() if status in ["SUCCESS", "FAILURE"] else None,
    }


def assert_datetime_recent(
    datetime_str: str,
    max_seconds_ago: int = 60
) -> bool:
    """
    Assert that a datetime string represents a recent time.
    
    Args:
        datetime_str: ISO format datetime string
        max_seconds_ago: Maximum seconds in the past
    
    Returns:
        True if datetime is recent
    """
    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    now = datetime.utcnow()
    diff = now - dt.replace(tzinfo=None)
    
    assert diff.total_seconds() <= max_seconds_ago, f"Datetime {datetime_str} is not recent (diff: {diff.total_seconds()}s)"
    return True


def clean_test_data(db_session, *models):
    """
    Clean test data from database.
    
    Args:
        db_session: Database session
        *models: Model classes to clean
    """
    for model in models:
        db_session.query(model).delete()
    db_session.commit()


class APITestCase:
    """Base class for API testing with common assertions."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def get(self, url: str, **kwargs) -> Any:
        """GET request with automatic assertion."""
        response = self.client.get(url, **kwargs)
        return assert_response_ok(response)
    
    def post(self, url: str, expected_status: int = 200, **kwargs) -> Any:
        """POST request with automatic assertion."""
        response = self.client.post(url, **kwargs)
        return assert_response_ok(response, expected_status)
    
    def put(self, url: str, expected_status: int = 200, **kwargs) -> Any:
        """PUT request with automatic assertion."""
        response = self.client.put(url, **kwargs)
        return assert_response_ok(response, expected_status)
    
    def delete(self, url: str, expected_status: int = 200, **kwargs) -> Any:
        """DELETE request with automatic assertion."""
        response = self.client.delete(url, **kwargs)
        return assert_response_ok(response, expected_status)
    
    def assert_unauthorized(self, method: str, url: str, **kwargs):
        """Assert that request returns 401 Unauthorized."""
        response = getattr(self.client, method.lower())(url, **kwargs)
        assert_response_error(response, status.HTTP_401_UNAUTHORIZED)
    
    def assert_forbidden(self, method: str, url: str, **kwargs):
        """Assert that request returns 403 Forbidden."""
        response = getattr(self.client, method.lower())(url, **kwargs)
        assert_response_error(response, status.HTTP_403_FORBIDDEN)
    
    def assert_not_found(self, method: str, url: str, **kwargs):
        """Assert that request returns 404 Not Found."""
        response = getattr(self.client, method.lower())(url, **kwargs)
        assert_response_error(response, status.HTTP_404_NOT_FOUND)