TEST_CONFIG = {
    "test_database_url": "postgresql://user:password@localhost/testdb",
    "test_redis_url": "redis://localhost:6379/1",
    "test_upload_dir": "tests_uploads",
    "test_user_password": "TestPassword123!",
    "api_base_url": "http://localhost:8000",
}

from tests.utils.factories import UserFactory, DocumentFactory
from tests.utils.helpers import *

__all__ = [
    "TEST_CONFIG",
    "UserFactory",
    "DocumentFactory",
]