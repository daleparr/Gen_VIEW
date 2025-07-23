"""
Performance Test Suite
Load testing, stress testing, and performance benchmarks for GEN-VIEW-KSE
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, AsyncMock
import psutil
import gc


class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_generation_endpoint_response_time(
        self, 
        test_client, 
        sample_generation_request,
        performance_test_config
    ):
        """Test generation endpoint response time under normal load."""
        response_times = []
        max_response_time = performance_test_config["max_response_time"]
        
        # Warm up
        test_client.post("/api/v1/generate/capsule", json=sample_generation_request)
        
        # Measure response times
        for _ in range(10):
            start_time = time.time()
            response = test_client.post(
                "/api/v1/generate/capsule",
                json=sample_generation_request
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Verify response is successful
            assert response.status_code in [200, 422, 500]  # Allow validation errors
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        # Performance assertions
        assert avg_response_time < max_response_time, f"Average response time {avg_response_time:.3f}s exceeds limit {max_response_time}s"
        assert p95_response_time < max_response_time * 1.5, f"95th percentile {p95_response_time:.3f}s too high"
        
        print(f"Average response time: {avg_response_time:.3f}s")
        print(f"Median response time: {median_response_time:.3f}s")
        print(f"95th percentile: {p95_response_time:.3f}s")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_generation_requests(
        self, 
        test_client, 
        sample_generation_request,
        performance_test_config
    ):
        """Test API performance under concurrent load."""
        concurrent_requests = performance_test_config["concurrent_requests"]
        request_timeout = performance_test_config["request_timeout"]
        
        async def make_request():
            start_time = time.time()
            try:
                response = test_client.post(
                    "/api/v1/generate/capsule",
                    json=sample_generation_request,
                    timeout=request_timeout
                )
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code in [200, 422]
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "status_code": 500,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r["success"]]
        failed_requests = [r for r in results if isinstance(r, dict) and not r["success"]]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = statistics.mean([r["response_time"] for r in successful_requests]) if successful_requests else 0
        throughput = len(successful_requests) / total_time
        
        # Performance assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        assert throughput >= performance_test_config["min_throughput"] / 10, f"Throughput {throughput:.1f} req/s too low"
        
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Average response time: {avg_response_time:.3f}s")
        print(f"Throughput: {throughput:.1f} requests/second")
        print(f"Failed requests: {len(failed_requests)}")
    
    @pytest.mark.performance
    def test_memory_insights_endpoint_performance(
        self, 
        test_client, 
        sample_brand_data,
        mock_kse_memory_service
    ):
        """Test memory insights endpoint performance."""
        brand_id = sample_brand_data["id"]
        response_times = []
        
        # Measure multiple requests
        for _ in range(20):
            start_time = time.time()
            with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
                response = test_client.get(f"/api/v1/generate/memory-insights/{brand_id}")
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            assert response.status_code == 200
        
        # Performance analysis
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        assert avg_time < 1.0, f"Average response time {avg_time:.3f}s too high for insights endpoint"
        assert max_time < 2.0, f"Maximum response time {max_time:.3f}s too high"
        
        print(f"Memory insights average response time: {avg_time:.3f}s")
        print(f"Memory insights max response time: {max_time:.3f}s")


class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_brand_query_performance(self, test_db_session):
        """Test brand query performance with large dataset."""
        from services.generation_api.src.models.fashion_models import Brand
        from sqlalchemy import select
        
        # Create test brands
        brands = []
        for i in range(100):
            brand = Brand(
                name=f"Performance Test Brand {i}",
                description=f"Brand {i} for performance testing",
                market_segment="luxury" if i % 3 == 0 else "mid-market",
                design_dna={
                    "aesthetic": "minimalist" if i % 2 == 0 else "contemporary",
                    "color_preferences": ["black", "white"] if i % 2 == 0 else ["blue", "red"]
                }
            )
            brands.append(brand)
            test_db_session.add(brand)
        
        await test_db_session.commit()
        
        # Test query performance
        query_times = []
        
        for _ in range(10):
            start_time = time.time()
            
            # Complex query with filtering and JSON operations
            stmt = select(Brand).where(
                Brand.market_segment == "luxury"
            ).where(
                Brand.design_dna["aesthetic"].astext == "minimalist"
            ).limit(20)
            
            result = await test_db_session.execute(stmt)
            brands_result = result.scalars().all()
            
            end_time = time.time()
            query_times.append(end_time - start_time)
            
            assert len(brands_result) > 0
        
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        assert avg_query_time < 0.1, f"Average query time {avg_query_time:.3f}s too high"
        assert max_query_time < 0.2, f"Maximum query time {max_query_time:.3f}s too high"
        
        print(f"Brand query average time: {avg_query_time:.4f}s")
        print(f"Brand query max time: {max_query_time:.4f}s")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_generation_job_bulk_operations(self, test_db_session):
        """Test bulk database operations performance."""
        from services.generation_api.src.models.generation_models import GenerationJob, GenerationType, GenerationStatus
        from services.generation_api.src.models.fashion_models import Brand
        
        # Create test brand
        brand = Brand(name="Bulk Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        # Test bulk insert performance
        start_time = time.time()
        
        jobs = []
        for i in range(1000):
            job = GenerationJob(
                name=f"Bulk Job {i}",
                generation_type=GenerationType.CAPSULE_COLLECTION,
                brand_id=brand.id,
                input_parameters={"test_index": i},
                status=GenerationStatus.COMPLETED if i % 2 == 0 else GenerationStatus.QUEUED,
                num_outputs=5,
                quality_level="high"
            )
            jobs.append(job)
            test_db_session.add(job)
        
        await test_db_session.commit()
        bulk_insert_time = time.time() - start_time
        
        # Test bulk query performance
        start_time = time.time()
        from sqlalchemy import select, func
        
        stmt = select(
            func.count(GenerationJob.id),
            func.avg(GenerationJob.num_outputs)
        ).where(GenerationJob.brand_id == brand.id)
        
        result = await test_db_session.execute(stmt)
        stats = result.first()
        bulk_query_time = time.time() - start_time
        
        # Performance assertions
        assert bulk_insert_time < 5.0, f"Bulk insert time {bulk_insert_time:.2f}s too high"
        assert bulk_query_time < 0.5, f"Bulk query time {bulk_query_time:.3f}s too high"
        assert stats[0] == 1000  # Verify all records inserted
        
        print(f"Bulk insert (1000 records): {bulk_insert_time:.2f}s")
        print(f"Bulk query time: {bulk_query_time:.3f}s")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, test_db_session):
        """Test database performance under concurrent access."""
        from services.generation_api.src.models.fashion_models import Brand, Collection
        
        # Create test brand
        brand = Brand(name="Concurrent Test Brand", market_segment="luxury")
        test_db_session.add(brand)
        await test_db_session.flush()
        
        async def create_collection(index):
            start_time = time.time()
            collection = Collection(
                name=f"Concurrent Collection {index}",
                brand_id=brand.id,
                season="spring",
                year=2024,
                target_pieces=5
            )
            test_db_session.add(collection)
            await test_db_session.flush()
            return time.time() - start_time
        
        # Execute concurrent operations
        start_time = time.time()
        tasks = [create_collection(i) for i in range(50)]
        operation_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        await test_db_session.commit()
        
        # Performance analysis
        avg_operation_time = statistics.mean(operation_times)
        max_operation_time = max(operation_times)
        throughput = len(tasks) / total_time
        
        assert avg_operation_time < 0.1, f"Average operation time {avg_operation_time:.3f}s too high"
        assert throughput > 100, f"Database throughput {throughput:.1f} ops/s too low"
        
        print(f"Concurrent DB operations: {len(tasks)}")
        print(f"Average operation time: {avg_operation_time:.4f}s")
        print(f"Database throughput: {throughput:.1f} operations/second")


class TestMemoryPerformance:
    """Memory usage and performance tests."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_kse_memory_service_performance(
        self, 
        mock_kse_memory_service,
        sample_multimodal_inputs,
        performance_test_config
    ):
        """Test KSE Memory Service performance under load."""
        memory_limit = performance_test_config["memory_limit"]  # MB
        
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate high-volume memory operations
        operation_times = []
        
        for i in range(100):
            generation_id = f"perf_test_gen_{i}"
            mock_outputs = {"outputs": [{"id": f"output_{i}", "quality": 0.8}]}
            
            start_time = time.time()
            
            # Store generation context
            await mock_kse_memory_service.store_generation_context(
                generation_id,
                sample_multimodal_inputs,
                mock_outputs
            )
            
            # Retrieve relevant context
            await mock_kse_memory_service.retrieve_relevant_context(
                sample_multimodal_inputs.metadata,
                brand_id="test_brand",
                depth=5
            )
            
            operation_time = time.time() - start_time
            operation_times.append(operation_time)
            
            # Check memory usage periodically
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                
                if memory_increase > memory_limit:
                    pytest.fail(f"Memory usage increased by {memory_increase:.1f}MB, exceeding limit of {memory_limit}MB")
        
        # Performance analysis
        avg_operation_time = statistics.mean(operation_times)
        p95_operation_time = sorted(operation_times)[int(0.95 * len(operation_times))]
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        
        # Performance assertions
        assert avg_operation_time < 0.05, f"Average KSE operation time {avg_operation_time:.3f}s too high"
        assert p95_operation_time < 0.1, f"95th percentile operation time {p95_operation_time:.3f}s too high"
        assert total_memory_increase < memory_limit, f"Total memory increase {total_memory_increase:.1f}MB exceeds limit"
        
        print(f"KSE Memory Service - 100 operations:")
        print(f"Average operation time: {avg_operation_time:.4f}s")
        print(f"95th percentile time: {p95_operation_time:.4f}s")
        print(f"Memory increase: {total_memory_increase:.1f}MB")
    
    @pytest.mark.performance
    def test_memory_leak_detection(self, mock_kse_memory_service):
        """Test for memory leaks in long-running operations."""
        process = psutil.Process()
        
        # Baseline memory measurement
        gc.collect()  # Force garbage collection
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        # Simulate long-running operations
        for cycle in range(5):
            # Perform operations that might cause memory leaks
            for i in range(200):
                generation_id = f"leak_test_{cycle}_{i}"
                
                # Create and store data
                mock_kse_memory_service.memory_store[generation_id] = {
                    "inputs": {"test_data": "x" * 1000},  # Create some data
                    "outputs": {"test_outputs": list(range(100))},
                    "stored_at": "2024-01-15T10:30:00Z"
                }
            
            # Clear data (simulating cleanup)
            mock_kse_memory_service.memory_store.clear()
            
            # Force garbage collection and measure memory
            gc.collect()
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - baseline_memory
            
            print(f"Cycle {cycle + 1}: Memory increase = {memory_increase:.1f}MB")
            
            # Check for excessive memory growth
            max_acceptable_increase = 50  # MB
            assert memory_increase < max_acceptable_increase, f"Potential memory leak detected: {memory_increase:.1f}MB increase"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multimodal_processor_memory_usage(self, mock_multimodal_processor):
        """Test memory usage of multimodal processing operations."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Process multiple inputs to test memory usage
        memory_measurements = []
        
        for i in range(50):
            # Create test inputs
            text_prompt = f"test prompt {i} with additional content to simulate real usage"
            image_url = f"https://example.com/test_image_{i}.jpg"
            color_palette = ["red", "blue", "green", "yellow", "purple"]
            
            # Process inputs
            await mock_multimodal_processor.encode_text(text_prompt)
            await mock_multimodal_processor.encode_image(image_url)
            await mock_multimodal_processor.encode_colors(color_palette)
            
            # Measure memory every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(current_memory - initial_memory)
        
        # Analyze memory growth
        memory_growth = memory_measurements[-1] - memory_measurements[0] if len(memory_measurements) > 1 else 0
        max_memory_increase = max(memory_measurements)
        
        # Memory usage assertions
        assert max_memory_increase < 100, f"Maximum memory increase {max_memory_increase:.1f}MB too high"
        assert memory_growth < 50, f"Memory growth {memory_growth:.1f}MB indicates potential leak"
        
        print(f"Multimodal processor memory usage:")
        print(f"Maximum increase: {max_memory_increase:.1f}MB")
        print(f"Total growth: {memory_growth:.1f}MB")


class TestWebSocketPerformance:
    """WebSocket connection and messaging performance tests."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self, mock_websocket):
        """Test WebSocket message throughput."""
        message_count = 1000
        message_size = 1024  # bytes
        
        # Create test message
        test_message = {
            "type": "status_update",
            "taskId": "perf-test-task",
            "status": "running",
            "progress": 0.5,
            "data": "x" * (message_size - 200)  # Adjust for JSON overhead
        }
        
        # Measure message sending performance
        start_time = time.time()
        
        for i in range(message_count):
            test_message["sequence"] = i
            await mock_websocket.send_json(test_message)
        
        total_time = time.time() - start_time
        
        # Calculate throughput
        messages_per_second = message_count / total_time
        bytes_per_second = (message_count * message_size) / total_time
        
        # Performance assertions
        min_throughput = 500  # messages per second
        assert messages_per_second > min_throughput, f"Message throughput {messages_per_second:.1f} msg/s below {min_throughput}"
        
        print(f"WebSocket Performance:")
        print(f"Messages sent: {message_count}")
        print(f"Message size: {message_size} bytes")
        print(f"Throughput: {messages_per_second:.1f} messages/second")
        print(f"Bandwidth: {bytes_per_second / 1024:.1f} KB/second")
        
        # Verify all messages were sent
        assert len(mock_websocket.messages) == message_count
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self, async_test_utils):
        """Test performance with multiple concurrent WebSocket connections."""
        connection_count = 50
        messages_per_connection = 20
        
        class MockWebSocketConnection:
            def __init__(self, connection_id):
                self.connection_id = connection_id
                self.messages = []
                self.connected = False
            
            async def connect(self):
                await async_test_utils.simulate_delay(0.01)  # Connection delay
                self.connected = True
            
            async def send_message(self, message):
                if not self.connected:
                    raise Exception("Not connected")
                await async_test_utils.simulate_delay(0.001)  # Message delay
                self.messages.append(message)
            
            async def disconnect(self):
                self.connected = False
        
        # Create connections
        connections = [MockWebSocketConnection(i) for i in range(connection_count)]
        
        # Test concurrent connection establishment
        start_time = time.time()
        await asyncio.gather(*[conn.connect() for conn in connections])
        connection_time = time.time() - start_time
        
        # Test concurrent message sending
        async def send_messages_to_connection(conn):
            for i in range(messages_per_connection):
                message = {
                    "type": "test_message",
                    "connection_id": conn.connection_id,
                    "message_index": i
                }
                await conn.send_message(message)
        
        start_time = time.time()
        await asyncio.gather(*[send_messages_to_connection(conn) for conn in connections])
        messaging_time = time.time() - start_time
        
        # Performance analysis
        total_messages = connection_count * messages_per_connection
        message_throughput = total_messages / messaging_time
        connection_throughput = connection_count / connection_time
        
        # Performance assertions
        assert connection_throughput > 100, f"Connection throughput {connection_throughput:.1f} conn/s too low"
        assert message_throughput > 1000, f"Message throughput {message_throughput:.1f} msg/s too low"
        
        print(f"Concurrent WebSocket Performance:")
        print(f"Connections: {connection_count}")
        print(f"Messages per connection: {messages_per_connection}")
        print(f"Connection throughput: {connection_throughput:.1f} connections/second")
        print(f"Message throughput: {message_throughput:.1f} messages/second")
        
        # Verify all messages were sent
        total_sent_messages = sum(len(conn.messages) for conn in connections)
        assert total_sent_messages == total_messages
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_reconnect_performance(self, async_test_utils):
        """Test WebSocket reconnection performance and reliability."""
        max_reconnect_attempts = 5
        base_delay = 0.1  # seconds
        backoff_multiplier = 2
        
        class MockReconnectingWebSocket:
            def __init__(self):
                self.connected = False
                self.reconnect_attempts = 0
                self.connection_history = []
            
            async def connect(self):
                # Simulate connection failure for first few attempts
                if self.reconnect_attempts < 3:
                    self.reconnect_attempts += 1
                    self.connection_history.append({"attempt": self.reconnect_attempts, "success": False})
                    raise Exception(f"Connection failed (attempt {self.reconnect_attempts})")
                
                self.connected = True
                self.connection_history.append({"attempt": self.reconnect_attempts + 1, "success": True})
            
            async def reconnect_with_backoff(self):
                for attempt in range(max_reconnect_attempts):
                    try:
                        await self.connect()
                        return True
                    except Exception:
                        if attempt < max_reconnect_attempts - 1:
                            delay = min(base_delay * (backoff_multiplier ** attempt), 2.0)
                            await async_test_utils.simulate_delay(delay)
                return False
        
        # Test reconnection performance
        websocket = MockReconnectingWebSocket()
        
        start_time = time.time()
        success = await websocket.reconnect_with_backoff()
        reconnect_time = time.time() - start_time
        
        # Performance assertions
        assert success, "WebSocket should eventually reconnect"
        assert reconnect_time < 5.0, f"Reconnection time {reconnect_time:.2f}s too high"
        assert websocket.connected, "WebSocket should be connected after successful reconnection"
        
        # Analyze reconnection pattern
        failed_attempts = [h for h in websocket.connection_history if not h["success"]]
        successful_attempts = [h for h in websocket.connection_history if h["success"]]
        
        assert len(failed_attempts) == 3, "Should have exactly 3 failed attempts"
        assert len(successful_attempts) == 1, "Should have exactly 1 successful attempt"
        
        print(f"WebSocket Reconnection Performance:")
        print(f"Total reconnection time: {reconnect_time:.2f}s")
        print(f"Failed attempts: {len(failed_attempts)}")
        print(f"Successful attempts: {len(successful_attempts)}")


class TestSystemResourceUsage:
    """System resource usage and limits testing."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cpu_usage_under_load(
        self, 
        test_client, 
        sample_generation_request,
        performance_test_config
    ):
        """Test CPU usage during high load scenarios."""
        cpu_limit = performance_test_config["cpu_limit"]  # percentage
        
        # Monitor CPU usage
        process = psutil.Process()
        cpu_measurements = []
        
        async def cpu_monitor():
            for _ in range(20):  # Monitor for 2 seconds
                cpu_percent = process.cpu_percent()
                cpu_measurements.append(cpu_percent)
                await asyncio.sleep(0.1)
        
        async def generate_load():
            # Generate load with concurrent requests
            tasks = []
            for _ in range(20):
                task = asyncio.create_task(
                    asyncio.to_thread(
                        test_client.post,
                        "/api/v1/generate/capsule",
                        json=sample_generation_request
                    )
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Run load generation and monitoring concurrently
        await asyncio.gather(
            cpu_monitor(),
            generate_load()
        )
        
        # Analyze CPU usage
        avg_cpu = statistics.mean(cpu_measurements) if cpu_measurements else 0
        max_cpu = max(cpu_measurements) if cpu_measurements else 0
        
        # CPU usage assertions
        assert max_cpu < cpu_limit, f"Maximum CPU usage {max_cpu:.1f}% exceeds limit {cpu_limit}%"
        
        print(f"CPU Usage Analysis:")
        print(f"Average CPU: {avg_cpu:.1f}%")
        print(f"Maximum CPU: {max_cpu:.1f}%")
        print(f"CPU measurements: {len(cpu_measurements)}")
    
    @pytest.mark.performance
    def test_file_descriptor_usage(self):
        """Test file descriptor usage and limits."""
        import resource
        
        # Get current file descriptor usage
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        process = psutil.Process()
        current_fd_count = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        print(f"File Descriptor Usage:")
        print(f"Current FDs: {current_fd_count}")
        print(f"Soft limit: {soft_limit}")
        print(f"Hard limit: {hard_limit}")
        
        # Ensure we're not approaching limits
        fd_usage_percentage = (current_fd_count / soft_limit) * 100 if soft_limit > 0 else 0
        
        assert fd_usage_percentage < 80, f"File descriptor usage {fd_usage_percentage:.1f}% too high"
        assert current_fd_count < soft_limit * 0.8, "Approaching file descriptor limit"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, test_db_session):
        """Test database connection pool performance and limits."""
        from sqlalchemy import text
        
        # Test connection pool under load
        connection_times = []
        query_times = []
        
        async def execute_query(query_id):
            start_time = time.time()
            
            # Simple query to test connection performance
            result = await test_db_session.execute(text("SELECT 1 as test_value"))
            connection_time = time.time() - start_time
            
            # Execute a more complex query
            query_start = time.time()
            result = await test_db_session.execute(
                text("SELECT COUNT(*) FROM information_schema.tables")
            )
            query_time = time.time() - query_start
            
            return connection_time, query_time
        
        # Execute concurrent database operations
        tasks = [execute_query(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        connection_times = [r[0] for r in results]
        query_times = [r[1] for r in results]
        
        avg_connection_time = statistics.mean(connection_times)
        avg_query_time = statistics.mean(query_times)
        max_connection_time = max(connection_times)
        
        # Performance assertions
        assert avg_connection_time < 0.1, f"Average connection time {avg_connection_time:.3f}s too high"
        assert max_connection_time < 0.5, f"Maximum connection time {max_connection_time:.3f}s too high"
        assert avg_query_time < 0.05, f"Average query time {avg_query_time:.3f}s too high"
        
        print(f"Database Connection Pool Performance:")
        print(f"Concurrent operations: {len(tasks)}")
        print(f"Average connection time: {avg_connection_time:.4f}s")
        print(f"Average query time: {avg_query_time:.4f}s")
        print(f"Maximum connection time: {max_connection_time:.4f}s")


@pytest.mark.performance
class TestEndToEndPerformance:
    """End-to-end performance testing scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_generation_workflow_performance(
        self, 
        test_client, 
        sample_brand_data,
        sample_generation_request,
        mock_kse_memory_service,
        async_test_utils
    ):
        """Test complete generation workflow performance."""
        workflow_start = time.time()
        
        # Step 1: Create brand
        brand_start = time.time()
        brand_response = test_client.post("/api/v1/brands", json=sample_brand_data)
        brand_time = time.time() - brand_start
        
        assert brand_response.status_code == 201
        brand_id = brand_response.json()["id"]
        
        # Step 2: Start generation
        generation_start = time.time()
        generation_request = sample_generation_request.copy()
        generation_request["brandParameters"]["brandId"] = brand_id
        
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            gen_response = test_client.post(
                "/api/v1/generate/capsule",
                json=generation_request
            )
        generation_time = time.time() - generation_start
        
        assert gen_response.status_code == 200
        task_id = gen_response.json()["taskId"]
        
        # Step 3: Get memory insights
        insights_start = time.time()
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            insights_response = test_client.get(f"/api/v1/generate/memory-insights/{brand_id}")
        insights_time = time.time() - insights_start
        
        assert insights_response.status_code == 200
        
        # Step 4: Submit feedback
        feedback_start = time.time()
        feedback_data = {
            "generation_id": task_id,
            "user_ratings": {"overall_rating": 4.5}
        }
        
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            feedback_response = test_client.post(
                "/api/v1/generate/feedback",
                json=feedback_data
            )
        feedback_time = time.time() - feedback_start
        
        assert feedback_response.status_code == 200
        
        # Calculate total workflow time
        total_workflow_time = time.time() - workflow_start
        
        # Performance assertions
        assert brand_time < 1.0, f"Brand creation time {brand_time:.3f}s too high"
        assert generation_time < 2.0, f"Generation time {generation_time:.3f}s too high"
        assert insights_time < 1.0, f"Insights time {insights_time:.3f}s too high"
        assert feedback_time < 0.5, f"Feedback time {feedback_time:.3f}s too high"
        assert total_workflow_time < 5.0, f"Total workflow time {total_workflow_time:.3f}s too high"
        
        print(f"End-to-End Workflow Performance:")
        print(f"Brand creation: {brand_time:.3f}s")
        print(f"Generation request: {generation_time:.3f}s")
        print(f"Memory insights: {insights_time:.3f}s")
        print(f"Feedback submission: {feedback_time:.3f}s")
        print(f"Total workflow: {total_workflow_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_system_performance_under_realistic_load(
        self, 
        test_client, 
        sample_generation_request,
        performance_test_config
    ):
        """Test system performance under realistic user load."""
        # Simulate realistic user behavior
        concurrent_users = 10
        operations_per_user = 5
        
        async def simulate_user_session(user_id):
            session_times = []
            
            for operation in range(operations_per_user):
                start_time = time.time()
                
                # Vary operations to simulate real usage
                if operation % 3 == 0:
                    # Generation request
                    response = test_client.post(
                        "/api/v1/generate/capsule",
                        json=sample_generation_request
                    )
                elif operation % 3 == 1:
                    # Health check
                    response = test_client.get("/api/v1/health")
                else:
                    # Brand listing
                    response = test_client.get("/api/v1/brands")
                
                operation_time = time.time() - start_time
                session_times.append(operation_time)
                
                # Simulate user think time
                await asyncio.sleep(0.1)
            
            return {
                "user_id": user_id,
                "session_times": session_times,
                "total_session_time": sum(session_times)
            }
        
        # Execute concurrent user sessions
        start_time = time.time()
        user_sessions = await asyncio.gather(*[
            simulate_user_session(i) for i in range(concurrent_users)
        ])
        total_test_time = time.time() - start_time
        
        # Analyze performance
        all_operation_times = []
        for session in user_sessions:
            all_operation_times.extend(session["session_times"])
        
        avg_operation_time = statistics.mean(all_operation_times)
        p95_operation_time = sorted(all_operation_times)[int(0.95 * len(all_operation_times))]
        total_operations = len(all_operation_times)
        system_throughput = total_operations / total_test_time
        
        # Performance assertions
        assert avg_operation_time < 1.0, f"Average operation time {avg_operation_time:.3f}s too high"
        assert p95_operation_time < 3.0, f"95th percentile operation time {p95_operation_time:.3f}s too high"
        assert system_throughput > 10, f"System throughput {system_throughput:.1f} ops/s too low"
        
        print(f"Realistic Load Test Results:")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Operations per user: {operations_per_user}")
        print(f"Total operations: {total_operations}")
        print(f"Average operation time: {avg_operation_time:.3f}s")
        print(f"95th percentile time: {p95_operation_time:.3f}s")
        print(f"System throughput: {system_throughput:.1f} operations/second")
        print(f"Test duration: {total_test_time:.2f}s")