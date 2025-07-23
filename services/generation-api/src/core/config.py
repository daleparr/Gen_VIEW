"""
Configuration management for GEN-VIEW-KSE Generation API
Uses Pydantic settings for type-safe environment variable handling
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "GEN-VIEW-KSE Generation API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/gen_view_kse"
    database_echo: bool = False
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 20
    
    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # ChromaDB settings
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_collection_name: str = "fashion_embeddings"
    
    # AI Model settings
    model_cache_dir: str = "./models"
    max_concurrent_generations: int = 4
    generation_timeout: int = 300  # 5 minutes
    
    # StyleGAN3 settings
    stylegan_checkpoint_path: str = "./models/stylegan3-fashion.pkl"
    stylegan_device: str = "cuda" if os.path.exists("/usr/local/cuda") else "cpu"
    
    # CLIP settings
    clip_model_name: str = "ViT-B/32"
    clip_device: str = "cuda" if os.path.exists("/usr/local/cuda") else "cpu"
    
    # Stable Diffusion settings
    diffusion_model_name: str = "stabilityai/stable-diffusion-xl-base-1.0"
    diffusion_device: str = "cuda" if os.path.exists("/usr/local/cuda") else "cpu"
    
    # NeRF settings
    nerf_model_path: str = "./models/instant-ngp"
    nerf_device: str = "cuda" if os.path.exists("/usr/local/cuda") else "cpu"
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # CORS settings
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    
    # Performance settings
    max_workers: int = 4
    request_timeout: int = 60
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # KSE Substrate settings
    kse_memory_enabled: bool = True
    kse_temporal_reasoning: bool = True
    kse_cross_modal_learning: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Development settings override
class DevelopmentSettings(Settings):
    """Development-specific settings."""
    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"
    
    # Use local resources for development
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/gen_view_kse_dev"
    redis_url: str = "redis://localhost:6379/0"


# Production settings override
class ProductionSettings(Settings):
    """Production-specific settings."""
    debug: bool = False
    database_echo: bool = False
    log_level: str = "WARNING"
    
    # Security hardening for production
    allowed_origins: List[str] = [
        "https://gen-view-kse.com",
        "https://api.gen-view-kse.com"
    ]


def get_settings_for_environment(env: str = None) -> Settings:
    """Get settings based on environment."""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")
    
    if env.lower() == "production":
        return ProductionSettings()
    elif env.lower() == "development":
        return DevelopmentSettings()
    else:
        return Settings()