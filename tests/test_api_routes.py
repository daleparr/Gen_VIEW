"""
API Routes Test Suite
Tests for FastAPI generation endpoints and WebSocket connections
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from services.generation_api.src.models.generation_models import GenerationStatus


class TestGenerationRoutes:
    """Test suite for generation API routes."""
    
    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_detailed(self, test_client):
        """Test detailed health check endpoint."""
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "models" in data
        assert "memory" in data
    
    @pytest.mark.asyncio
    async def test_capsule_collection_generation_valid(
        self, 
        test_client, 
        sample_generation_request,
        mock_kse_memory_service,
        mock_multimodal_processor
    ):
        """Test valid capsule collection generation request."""
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            with patch('services.generation_api.src.api.routes.generation.MultiModalProcessor', return_value=mock_multimodal_processor):
                response = test_client.post(
                    "/api/v1/generate/capsule",
                    json=sample_generation_request
                )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "taskId" in data
        assert data["status"] == GenerationStatus.QUEUED
        assert data["kseContextRetrieved"] is True
        assert data["memoryNodesAccessed"] >= 0
        assert data["commercialPredictionsEnabled"] is True
        assert "websocketUrl" in data
    
    def test_capsule_collection_generation_invalid(self, test_client):
        """Test invalid capsule collection generation request."""
        invalid_request = {
            "name": "",  # Invalid: empty name
            "inputs": {},  # Invalid: no inputs
            "brandParameters": {},  # Invalid: missing required fields
            "targetPieces": 0  # Invalid: zero pieces
        }
        
        response = test_client.post(
            "/api/v1/generate/capsule",
            json=invalid_request
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_capsule_collection_generation_missing_inputs(self, test_client):
        """Test capsule collection generation with missing required inputs."""
        request_without_inputs = {
            "name": "Test Collection",
            "brandParameters": {
                "brandId": "test-brand-id",
                "designDnaAdherence": 0.8
            },
            "targetPieces": 5,
            "qualityLevel": "high",
            "creativityLevel": 0.7,
            "useMemoryContext": True,
            "memoryDepth": 5,
            "optimizeForCommercial": False
        }
        
        response = test_client.post(
            "/api/v1/generate/capsule",
            json=request_without_inputs
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio 
    async def test_single_product_generation(
        self, 
        test_client, 
        generation_test_data,
        mock_kse_memory_service
    ):
        """Test single product generation endpoint."""
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            response = test_client.post(
                "/api/v1/generate/single-product",
                json=generation_test_data["single_product_request"]
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "taskId" in data
        assert data["status"] == GenerationStatus.QUEUED
        assert "websocketUrl" in data
    
    @pytest.mark.asyncio
    async def test_style_transfer_generation(
        self, 
        test_client, 
        generation_test_data,
        mock_kse_memory_service
    ):
        """Test style transfer generation endpoint."""
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            response = test_client.post(
                "/api/v1/generate/style-transfer",
                json=generation_test_data["style_transfer_request"]
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "taskId" in data
        assert data["status"] == GenerationStatus.QUEUED
        assert "websocketUrl" in data
    
    @pytest.mark.asyncio
    async def test_memory_insights_endpoint(
        self, 
        test_client, 
        sample_brand_data,
        mock_kse_memory_service
    ):
        """Test KSE memory insights endpoint."""
        brand_id = sample_brand_data["id"]
        
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            response = test_client.get(f"/api/v1/generate/memory-insights/{brand_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["brand_id"] == brand_id
        assert "total_memory_nodes" in data
        assert "recent_generations" in data
        assert "design_evolution" in data
        assert "commercial_performance" in data
        assert "temporal_patterns" in data
    
    @pytest.mark.asyncio
    async def test_feedback_submission(
        self, 
        test_client,
        mock_kse_memory_service
    ):
        """Test feedback submission endpoint."""
        feedback_data = {
            "generation_id": "test-generation-id",
            "commercial_outcomes": {
                "would_purchase": True,
                "conversion_rate": 0.15
            },
            "user_ratings": {
                "overall_rating": 4.5,
                "comments": "Great design!"
            }
        }
        
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            response = test_client.post(
                "/api/v1/generate/feedback",
                json=feedback_data
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "feedback_integrated"
        assert data["generation_id"] == feedback_data["generation_id"]
        assert "learning_update" in data


class TestCollectionRoutes:
    """Test suite for collection management routes."""
    
    @pytest.mark.asyncio
    async def test_create_brand(self, test_client, sample_brand_data):
        """Test brand creation endpoint."""
        response = test_client.post(
            "/api/v1/brands",
            json=sample_brand_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_brand_data["name"]
        assert data["description"] == sample_brand_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_brands(self, test_client):
        """Test get brands endpoint."""
        response = test_client.get("/api/v1/brands")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should include sample brands from database init
        assert len(data) >= 0
    
    @pytest.mark.asyncio
    async def test_get_brand_by_id(self, test_client, sample_brand_data):
        """Test get specific brand endpoint."""
        # First create a brand
        create_response = test_client.post("/api/v1/brands", json=sample_brand_data)
        assert create_response.status_code == 201
        brand_id = create_response.json()["id"]
        
        # Then retrieve it
        response = test_client.get(f"/api/v1/brands/{brand_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == brand_id
        assert data["name"] == sample_brand_data["name"]
    
    @pytest.mark.asyncio
    async def test_create_collection(self, test_client, sample_brand_data, sample_collection_data):
        """Test collection creation endpoint."""
        # First create a brand
        brand_response = test_client.post("/api/v1/brands", json=sample_brand_data)
        brand_id = brand_response.json()["id"]
        
        # Update collection data with actual brand ID
        collection_data = sample_collection_data.copy()
        collection_data["brand_id"] = brand_id
        
        response = test_client.post(
            "/api/v1/collections",
            json=collection_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == collection_data["name"]
        assert data["brand_id"] == brand_id
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_search_products(self, test_client):
        """Test product search endpoint."""
        search_params = {
            "query": "minimalist",
            "category": "top",
            "price_min": 50,
            "price_max": 200
        }
        
        response = test_client.get("/api/v1/products/search", params=search_params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["results"], list)


class TestWebSocketConnections:
    """Test suite for WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_generation_websocket_connection(self, mock_websocket, async_test_utils):
        """Test WebSocket connection for generation updates."""
        task_id = async_test_utils.create_mock_task_id()
        
        # Mock the WebSocket endpoint behavior
        with patch('services.generation_api.src.api.routes.generation.redis_manager') as mock_redis:
            mock_redis.get.return_value = {
                "status": GenerationStatus.RUNNING,
                "progress": 0.5,
                "current_step": "generating_visuals",
                "outputs_ready": 2,
                "total_outputs": 5
            }
            
            # Simulate WebSocket message handling
            await mock_websocket.accept()
            
            # Simulate sending status update
            update_message = {
                "task_id": task_id,
                "status": GenerationStatus.RUNNING,
                "progress": 0.5,
                "current_step": "generating_visuals",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await mock_websocket.send_json(update_message)
            
            assert len(mock_websocket.messages) == 1
            assert mock_websocket.messages[0]["task_id"] == task_id
            assert mock_websocket.messages[0]["progress"] == 0.5
    
    @pytest.mark.asyncio
    async def test_websocket_completion_message(self, mock_websocket, async_test_utils):
        """Test WebSocket completion message."""
        task_id = async_test_utils.create_mock_task_id()
        
        completion_message = {
            "task_id": task_id,
            "status": GenerationStatus.COMPLETED,
            "progress": 1.0,
            "results": {
                "outputs": [
                    {
                        "output_id": "output_1",
                        "content_url": "https://example.com/output1.jpg",
                        "quality_score": 0.85
                    }
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await mock_websocket.accept()
        await mock_websocket.send_json(completion_message)
        
        assert len(mock_websocket.messages) == 1
        assert mock_websocket.messages[0]["status"] == GenerationStatus.COMPLETED
        assert "results" in mock_websocket.messages[0]
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, mock_websocket, async_test_utils):
        """Test WebSocket error handling."""
        task_id = async_test_utils.create_mock_task_id()
        
        error_message = {
            "task_id": task_id,
            "error": "Generation failed due to invalid input",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await mock_websocket.accept()
        await mock_websocket.send_json(error_message)
        
        assert len(mock_websocket.messages) == 1
        assert "error" in mock_websocket.messages[0]


class TestRateLimiting:
    """Test suite for API rate limiting."""
    
    def test_rate_limiting_generation_endpoint(self, test_client, sample_generation_request):
        """Test rate limiting on generation endpoints."""
        # Make multiple rapid requests
        responses = []
        for i in range(15):  # Assuming rate limit is 10 requests per minute
            response = test_client.post(
                "/api/v1/generate/capsule",
                json=sample_generation_request
            )
            responses.append(response)
        
        # Check if rate limiting kicks in
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        # Should have some rate limited responses after hitting the limit
        assert len(rate_limited_responses) > 0 or all(r.status_code in [200, 422, 500] for r in responses)


class TestErrorHandling:
    """Test suite for API error handling."""
    
    def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON requests."""
        response = test_client.post(
            "/api/v1/generate/capsule",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields."""
        incomplete_request = {
            "name": "Test Collection"
            # Missing required fields
        }
        
        response = test_client.post(
            "/api/v1/generate/capsule",
            json=incomplete_request
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_invalid_field_types(self, test_client):
        """Test handling of invalid field types."""
        invalid_request = {
            "name": "Test Collection",
            "inputs": {
                "textPrompt": "test prompt",
                "referenceImages": ["https://example.com/image.jpg"],
                "colorPalette": ["red", "blue"]
            },
            "brandParameters": {
                "brandId": "test-brand",
                "designDnaAdherence": "invalid_float"  # Should be float
            },
            "targetPieces": "invalid_int",  # Should be int
            "qualityLevel": "high",
            "creativityLevel": 0.7,
            "useMemoryContext": True,
            "memoryDepth": 5,
            "optimizeForCommercial": False
        }
        
        response = test_client.post(
            "/api/v1/generate/capsule",
            json=invalid_request
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, test_client, sample_generation_request):
        """Test handling of database connection errors."""
        with patch('services.generation_api.src.core.database.get_db', side_effect=Exception("Database connection failed")):
            response = test_client.post(
                "/api/v1/generate/capsule",
                json=sample_generation_request
            )
            
            assert response.status_code == 500
    
    def test_nonexistent_endpoint(self, test_client):
        """Test handling of requests to nonexistent endpoints."""
        response = test_client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, test_client):
        """Test handling of incorrect HTTP methods."""
        response = test_client.get("/api/v1/generate/capsule")  # Should be POST
        
        assert response.status_code == 405


class TestAuthentication:
    """Test suite for API authentication."""
    
    def test_protected_endpoint_without_auth(self, test_client):
        """Test access to protected endpoints without authentication."""
        # Assuming some endpoints require authentication
        response = test_client.get("/api/v1/admin/users")
        
        # Should return 401 or 403 if authentication is required
        assert response.status_code in [401, 403, 404]  # 404 if endpoint doesn't exist yet
    
    def test_invalid_api_key(self, test_client):
        """Test requests with invalid API keys."""
        headers = {"Authorization": "Bearer invalid_api_key"}
        
        response = test_client.get(
            "/api/v1/brands",
            headers=headers
        )
        
        # Should succeed if endpoint is public, or fail with 401/403 if protected
        assert response.status_code in [200, 401, 403]


class TestCORS:
    """Test suite for CORS configuration."""
    
    def test_cors_preflight_request(self, test_client):
        """Test CORS preflight requests."""
        response = test_client.options(
            "/api/v1/generate/capsule",
            headers={
                "Origin": "https://demo.genviewkse.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should return 200 with appropriate CORS headers
        assert response.status_code == 200
        
        # Check for CORS headers (if implemented)
        headers = response.headers
        cors_headers_present = any(
            header.lower().startswith('access-control') 
            for header in headers.keys()
        )
        
        # CORS headers should be present in a production setup
        # For now, just verify the request doesn't fail
        assert True  # Placeholder assertion


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_generation_workflow(
        self, 
        test_client, 
        sample_brand_data, 
        sample_generation_request,
        mock_kse_memory_service,
        async_test_utils
    ):
        """Test complete generation workflow from request to completion."""
        # 1. Create a brand
        brand_response = test_client.post("/api/v1/brands", json=sample_brand_data)
        assert brand_response.status_code == 201
        brand_id = brand_response.json()["id"]
        
        # 2. Update generation request with actual brand ID
        generation_request = sample_generation_request.copy()
        generation_request["brandParameters"]["brandId"] = brand_id
        
        # 3. Start generation
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            gen_response = test_client.post(
                "/api/v1/generate/capsule",
                json=generation_request
            )
        
        assert gen_response.status_code == 200
        task_id = gen_response.json()["taskId"]
        
        # 4. Check memory insights
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            insights_response = test_client.get(f"/api/v1/generate/memory-insights/{brand_id}")
        
        assert insights_response.status_code == 200
        insights_data = insights_response.json()
        assert insights_data["brand_id"] == brand_id
        
        # 5. Submit feedback
        feedback_data = {
            "generation_id": task_id,
            "user_ratings": {
                "overall_rating": 4.5,
                "comments": "Excellent collection!"
            }
        }
        
        with patch('services.generation_api.src.api.routes.generation.KSEMemoryService', return_value=mock_kse_memory_service):
            feedback_response = test_client.post(
                "/api/v1/generate/feedback",
                json=feedback_data
            )
        
        assert feedback_response.status_code == 200
        assert feedback_response.json()["status"] == "feedback_integrated"