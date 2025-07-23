"""
NeRF Service for Neural Radiance Field Rendering
Handles NeRF model training, inference, and 3D scene rendering
"""

import asyncio
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json
from pathlib import Path
import cv2
from PIL import Image
import trimesh
import open3d as o3d

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class NeRFModel(nn.Module):
    """
    Simplified NeRF model implementation for fashion product rendering.
    Based on the original NeRF paper with optimizations for real-time inference.
    """
    
    def __init__(
        self,
        input_dim: int = 3,
        hidden_dim: int = 256,
        num_layers: int = 8,
        skip_layers: List[int] = [4],
        use_viewdirs: bool = True,
        viewdir_dim: int = 3
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.skip_layers = skip_layers
        self.use_viewdirs = use_viewdirs
        
        # Position encoding
        self.pos_encoding_dim = 60  # 3 * 2 * 10 (L=10)
        self.dir_encoding_dim = 24  # 3 * 2 * 4 (L=4)
        
        # Main MLP for density and features
        layers = []
        in_dim = self.pos_encoding_dim
        
        for i in range(num_layers):
            if i in skip_layers:
                in_dim += self.pos_encoding_dim
            
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.ReLU(inplace=True))
            in_dim = hidden_dim
        
        self.density_layers = nn.ModuleList(layers)
        
        # Density output
        self.density_head = nn.Linear(hidden_dim, 1)
        
        # Feature output (for color prediction)
        self.feature_head = nn.Linear(hidden_dim, hidden_dim)
        
        # Color MLP (if using view directions)
        if use_viewdirs:
            self.color_layers = nn.Sequential(
                nn.Linear(hidden_dim + self.dir_encoding_dim, hidden_dim // 2),
                nn.ReLU(inplace=True),
                nn.Linear(hidden_dim // 2, 3),
                nn.Sigmoid()
            )
        else:
            self.color_layers = nn.Sequential(
                nn.Linear(hidden_dim, 3),
                nn.Sigmoid()
            )
    
    def positional_encoding(self, x: torch.Tensor, L: int = 10) -> torch.Tensor:
        """Apply positional encoding to input coordinates."""
        encoding = []
        for i in range(L):
            encoding.append(torch.sin(2**i * np.pi * x))
            encoding.append(torch.cos(2**i * np.pi * x))
        return torch.cat(encoding, dim=-1)
    
    def forward(
        self, 
        positions: torch.Tensor, 
        directions: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through NeRF model.
        
        Args:
            positions: 3D positions (batch_size, 3)
            directions: View directions (batch_size, 3)
            
        Returns:
            Tuple of (colors, densities)
        """
        # Encode positions
        pos_encoded = self.positional_encoding(positions, L=10)
        
        # Forward through density layers
        x = pos_encoded
        for i, layer in enumerate(self.density_layers):
            if i > 0 and (i // 2) in self.skip_layers:
                x = torch.cat([x, pos_encoded], dim=-1)
            x = layer(x)
        
        # Get density
        density = F.relu(self.density_head(x))
        
        # Get features for color prediction
        features = self.feature_head(x)
        
        # Predict color
        if self.use_viewdirs and directions is not None:
            dir_encoded = self.positional_encoding(directions, L=4)
            color_input = torch.cat([features, dir_encoded], dim=-1)
        else:
            color_input = features
        
        colors = self.color_layers(color_input)
        
        return colors, density


class NeRFService:
    """
    NeRF service for neural radiance field operations.
    Handles model loading, training, and inference for fashion product rendering.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.device = torch.device(
            self.settings.rendering_device if torch.cuda.is_available() 
            else "cpu"
        )
        
        # Model storage
        self.models: Dict[str, NeRFModel] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Rendering parameters
        self.near = 0.1
        self.far = 10.0
        self.num_samples = self.settings.nerf_num_samples
        self.resolution = self.settings.nerf_resolution
        
        logger.info(f"NeRF Service initialized on device: {self.device}")
    
    async def initialize(self):
        """Initialize the NeRF service."""
        try:
            logger.info("Initializing NeRF Service...")
            
            # Create model directory
            os.makedirs(self.settings.nerf_model_path, exist_ok=True)
            
            # Load any existing models
            await self._load_existing_models()
            
            logger.info("NeRF Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NeRF Service: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up NeRF Service...")
        # Clear GPU memory
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
    
    async def _load_existing_models(self):
        """Load existing NeRF models from disk."""
        try:
            model_path = Path(self.settings.nerf_model_path)
            if not model_path.exists():
                return
            
            for model_file in model_path.glob("*.pth"):
                model_id = model_file.stem
                await self.load_model(model_id)
            
            logger.info(f"Loaded {len(self.models)} existing NeRF models")
            
        except Exception as e:
            logger.error(f"Failed to load existing models: {e}")
    
    async def load_model(self, model_id: str) -> bool:
        """Load a NeRF model from disk."""
        try:
            model_path = Path(self.settings.nerf_model_path) / f"{model_id}.pth"
            metadata_path = Path(self.settings.nerf_model_path) / f"{model_id}_meta.json"
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            # Load metadata
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Create and load model
            model = NeRFModel(
                hidden_dim=metadata.get('hidden_dim', 256),
                num_layers=metadata.get('num_layers', 8),
                use_viewdirs=metadata.get('use_viewdirs', True)
            )
            
            # Load state dict
            checkpoint = torch.load(model_path, map_location=self.device)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.to(self.device)
            model.eval()
            
            self.models[model_id] = model
            self.model_metadata[model_id] = metadata
            
            logger.info(f"Loaded NeRF model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def create_model(
        self,
        model_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Create a new NeRF model."""
        try:
            # Create model with specified configuration
            model = NeRFModel(
                hidden_dim=config.get('hidden_dim', 256),
                num_layers=config.get('num_layers', 8),
                use_viewdirs=config.get('use_viewdirs', True)
            )
            
            model.to(self.device)
            
            # Store model and metadata
            self.models[model_id] = model
            self.model_metadata[model_id] = config
            
            logger.info(f"Created NeRF model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create model {model_id}: {e}")
            return False
    
    async def render_image(
        self,
        model_id: str,
        camera_pose: np.ndarray,
        intrinsics: Dict[str, float],
        resolution: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Render an image from a NeRF model.
        
        Args:
            model_id: ID of the NeRF model to use
            camera_pose: 4x4 camera pose matrix
            intrinsics: Camera intrinsics (fx, fy, cx, cy)
            resolution: Image resolution (width, height)
            
        Returns:
            Rendered image as numpy array
        """
        try:
            if model_id not in self.models:
                logger.error(f"Model {model_id} not found")
                return None
            
            model = self.models[model_id]
            res = resolution or (self.resolution, self.resolution)
            
            # Generate rays
            rays_o, rays_d = self._generate_rays(camera_pose, intrinsics, res)
            
            # Render image
            with torch.no_grad():
                image = await self._render_rays(model, rays_o, rays_d)
            
            # Convert to numpy
            image_np = image.cpu().numpy()
            image_np = (image_np * 255).astype(np.uint8)
            
            return image_np
            
        except Exception as e:
            logger.error(f"Failed to render image: {e}")
            return None
    
    def _generate_rays(
        self,
        camera_pose: np.ndarray,
        intrinsics: Dict[str, float],
        resolution: Tuple[int, int]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Generate camera rays for rendering."""
        width, height = resolution
        fx, fy = intrinsics['fx'], intrinsics['fy']
        cx, cy = intrinsics['cx'], intrinsics['cy']
        
        # Create pixel coordinates
        i, j = np.meshgrid(
            np.arange(width, dtype=np.float32),
            np.arange(height, dtype=np.float32),
            indexing='xy'
        )
        
        # Convert to camera coordinates
        dirs = np.stack([
            (i - cx) / fx,
            -(j - cy) / fy,
            -np.ones_like(i)
        ], axis=-1)
        
        # Transform ray directions to world coordinates
        rays_d = np.sum(dirs[..., None, :] * camera_pose[:3, :3], axis=-1)
        rays_d = rays_d / np.linalg.norm(rays_d, axis=-1, keepdims=True)
        
        # Ray origins
        rays_o = np.broadcast_to(camera_pose[:3, 3], rays_d.shape)
        
        # Convert to tensors
        rays_o = torch.from_numpy(rays_o).to(self.device)
        rays_d = torch.from_numpy(rays_d).to(self.device)
        
        return rays_o, rays_d
    
    async def _render_rays(
        self,
        model: NeRFModel,
        rays_o: torch.Tensor,
        rays_d: torch.Tensor
    ) -> torch.Tensor:
        """Render rays through the NeRF model."""
        batch_size = self.settings.nerf_batch_size
        height, width = rays_o.shape[:2]
        
        # Flatten rays
        rays_o_flat = rays_o.view(-1, 3)
        rays_d_flat = rays_d.view(-1, 3)
        
        # Render in batches
        all_colors = []
        
        for i in range(0, rays_o_flat.shape[0], batch_size):
            batch_rays_o = rays_o_flat[i:i + batch_size]
            batch_rays_d = rays_d_flat[i:i + batch_size]
            
            # Sample points along rays
            t_vals = torch.linspace(
                self.near, self.far, self.num_samples,
                device=self.device
            )
            
            # Add noise to sampling positions
            if model.training:
                t_vals = t_vals + torch.rand_like(t_vals) * (self.far - self.near) / self.num_samples
            
            # Get 3D points
            pts = batch_rays_o[..., None, :] + batch_rays_d[..., None, :] * t_vals[..., :, None]
            pts_flat = pts.view(-1, 3)
            
            # Get view directions
            viewdirs = batch_rays_d / torch.norm(batch_rays_d, dim=-1, keepdim=True)
            viewdirs = viewdirs[..., None, :].expand(pts.shape)
            viewdirs_flat = viewdirs.view(-1, 3)
            
            # Forward through model
            colors, densities = model(pts_flat, viewdirs_flat)
            
            # Reshape outputs
            colors = colors.view(batch_rays_o.shape[0], self.num_samples, 3)
            densities = densities.view(batch_rays_o.shape[0], self.num_samples, 1)
            
            # Volume rendering
            dists = t_vals[..., 1:] - t_vals[..., :-1]
            dists = torch.cat([
                dists,
                torch.full_like(dists[..., :1], 1e10)
            ], dim=-1)
            
            alpha = 1.0 - torch.exp(-densities[..., 0] * dists)
            weights = alpha * torch.cumprod(
                torch.cat([
                    torch.ones_like(alpha[..., :1]),
                    1.0 - alpha[..., :-1]
                ], dim=-1),
                dim=-1
            )
            
            # Composite colors
            rgb = torch.sum(weights[..., None] * colors, dim=-2)
            all_colors.append(rgb)
        
        # Concatenate all batches
        final_colors = torch.cat(all_colors, dim=0)
        
        # Reshape to image
        image = final_colors.view(height, width, 3)
        
        return image
    
    async def render_360_video(
        self,
        model_id: str,
        intrinsics: Dict[str, float],
        radius: float = 3.0,
        num_frames: int = 120,
        resolution: Optional[Tuple[int, int]] = None
    ) -> Optional[List[np.ndarray]]:
        """
        Render a 360-degree rotation video of the NeRF model.
        
        Args:
            model_id: ID of the NeRF model
            intrinsics: Camera intrinsics
            radius: Camera distance from origin
            num_frames: Number of frames in the video
            resolution: Image resolution
            
        Returns:
            List of rendered frames
        """
        try:
            if model_id not in self.models:
                logger.error(f"Model {model_id} not found")
                return None
            
            frames = []
            
            for i in range(num_frames):
                # Calculate camera position
                angle = 2 * np.pi * i / num_frames
                camera_pos = np.array([
                    radius * np.cos(angle),
                    0.0,
                    radius * np.sin(angle)
                ])
                
                # Look at origin
                look_at = np.array([0.0, 0.0, 0.0])
                up = np.array([0.0, 1.0, 0.0])
                
                # Create camera pose matrix
                camera_pose = self._look_at_matrix(camera_pos, look_at, up)
                
                # Render frame
                frame = await self.render_image(
                    model_id, camera_pose, intrinsics, resolution
                )
                
                if frame is not None:
                    frames.append(frame)
                
                # Yield control to allow other operations
                await asyncio.sleep(0)
            
            logger.info(f"Rendered {len(frames)} frames for 360° video")
            return frames
            
        except Exception as e:
            logger.error(f"Failed to render 360° video: {e}")
            return None
    
    def _look_at_matrix(
        self,
        eye: np.ndarray,
        target: np.ndarray,
        up: np.ndarray
    ) -> np.ndarray:
        """Create a look-at camera pose matrix."""
        forward = target - eye
        forward = forward / np.linalg.norm(forward)
        
        right = np.cross(forward, up)
        right = right / np.linalg.norm(right)
        
        up = np.cross(right, forward)
        
        pose = np.eye(4)
        pose[:3, 0] = right
        pose[:3, 1] = up
        pose[:3, 2] = -forward
        pose[:3, 3] = eye
        
        return pose
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a NeRF model."""
        if model_id not in self.models:
            return None
        
        model = self.models[model_id]
        metadata = self.model_metadata.get(model_id, {})
        
        # Count parameters
        num_params = sum(p.numel() for p in model.parameters())
        
        return {
            "model_id": model_id,
            "num_parameters": num_params,
            "device": str(self.device),
            "metadata": metadata,
            "is_trained": metadata.get('is_trained', False)
        }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available NeRF models."""
        models_info = []
        
        for model_id in self.models.keys():
            info = await self.get_model_info(model_id)
            if info:
                models_info.append(info)
        
        return models_info
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the NeRF service."""
        try:
            health = {
                'status': 'healthy',
                'device': str(self.device),
                'models_loaded': len(self.models),
                'cuda_available': torch.cuda.is_available(),
                'memory_allocated': 0,
                'memory_cached': 0
            }
            
            if torch.cuda.is_available():
                health['memory_allocated'] = torch.cuda.memory_allocated(self.device)
                health['memory_cached'] = torch.cuda.memory_reserved(self.device)
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }