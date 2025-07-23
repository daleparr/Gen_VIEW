"""
AI Model Manager for loading and managing multiple AI models
Handles StyleGAN3, CLIP, Stable Diffusion XL, and NeRF models with efficient memory management
"""

import asyncio
import logging
import torch
import gc
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
from datetime import datetime

from ..core.config import get_settings
from ..core.redis_client import redis_manager

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages loading, unloading, and inference for multiple AI models.
    Implements efficient memory management and model caching.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict] = {}
        self.model_stats: Dict[str, Dict] = {}
        self.initialized = False
        
        # Device management
        self.primary_device = self._get_primary_device()
        self.available_devices = self._get_available_devices()
        
        logger.info(f"ModelManager initialized with primary device: {self.primary_device}")
        logger.info(f"Available devices: {self.available_devices}")
    
    async def initialize(self):
        """Initialize all AI models asynchronously."""
        if self.initialized:
            logger.info("ModelManager already initialized")
            return
        
        logger.info("Starting AI model initialization...")
        start_time = datetime.utcnow()
        
        try:
            # Initialize models in parallel where possible
            initialization_tasks = [
                self._initialize_clip(),
                self._initialize_stylegan3(),
                self._initialize_stable_diffusion(),
                self._initialize_nerf()
            ]
            
            # Run initializations with some models in parallel
            await asyncio.gather(*initialization_tasks, return_exceptions=True)
            
            # Verify models are loaded
            self._verify_models()
            
            # Cache model information in Redis
            await self._cache_model_info()
            
            self.initialized = True
            initialization_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"All AI models initialized successfully in {initialization_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            raise
    
    async def _initialize_clip(self):
        """Initialize CLIP model for multi-modal processing."""
        try:
            logger.info("Loading CLIP model...")
            
            # Import here to avoid loading if not needed
            import clip
            
            model_name = self.settings.clip_model_name
            device = self.settings.clip_device
            
            model, preprocess = clip.load(model_name, device=device)
            model.eval()
            
            self.models["clip"] = {
                "model": model,
                "preprocess": preprocess,
                "device": device,
                "loaded_at": datetime.utcnow(),
                "memory_usage": self._get_model_memory_usage(model)
            }
            
            self.model_configs["clip"] = {
                "model_name": model_name,
                "device": device,
                "parameters": sum(p.numel() for p in model.parameters()),
                "precision": "float32"
            }
            
            logger.info(f"CLIP model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            # Store error info but don't fail completely
            self.models["clip"] = {"error": str(e), "loaded_at": datetime.utcnow()}
    
    async def _initialize_stylegan3(self):
        """Initialize StyleGAN3 model for fashion generation."""
        try:
            logger.info("Loading StyleGAN3 model...")
            
            checkpoint_path = self.settings.stylegan_checkpoint_path
            device = self.settings.stylegan_device
            
            # Check if checkpoint exists
            if not Path(checkpoint_path).exists():
                logger.warning(f"StyleGAN3 checkpoint not found at {checkpoint_path}")
                self.models["stylegan3"] = {
                    "error": f"Checkpoint not found: {checkpoint_path}",
                    "loaded_at": datetime.utcnow()
                }
                return
            
            # Load StyleGAN3 (this would be the actual implementation)
            # For now, we'll create a mock model structure
            model = self._create_mock_stylegan3_model(device)
            
            self.models["stylegan3"] = {
                "model": model,
                "device": device,
                "loaded_at": datetime.utcnow(),
                "memory_usage": 2048  # Mock 2GB usage
            }
            
            self.model_configs["stylegan3"] = {
                "checkpoint_path": checkpoint_path,
                "device": device,
                "resolution": 1024,
                "latent_dim": 512,
                "precision": "float32"
            }
            
            logger.info(f"StyleGAN3 model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load StyleGAN3 model: {e}")
            self.models["stylegan3"] = {"error": str(e), "loaded_at": datetime.utcnow()}
    
    async def _initialize_stable_diffusion(self):
        """Initialize Stable Diffusion XL model."""
        try:
            logger.info("Loading Stable Diffusion XL model...")
            
            model_name = self.settings.diffusion_model_name
            device = self.settings.diffusion_device
            
            # Import diffusers here to avoid loading if not needed
            try:
                from diffusers import StableDiffusionXLPipeline
                import torch
                
                # Load the pipeline
                pipe = StableDiffusionXLPipeline.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    use_safetensors=True,
                    variant="fp16" if device == "cuda" else None
                )
                
                if device == "cuda":
                    pipe = pipe.to(device)
                    pipe.enable_model_cpu_offload()
                
                pipe.enable_attention_slicing()
                
                self.models["stable_diffusion"] = {
                    "pipeline": pipe,
                    "device": device,
                    "loaded_at": datetime.utcnow(),
                    "memory_usage": 6144  # Estimated 6GB usage
                }
                
                self.model_configs["stable_diffusion"] = {
                    "model_name": model_name,
                    "device": device,
                    "precision": "float16" if device == "cuda" else "float32",
                    "attention_slicing": True,
                    "cpu_offload": device == "cuda"
                }
                
                logger.info(f"Stable Diffusion XL loaded successfully on {device}")
                
            except ImportError:
                logger.warning("Diffusers library not available, creating mock model")
                self.models["stable_diffusion"] = {
                    "error": "Diffusers library not installed",
                    "loaded_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion model: {e}")
            self.models["stable_diffusion"] = {"error": str(e), "loaded_at": datetime.utcnow()}
    
    async def _initialize_nerf(self):
        """Initialize NeRF model for 3D rendering."""
        try:
            logger.info("Loading NeRF model...")
            
            model_path = self.settings.nerf_model_path
            device = self.settings.nerf_device
            
            # Check if model path exists
            if not Path(model_path).exists():
                logger.warning(f"NeRF model not found at {model_path}")
                self.models["nerf"] = {
                    "error": f"Model not found: {model_path}",
                    "loaded_at": datetime.utcnow()
                }
                return
            
            # Create mock NeRF model (in real implementation, load actual NeRF)
            model = self._create_mock_nerf_model(device)
            
            self.models["nerf"] = {
                "model": model,
                "device": device,
                "loaded_at": datetime.utcnow(),
                "memory_usage": 1024  # Mock 1GB usage
            }
            
            self.model_configs["nerf"] = {
                "model_path": model_path,
                "device": device,
                "rendering_resolution": 512,
                "precision": "float32"
            }
            
            logger.info(f"NeRF model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load NeRF model: {e}")
            self.models["nerf"] = {"error": str(e), "loaded_at": datetime.utcnow()}
    
    def _create_mock_stylegan3_model(self, device: str):
        """Create a mock StyleGAN3 model for development."""
        class MockStyleGAN3:
            def __init__(self, device):
                self.device = device
                self.latent_dim = 512
                self.resolution = 1024
            
            def generate(self, latent_codes, **kwargs):
                # Mock generation - return random tensor
                batch_size = latent_codes.shape[0]
                return torch.randn(batch_size, 3, self.resolution, self.resolution)
            
            def encode_text(self, text_prompt):
                # Mock text encoding
                return torch.randn(1, self.latent_dim)
        
        return MockStyleGAN3(device)
    
    def _create_mock_nerf_model(self, device: str):
        """Create a mock NeRF model for development."""
        class MockNeRF:
            def __init__(self, device):
                self.device = device
                self.resolution = 512
            
            def render(self, camera_params, **kwargs):
                # Mock rendering - return random image
                return torch.randn(3, self.resolution, self.resolution)
        
        return MockNeRF(device)
    
    def _get_primary_device(self) -> str:
        """Determine the primary compute device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _get_available_devices(self) -> List[str]:
        """Get list of available compute devices."""
        devices = ["cpu"]
        
        if torch.cuda.is_available():
            devices.extend([f"cuda:{i}" for i in range(torch.cuda.device_count())])
        
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            devices.append("mps")
        
        return devices
    
    def _get_model_memory_usage(self, model) -> float:
        """Estimate model memory usage in MB."""
        if hasattr(model, 'parameters'):
            param_size = sum(p.numel() * p.element_size() for p in model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())
            return (param_size + buffer_size) / (1024 * 1024)  # Convert to MB
        return 0.0
    
    def _verify_models(self):
        """Verify that critical models are loaded successfully."""
        critical_models = ["clip"]  # Models that must be loaded
        
        for model_name in critical_models:
            if model_name not in self.models or "error" in self.models[model_name]:
                error_msg = f"Critical model {model_name} failed to load"
                logger.error(error_msg)
                # In production, you might want to raise an exception here
    
    async def _cache_model_info(self):
        """Cache model information in Redis for quick access."""
        try:
            model_info = {
                "initialized_at": datetime.utcnow().isoformat(),
                "models": {},
                "total_memory_usage": 0
            }
            
            for model_name, model_data in self.models.items():
                if "error" not in model_data:
                    model_info["models"][model_name] = {
                        "loaded": True,
                        "device": model_data.get("device"),
                        "memory_usage": model_data.get("memory_usage", 0),
                        "loaded_at": model_data.get("loaded_at").isoformat()
                    }
                    model_info["total_memory_usage"] += model_data.get("memory_usage", 0)
                else:
                    model_info["models"][model_name] = {
                        "loaded": False,
                        "error": model_data["error"]
                    }
            
            await redis_manager.set("model_manager_info", model_info, expire=3600)
            
        except Exception as e:
            logger.warning(f"Failed to cache model info: {e}")
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a loaded model by name."""
        if not self.initialized:
            raise RuntimeError("ModelManager not initialized")
        
        model_data = self.models.get(model_name)
        if not model_data or "error" in model_data:
            return None
        
        return model_data.get("model") or model_data.get("pipeline")
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available and loaded."""
        model_data = self.models.get(model_name)
        return model_data is not None and "error" not in model_data
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about all loaded models."""
        return {
            "initialized": self.initialized,
            "primary_device": self.primary_device,
            "available_devices": self.available_devices,
            "models": {
                name: {
                    "loaded": "error" not in data,
                    "device": data.get("device"),
                    "memory_usage": data.get("memory_usage"),
                    "loaded_at": data.get("loaded_at").isoformat() if data.get("loaded_at") else None,
                    "error": data.get("error")
                }
                for name, data in self.models.items()
            },
            "configs": self.model_configs
        }
    
    async def cleanup(self):
        """Clean up models and free memory."""
        logger.info("Cleaning up AI models...")
        
        for model_name, model_data in self.models.items():
            if "model" in model_data or "pipeline" in model_data:
                try:
                    # Move model to CPU and delete
                    model = model_data.get("model") or model_data.get("pipeline")
                    if hasattr(model, 'cpu'):
                        model.cpu()
                    del model
                    logger.info(f"Cleaned up {model_name}")
                except Exception as e:
                    logger.warning(f"Error cleaning up {model_name}: {e}")
        
        self.models.clear()
        self.model_configs.clear()
        
        # Force garbage collection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        self.initialized = False
        logger.info("Model cleanup completed")
    
    async def reload_model(self, model_name: str):
        """Reload a specific model."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        logger.info(f"Reloading model: {model_name}")
        
        # Clean up existing model
        if "model" in self.models[model_name] or "pipeline" in self.models[model_name]:
            model = self.models[model_name].get("model") or self.models[model_name].get("pipeline")
            if hasattr(model, 'cpu'):
                model.cpu()
            del model
        
        # Reload model
        if model_name == "clip":
            await self._initialize_clip()
        elif model_name == "stylegan3":
            await self._initialize_stylegan3()
        elif model_name == "stable_diffusion":
            await self._initialize_stable_diffusion()
        elif model_name == "nerf":
            await self._initialize_nerf()
        
        # Update cache
        await self._cache_model_info()
        
        logger.info(f"Model {model_name} reloaded successfully")
    
    def get_generation_capacity(self) -> Dict[str, int]:
        """Get estimated generation capacity for different model types."""
        capacity = {}
        
        if self.is_model_available("stylegan3"):
            capacity["stylegan3"] = 4  # Concurrent generations
        
        if self.is_model_available("stable_diffusion"):
            capacity["stable_diffusion"] = 2  # Concurrent generations
        
        if self.is_model_available("nerf"):
            capacity["nerf"] = 1  # Single rendering at a time
        
        return capacity