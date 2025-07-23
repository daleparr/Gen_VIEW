"""
GEN-VIEW-KSE Test Suite Configuration
Pytest fixtures and configuration for comprehensive testing
"""

import pytest
import asyncio
import uuid
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
import json

# FastAPI and database imports
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Application imports
from services.generation_api.src.main import app
from services.generation_api.src.core.database import get_db
from services.generation_api.src.core.config import get_settings
from services.generation_api.src.models.fashion_models import Base as FashionBase
from services.generation_api.src.models.generation_models import Base as GenerationBase
from services.generation_api.src.models.user_models import Base as UserBase
from services.generation_api.src.services.model_manager import ModelManager
from services.generation_api.src.services.kse_memory_service import KSEMemoryService
from services.generation_api.src.services.multimodal_processor import MultiModalProcessor

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(FashionBase.metadata.create_all)
        await conn.run_sync(GenerationBase.metadata.create_all)
        await conn.run_sync(UserBase.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(FashionBase.metadata.drop_all)
        await conn.run_sync(GenerationBase.metadata.drop_all)
        await conn.run_sync(UserBase.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
def test_client(test_db_session):
    """Create test client with database dependency override."""
    
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_model_manager():
    """Mock model manager for testing."""
    class MockModelManager:
        def __init__(self):
            self.models = {}
        
        def get_model(self, model_name: str):
            return {
                "model": MockModel(),
                "preprocess": lambda x: x,
                "tokenize": lambda x: x
            }
        
        def load_model(self, model_name: str, model_path: str):
            self.models[model_name] = {"loaded": True, "path": model_path}
            return True
        
        def unload_model(self, model_name: str):
            if model_name in self.models:
                del self.models[model_name]
                return True
            return False
    
    class MockModel:
        def encode_text(self, tokens):
            # Return mock embedding
            import torch
            return torch.randn(1, 512)
        
        def encode_image(self, image):
            # Return mock embedding
            import torch
            return torch.randn(1, 512)
    
    return MockModelManager()

@pytest.fixture
def mock_kse_memory_service():
    """Mock KSE Memory Service for testing."""
    class MockKSEMemoryService:
        def __init__(self):
            self.memory_store = {}
            self.feedback_store = {}
        
        async def store_generation_context(self, generation_id, inputs, outputs, commercial_data=None):
            self.memory_store[generation_id] = {
                "inputs": inputs,
                "outputs": outputs,
                "commercial_data": commercial_data,
                "stored_at": datetime.utcnow().isoformat()
            }
        
        async def retrieve_relevant_context(self, inputs, brand_id=None, depth=5):
            return {
                "memory_nodes": [
                    {
                        "id": f"mock_node_{i}",
                        "similarity_score": 0.8 - (i * 0.1),
                        "metadata": {"generation_id": f"gen_{i}"}
                    }
                    for i in range(min(depth, 3))
                ],
                "temporal_context": {
                    "temporal_coherence": 0.85,
                    "evolution_stage": "mature"
                },
                "design_evolution": {
                    "generations": [],
                    "evolution_trends": {"trend": "improving"},
                    "consistency_score": 0.8
                },
                "brand_consistency_patterns": {
                    "dominant_styles": ["minimalist", "contemporary"],
                    "color_preferences": ["neutral", "monochrome"],
                    "consistency_score": 0.85
                },
                "commercial_insights": {
                    "average_conversion_rate": 0.15,
                    "revenue_trend": "increasing"
                }
            }
        
        async def integrate_feedback(self, generation_id, commercial_outcomes=None, user_ratings=None, db=None):
            self.feedback_store[generation_id] = {
                "commercial_outcomes": commercial_outcomes,
                "user_ratings": user_ratings,
                "integrated_at": datetime.utcnow().isoformat()
            }
        
        async def get_brand_memory_insights(self, brand_id):
            return {
                "total_nodes": 25,
                "recent_generations": [
                    {
                        "id": "gen_1",
                        "timestamp": datetime.utcnow().isoformat(),
                        "generationType": "capsule_collection",
                        "qualityScore": 0.85
                    }
                ],
                "design_evolution": {
                    "evolution_velocity": 0.65,
                    "consistency_trend": "stable",
                    "innovation_index": 0.72
                },
                "commercial_performance": {
                    "average_conversion_rate": 0.15,
                    "revenue_trend": "increasing"
                },
                "temporal_patterns": {
                    "seasonal_cycles": ["spring_fresh", "summer_light"]
                },
                "memory_health": {
                    "overall_health": 0.8,
                    "node_count": 25,
                    "recent_activity": 8
                },
                "learning_velocity": {
                    "learning_velocity": 0.6,
                    "velocity_category": "moderate"
                }
            }
    
    return MockKSEMemoryService()

@pytest.fixture
def mock_multimodal_processor():
    """Mock Multi-Modal Processor for testing."""
    class MockMultiModalProcessor:
        async def encode_text(self, text_prompt):
            # Return consistent mock embedding based on text hash
            text_hash = hash(text_prompt) % 1000
            return [0.1 * (text_hash % 100)] * 512
        
        async def encode_image(self, image_url):
            # Return mock image embedding
            url_hash = hash(image_url) % 1000
            return [0.2 * (url_hash % 100)] * 512
        
        async def encode_sketch(self, sketch_url):
            # Return mock sketch embedding
            url_hash = hash(sketch_url) % 1000
            return [0.3 * (url_hash % 100)] * 512
        
        async def encode_colors(self, color_palette):
            # Return mock color embedding
            return [0.4] * 512
        
        async def encode_materials(self, material_preferences):
            # Return mock material embedding
            return [0.5] * 512
    
    return MockMultiModalProcessor()

@pytest.fixture
def sample_brand_data():
    """Sample brand data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Fashion Brand",
        "description": "A test fashion brand for unit testing",
        "design_dna": {
            "aesthetic": "minimalist",
            "sustainability_focus": True,
            "color_preference": ["black", "white", "beige"],
            "silhouette_style": "clean_lines"
        },
        "target_demographic": {
            "age_range": "25-40",
            "income_level": "middle_to_high",
            "style_preference": "contemporary"
        },
        "market_segment": "luxury",
        "brand_values": ["quality", "sustainability", "timeless_design"]
    }

@pytest.fixture
def sample_collection_data(sample_brand_data):
    """Sample collection data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Spring Collection",
        "description": "A test collection for spring season",
        "brand_id": sample_brand_data["id"],
        "season": "spring",
        "year": 2024,
        "theme": "Minimalist Spring",
        "inspiration": "Clean lines and natural materials",
        "target_pieces": 5,
        "generation_config": {
            "quality_level": "high",
            "creativity_level": 0.7
        }
    }

@pytest.fixture
def sample_generation_request():
    """Sample generation request for testing."""
    return {
        "name": "Test Capsule Generation",
        "description": "Test generation for unit testing",
        "inputs": {
            "textPrompt": "minimalist spring collection with clean lines",
            "referenceImages": ["https://example.com/ref1.jpg"],
            "sketchInputs": [],
            "colorPalette": ["white", "beige", "black"],
            "materialPreferences": ["cotton", "linen"],
            "styleVectors": [],
            "brandContext": {
                "brandId": str(uuid.uuid4()),
                "designDNA": {
                    "aesthetic": "minimalist",
                    "colorPreferences": ["neutral"],
                    "silhouetteStyle": "clean_lines"
                }
            }
        },
        "brandParameters": {
            "brandId": str(uuid.uuid4()),
            "designDnaAdherence": 0.8,
            "targetDemographic": "urban_professional",
            "pricePoint": "premium"
        },
        "targetPieces": 5,
        "qualityLevel": "high",
        "creativityLevel": 0.7,
        "useMemoryContext": True,
        "memoryDepth": 5,
        "optimizeForCommercial": True
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@genviewkse.com",
        "username": "testuser",
        "hashed_password": "hashed_password_123",
        "first_name": "Test",
        "last_name": "User",
        "role": "designer",
        "is_active": True,
        "is_verified": True
    }

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    class MockRedisClient:
        def __init__(self):
            self.data = {}
            self.lists = {}
        
        async def set(self, key, value, expire=None):
            self.data[key] = {
                "value": value,
                "expire": expire,
                "set_at": datetime.utcnow()
            }
            return True
        
        async def get(self, key):
            if key in self.data:
                return self.data[key]["value"]
            return None
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
                return True
            return False
        
        async def add_to_list(self, key, value):
            if key not in self.lists:
                self.lists[key] = []
            self.lists[key].append(value)
        
        async def get_list(self, key, start=0, end=-1):
            if key not in self.lists:
                return []
            return self.lists[key][start:end+1 if end >= 0 else None]
        
        async def exists(self, key):
            return key in self.data
    
    return MockRedisClient()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing real-time features."""
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            self.closed = False
        
        async def accept(self):
            pass
        
        async def send_json(self, data):
            self.messages.append(data)
        
        async def close(self):
            self.closed = True
    
    return MockWebSocket()

# Test data generators
@pytest.fixture
def generation_test_data():
    """Generate various test data for generation testing."""
    return {
        "valid_capsule_request": {
            "name": "Test Capsule Collection",
            "inputs": {
                "textPrompt": "modern minimalist capsule collection",
                "referenceImages": ["https://example.com/ref.jpg"],
                "colorPalette": ["black", "white", "gray"]
            },
            "brandParameters": {
                "brandId": str(uuid.uuid4()),
                "designDnaAdherence": 0.8
            },
            "targetPieces": 5,
            "qualityLevel": "high",
            "creativityLevel": 0.7,
            "useMemoryContext": True,
            "memoryDepth": 5,
            "optimizeForCommercial": True
        },
        "invalid_capsule_request": {
            "name": "",  # Invalid: empty name
            "inputs": {},  # Invalid: no inputs
            "brandParameters": {},  # Invalid: missing required fields
            "targetPieces": 0  # Invalid: zero pieces
        },
        "single_product_request": {
            "inputs": {
                "textPrompt": "elegant silk blouse",
                "colorPalette": ["navy", "cream"]
            },
            "brandId": str(uuid.uuid4()),
            "garmentType": "top"
        },
        "style_transfer_request": {
            "sourceInputs": {
                "referenceImages": ["https://example.com/source.jpg"]
            },
            "targetInputs": {
                "textPrompt": "bohemian style adaptation"
            },
            "brandId": str(uuid.uuid4())
        }
    }

@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "concurrent_requests": 10,
        "request_timeout": 30,
        "max_response_time": 5.0,  # seconds
        "min_throughput": 100,  # requests per second
        "memory_limit": 512,  # MB
        "cpu_limit": 80  # percentage
    }

# Async test utilities
@pytest.fixture
def async_test_utils():
    """Utilities for async testing."""
    class AsyncTestUtils:
        @staticmethod
        async def wait_for_condition(condition_func, timeout=10, interval=0.1):
            """Wait for a condition to become true."""
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                if await condition_func():
                    return True
                await asyncio.sleep(interval)
            return False
        
        @staticmethod
        async def simulate_delay(seconds=0.1):
            """Simulate processing delay."""
            await asyncio.sleep(seconds)
        
        @staticmethod
        def create_mock_task_id():
            """Create a mock task ID."""
            return str(uuid.uuid4())
    
    return AsyncTestUtils()

# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment variables."""
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/1",
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "CHROMADB_HOST": "localhost",
        "CHROMADB_PORT": "8000",
        "LOG_LEVEL": "DEBUG"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)

# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup logic here if needed
    pass