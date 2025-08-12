"""
Performance and load tests.
"""
import pytest
import time
import concurrent.futures
from statistics import mean, median, stdev

from tests.utils.helpers import create_test_file
from tests.utils.factories import UserFactory, DocumentFactory


class TestPerformance:
    """Performance testing for API endpoints."""
    
    @pytest.mark.performance
    def test_auth_endpoint_performance(self, benchmark_client):
        """Test authentication endpoint performance."""
        client = benchmark_client
        
        # Prepare test data
        test_user = {
            "username": "perftest",
            "password": "PerfTest123!"
        }
        
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "email": "perftest@test.com",
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        
        # Measure login performance
        response_times = []
        
        for _ in range(100):
            start = time.time()
            
            response = client.post(
                "/api/auth/login",
                data=test_user
            )
            
            end = time.time()
            response_times.append(end - start)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_time = mean(response_times)
        med_time = median(response_times)
        std_time = stdev(response_times) if len(response_times) > 1 else 0
        
        print(f"\nLogin Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Median: {med_time*1000:.2f}ms")
        print(f"  StdDev: {std_time*1000:.2f}ms")
        
        # Assert performance requirements
        assert avg_time < 0.1  # Average should be under 100ms
        assert med_time < 0.08  # Median should be under 80ms
    
@pytest.mark.performance
    def test_document_list_performance(self, benchmark_client, db_session):
        """Test document list endpoint performance with many documents."""
        client = benchmark_client
        
        # Create test user and get token
        user = UserFactory.create()
        db_session.add(user)
        
        # Create many documents
        documents = DocumentFactory.create_batch(100, user_id=user.id)
        for doc in documents:
            db_session.add(doc)
        db_session.commit()
        
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Measure list performance
        response_times = []
        
        for _ in range(50):
            start = time.time()
            
            response = client.get(
                "/api/documents/?skip=0&limit=10",
                headers=headers
            )
            
            end = time.time()
            response_times.append(end - start)
            
            assert response.status_code == 200
        
        # Calculate statistics
        avg_time = mean(response_times)
        med_time = median(response_times)
        
        print(f"\nDocument List Performance (100 docs):")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Median: {med_time*1000:.2f}ms")
        
        # Assert performance requirements
        assert avg_time < 0.2  # Average should be under 200ms
        assert med_time < 0.15  # Median should be under 150ms
    
    @pytest.mark.performance
    def test_concurrent_requests(self, benchmark_client, db_session):
        """Test handling of concurrent requests."""
        client = benchmark_client
        
        # Create test user
        user = UserFactory.create()
        db_session.add(user)
        db_session.commit()
        
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        def make_request(index: int):
            """Make a single request."""
            start = time.time()
            
            response = client.get(
                "/api/auth/me",
                headers=headers
            )
            
            end = time.time()
            
            return {
                "index": index,
                "time": end - start,
                "status": response.status_code
            }
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful = [r for r in results if r["status"] == 200]
        response_times = [r["time"] for r in successful]
        
        avg_time = mean(response_times)
        max_time = max(response_times)
        
        print(f"\nConcurrent Requests (100 requests, 10 workers):")
        print(f"  Successful: {len(successful)}/100")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  Max: {max_time*1000:.2f}ms")
        
        # Assert all requests succeeded
        assert len(successful) == 100
        # Assert reasonable response times under load
        assert avg_time < 0.5  # Average under 500ms
        assert max_time < 2.0  # Max under 2 seconds
    
    @pytest.mark.performance
    def test_file_upload_performance(self, benchmark_client, mock_file_upload, db_session):
        """Test file upload performance."""
        client = benchmark_client
        
        # Create test user
        user = UserFactory.create()
        db_session.add(user)
        db_session.commit()
        
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test different file sizes
        file_sizes = [
            (1, "1KB"),
            (10, "10KB"),
            (100, "100KB"),
            (1000, "1MB"),
        ]
        
        results = {}
        
        for size_kb, label in file_sizes:
            file = create_test_file(f"test_{label}.txt", size_kb=size_kb)
            
            # Measure upload time
            times = []
            
            for i in range(5):
                file.seek(0)  # Reset file pointer
                
                start = time.time()
                
                response = client.post(
                    "/api/documents/upload",
                    headers=headers,
                    files={"file": (f"test_{label}_{i}.txt", file, "text/plain")}
                )
                
                end = time.time()
                
                if response.status_code == 200:
                    times.append(end - start)
            
            if times:
                results[label] = {
                    "avg": mean(times) * 1000,
                    "max": max(times) * 1000
                }
        
        print(f"\nFile Upload Performance:")
        for label, metrics in results.items():
            print(f"  {label}: avg={metrics['avg']:.2f}ms, max={metrics['max']:.2f}ms")
        
        # Assert reasonable upload times
        if "1KB" in results:
            assert results["1KB"]["avg"] < 100  # 1KB should upload in under 100ms
        if "1MB" in results:
            assert results["1MB"]["avg"] < 1000  # 1MB should upload in under 1 second