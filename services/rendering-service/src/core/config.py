"""
Configuration settings for NeRF Rendering Service
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Service configuration
    service_name: str = "nerf-rendering-service"
    service_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    
    # Rendering configuration
    rendering_device: str = Field(default="cpu", env="RENDERING_DEVICE")  # cpu, cuda
    max_concurrent_renders: int = Field(default=4, env="MAX_CONCURRENT_RENDERS")
    render_timeout: int = Field(default=300, env="RENDER_TIMEOUT")  # 5 minutes
    
    # NeRF configuration
    nerf_model_path: str = Field(default="/app/models/nerf", env="NERF_MODEL_PATH")
    nerf_resolution: int = Field(default=512, env="NERF_RESOLUTION")
    nerf_num_samples: int = Field(default=64, env="NERF_NUM_SAMPLES")
    nerf_batch_size: int = Field(default=1024, env="NERF_BATCH_SIZE")
    
    # 3D processing configuration
    mesh_simplification_ratio: float = Field(default=0.5, env="MESH_SIMPLIFICATION_RATIO")
    texture_resolution: int = Field(default=1024, env="TEXTURE_RESOLUTION")
    max_mesh_vertices: int = Field(default=100000, env="MAX_MESH_VERTICES")
    
    # File storage configuration
    output_directory: str = Field(default="/app/outputs", env="OUTPUT_DIRECTORY")
    cache_directory: str = Field(default="/app/cache", env="CACHE_DIRECTORY")
    model_directory: str = Field(default="/app/models", env="MODEL_DIRECTORY")
    temp_directory: str = Field(default="/tmp/rendering", env="TEMP_DIRECTORY")
    
    # Performance configuration
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    memory_limit_gb: float = Field(default=8.0, env="MEMORY_LIMIT_GB")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Quality settings
    render_quality: str = Field(default="medium", env="RENDER_QUALITY")  # low, medium, high
    anti_aliasing: bool = Field(default=True, env="ANTI_ALIASING")
    shadow_quality: str = Field(default="medium", env="SHADOW_QUALITY")
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    max_request_size: int = Field(default=100 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 100MB
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # External service URLs
    generation_api_url: str = Field(default="http://localhost:8001", env="GENERATION_API_URL")
    memory_service_url: str = Field(default="http://localhost:8002", env="MEMORY_SERVICE_URL")
    curation_engine_url: str = Field(default="http://localhost:8004", env="CURATION_ENGINE_URL")
    
    # Fashion-specific configuration
    garment_categories: list = Field(
        default=["tops", "bottoms", "dresses", "outerwear", "accessories"],
        env="GARMENT_CATEGORIES"
    )
    supported_materials: list = Field(
        default=["cotton", "silk", "wool", "leather", "synthetic"],
        env="SUPPORTED_MATERIALS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings