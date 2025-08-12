import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid
from typing import Any, Dict, Optional

from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType
from app.core.security import hash_password

class BaseFactory(factory.Factory):
    class Meta:
        abstract = True
    
    @classmethod
    def create_batch(cls, size: int, **kwargs) -> list:
        return [cls.create(**kwargs) for _ in range(size)]
    
class UserFactory(BaseFactory):
    class Meta:
        model = User
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    username = factory.Sequence(lambda n: f"testuser{n}")
    hashed_password = factory.LazyFunction(lambda: hash_password("TestPass123!"))
    is_active = True
    is_superuser = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = None

    @classmethod
    def create_with_password(cls, password: str, **kwargs) -> User:
        kwargs['hashed_password'] = hash_password(password)
        return cls.create(**kwargs)

    @classmethod
    def create_admin(cls, **kwargs) -> User:
        kwargs['is_superuser'] = True
        return cls.create(**kwargs)

    @classmethod
    def create_inactive(cls, **kwargs) -> User:
        kwargs['is_active'] = False
        return cls.create(**kwargs)

class DocumentFactory(BaseFactory):
    class Meta:
        model = Document

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    filename = factory.Sequence(lambda n: f"document_{n}_{uuid.uuid4().hex[:8]}.pdf")
    original_filename = factory.Sequence(lambda n: f"Document {n}.pdf")
    file_path = factory.LazyAttribute(lambda obj: f"uploads/pdf/{obj.filename}")
    file_size = fuzzy.FuzzyInteger(1024, 1024 * 1024 * 5)  # 1KB to 5MB
    file_type = DocumentType.PDF
    mime_type = "application/pdf"
    status = DocumentStatus.PENDING
    error_message = None
    page_count = fuzzy.FuzzyInteger(1, 100)
    word_count = fuzzy.FuzzyInteger(100, 10000)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = None
    processed_at = None

    @classmethod
    def create_processed(cls, **kwargs) -> Document:
        """Create a processed document."""
        kwargs['status'] = DocumentStatus.COMPLETED
        kwargs['processed_at'] = datetime.utcnow()
        return cls.create(**kwargs)
    
    @classmethod
    def create_failed(cls, error_message: str = "Processing failed", **kwargs) -> Document:
        """Create a failed document."""
        kwargs['status'] = DocumentStatus.FAILED
        kwargs['error_message'] = error_message
        return cls.create(**kwargs)

    @classmethod
    def create_with_type(cls, file_type: str, **kwargs) -> Document:
        """Create document with specific file type."""
        type_map = {
            'pdf': (DocumentType.PDF, 'application/pdf', '.pdf'),
            'txt': (DocumentType.TXT, 'text/plain', '.txt'),
            'docx': (DocumentType.DOCX, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
            'pptx': (DocumentType.PPTX, 'application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'),
        }
        
        if file_type in type_map:
            doc_type, mime_type, extension = type_map[file_type]
            kwargs['file_type'] = doc_type
            kwargs['mime_type'] = mime_type
            kwargs['filename'] = f"document_{uuid.uuid4().hex[:8]}{extension}"
            kwargs['original_filename'] = f"Document{extension}"
            kwargs['file_path'] = f"uploads/{file_type}/{kwargs['filename']}"
        
        return cls.create(**kwargs)

class AgentFactory(BaseFactory):
    
    class Meta:
        model = None
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f"Test Agent {n}")
    description = factory.Faker('text', max_nb_chars=200)
    created_at = factory.LazyFunction(datetime.utcnow)

class ChunkFactory(BaseFactory):
    """Factory for creating test chunks (for future use)."""
    
    class Meta:
        model = None
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    document_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    content = factory.Faker('text', max_nb_chars=500)
    embedding = factory.LazyFunction(lambda: [0.1] * 1536)  # OpenAI embedding dimension
    metadata = factory.Dict({
        'page': fuzzy.FuzzyInteger(1, 10),
        'position': fuzzy.FuzzyInteger(0, 1000),
    })
    
    # Add more fields as the Chunk model is developed

class TestDataGenerator:
    """Generate complex test scenarios."""
    
    @staticmethod
    def create_user_with_documents(
        num_documents: int = 5,
        user_kwargs: Optional[Dict[str, Any]] = None,
        document_kwargs: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Create a user with multiple documents."""
        user = UserFactory.create(**(user_kwargs or {}))
        
        doc_kwargs = document_kwargs or {}
        doc_kwargs['user_id'] = user.id
        
        documents = DocumentFactory.create_batch(num_documents, **doc_kwargs)
        
        return user, documents

    @staticmethod
    def create_multiple_users_with_documents(
        num_users: int = 3,
        docs_per_user: int = 5
    ) -> list:
        """Create multiple users, each with documents."""
        result = []
        
        for _ in range(num_users):
            user, docs = TestDataGenerator.create_user_with_documents(docs_per_user)
            result.append((user, docs))
        
        return result

    @staticmethod
    def create_document_processing_pipeline_data():
        """Create data for testing document processing pipeline."""
        user = UserFactory.create()
        
        # Create documents in various states
        pending_doc = DocumentFactory.create(user_id=user.id, status=DocumentStatus.PENDING)
        processing_doc = DocumentFactory.create(user_id=user.id, status=DocumentStatus.PROCESSING)
        completed_doc = DocumentFactory.create_processed(user_id=user.id)
        failed_doc = DocumentFactory.create_failed(user_id=user.id)
        
        return {
            'user': user,
            'pending': pending_doc,
            'processing': processing_doc,
            'completed': completed_doc,
            'failed': failed_doc,
        }