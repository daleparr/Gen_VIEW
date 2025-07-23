"""
Multi-Modal Processor Service
Handles encoding of text, images, sketches, colors, materials, and style vectors
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union
import httpx
from PIL import Image
import io
import base64

from ..core.config import get_settings
from ..services.model_manager import ModelManager

logger = logging.getLogger(__name__)


class MultiModalProcessor:
    """
    Service for processing and encoding multi-modal inputs.
    Supports text, images, sketches, colors, materials, and style vectors.
    """
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.settings = get_settings()
        self.model_manager = model_manager
        self.clip_model = None
        self.text_encoder = None
        self.image_encoder = None
        
        # Initialize processors
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize the multi-modal processors."""
        try:
            if self.model_manager:
                self.clip_model = self.model_manager.get_model("clip")
            
            logger.info("Multi-Modal Processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Multi-Modal Processor: {e}")
    
    async def encode_text(self, text_prompt: str) -> List[float]:
        """
        Encode text prompt into embedding vector.
        
        Args:
            text_prompt: Text description or prompt
            
        Returns:
            List of floats representing the text embedding
        """
        try:
            if self.clip_model and hasattr(self.clip_model, 'encode_text'):
                # Use actual CLIP model if available
                import torch
                
                # Tokenize and encode text
                tokens = self.clip_model['model'].tokenize([text_prompt])
                with torch.no_grad():
                    text_features = self.clip_model['model'].encode_text(tokens)
                    text_embedding = text_features.cpu().numpy().flatten().tolist()
                
                return text_embedding
            else:
                # Mock implementation for development
                return await self._mock_text_encoding(text_prompt)
                
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return await self._mock_text_encoding(text_prompt)
    
    async def encode_image(self, image_url: str) -> List[float]:
        """
        Encode image into embedding vector.
        
        Args:
            image_url: URL to the image
            
        Returns:
            List of floats representing the image embedding
        """
        try:
            # Download and preprocess image
            image = await self._download_and_preprocess_image(image_url)
            
            if self.clip_model and hasattr(self.clip_model, 'encode_image'):
                # Use actual CLIP model if available
                import torch
                
                # Preprocess image for CLIP
                image_input = self.clip_model['preprocess'](image).unsqueeze(0)
                
                with torch.no_grad():
                    image_features = self.clip_model['model'].encode_image(image_input)
                    image_embedding = image_features.cpu().numpy().flatten().tolist()
                
                return image_embedding
            else:
                # Mock implementation
                return await self._mock_image_encoding(image)
                
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return await self._mock_image_encoding(None)
    
    async def encode_sketch(self, sketch_url: str) -> List[float]:
        """
        Encode sketch/drawing into embedding vector.
        
        Args:
            sketch_url: URL to the sketch image
            
        Returns:
            List of floats representing the sketch embedding
        """
        try:
            # Download and preprocess sketch
            sketch = await self._download_and_preprocess_image(sketch_url)
            
            # Apply sketch-specific preprocessing
            sketch_processed = await self._preprocess_sketch(sketch)
            
            if self.clip_model:
                # Use CLIP for sketch encoding (similar to image)
                import torch
                
                sketch_input = self.clip_model['preprocess'](sketch_processed).unsqueeze(0)
                
                with torch.no_grad():
                    sketch_features = self.clip_model['model'].encode_image(sketch_input)
                    sketch_embedding = sketch_features.cpu().numpy().flatten().tolist()
                
                return sketch_embedding
            else:
                # Mock implementation
                return await self._mock_sketch_encoding(sketch_processed)
                
        except Exception as e:
            logger.error(f"Failed to encode sketch: {e}")
            return await self._mock_sketch_encoding(None)
    
    async def encode_colors(self, color_palette: List[str]) -> List[float]:
        """
        Encode color palette into embedding vector.
        
        Args:
            color_palette: List of color names or hex codes
            
        Returns:
            List of floats representing the color palette embedding
        """
        try:
            # Convert colors to numerical representation
            color_vectors = []
            
            for color in color_palette:
                color_vector = await self._color_to_vector(color)
                color_vectors.append(color_vector)
            
            # Combine color vectors
            if color_vectors:
                # Average the color vectors
                combined_vector = np.mean(color_vectors, axis=0)
                
                # Add color harmony and palette coherence features
                harmony_features = await self._calculate_color_harmony(color_palette)
                
                # Combine color representation with harmony features
                full_embedding = np.concatenate([combined_vector, harmony_features])
                
                return full_embedding.tolist()
            else:
                return [0.0] * 512  # Default embedding size
                
        except Exception as e:
            logger.error(f"Failed to encode colors: {e}")
            return [0.0] * 512
    
    async def encode_materials(self, material_preferences: List[str]) -> List[float]:
        """
        Encode material preferences into embedding vector.
        
        Args:
            material_preferences: List of material names
            
        Returns:
            List of floats representing the material embedding
        """
        try:
            # Material property mappings
            material_properties = {
                'cotton': {'softness': 0.8, 'durability': 0.7, 'breathability': 0.9, 'luxury': 0.4},
                'silk': {'softness': 0.9, 'durability': 0.5, 'breathability': 0.7, 'luxury': 0.9},
                'wool': {'softness': 0.7, 'durability': 0.8, 'breathability': 0.6, 'luxury': 0.7},
                'linen': {'softness': 0.6, 'durability': 0.8, 'breathability': 0.95, 'luxury': 0.6},
                'leather': {'softness': 0.4, 'durability': 0.95, 'breathability': 0.3, 'luxury': 0.8},
                'denim': {'softness': 0.5, 'durability': 0.9, 'breathability': 0.6, 'luxury': 0.5},
                'cashmere': {'softness': 0.95, 'durability': 0.6, 'breathability': 0.7, 'luxury': 0.95},
                'polyester': {'softness': 0.6, 'durability': 0.8, 'breathability': 0.4, 'luxury': 0.3}
            }
            
            # Encode each material
            material_vectors = []
            for material in material_preferences:
                material_lower = material.lower()
                if material_lower in material_properties:
                    props = material_properties[material_lower]
                    material_vector = [
                        props['softness'],
                        props['durability'], 
                        props['breathability'],
                        props['luxury']
                    ]
                    
                    # Add texture and appearance features
                    texture_features = await self._get_material_texture_features(material_lower)
                    material_vector.extend(texture_features)
                    
                    material_vectors.append(material_vector)
                else:
                    # Unknown material - use neutral values
                    material_vectors.append([0.5] * 8)  # 4 properties + 4 texture features
            
            if material_vectors:
                # Combine material vectors
                combined_vector = np.mean(material_vectors, axis=0)
                
                # Pad to standard embedding size
                target_size = 512
                if len(combined_vector) < target_size:
                    padding = [0.0] * (target_size - len(combined_vector))
                    combined_vector = np.concatenate([combined_vector, padding])
                
                return combined_vector[:target_size].tolist()
            else:
                return [0.0] * 512
                
        except Exception as e:
            logger.error(f"Failed to encode materials: {e}")
            return [0.0] * 512
    
    async def _download_and_preprocess_image(self, image_url: str) -> Image.Image:
        """Download and preprocess image from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30.0)
                response.raise_for_status()
                
                # Convert to PIL Image
                image_data = io.BytesIO(response.content)
                image = Image.open(image_data)
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                return image
                
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            # Return a placeholder image
            return Image.new('RGB', (224, 224), color='white')
    
    async def _preprocess_sketch(self, sketch: Image.Image) -> Image.Image:
        """Apply sketch-specific preprocessing."""
        try:
            # Convert to grayscale for sketch processing
            if sketch.mode != 'L':
                sketch_gray = sketch.convert('L')
            else:
                sketch_gray = sketch
            
            # Enhance contrast for better feature extraction
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(sketch_gray)
            sketch_enhanced = enhancer.enhance(1.5)
            
            # Convert back to RGB for CLIP compatibility
            sketch_rgb = sketch_enhanced.convert('RGB')
            
            return sketch_rgb
            
        except Exception as e:
            logger.error(f"Failed to preprocess sketch: {e}")
            return sketch
    
    async def _color_to_vector(self, color: str) -> np.ndarray:
        """Convert color name or hex code to numerical vector."""
        try:
            # Color name to RGB mapping
            color_map = {
                'red': [255, 0, 0], 'green': [0, 255, 0], 'blue': [0, 0, 255],
                'black': [0, 0, 0], 'white': [255, 255, 255], 'gray': [128, 128, 128],
                'yellow': [255, 255, 0], 'orange': [255, 165, 0], 'purple': [128, 0, 128],
                'pink': [255, 192, 203], 'brown': [165, 42, 42], 'beige': [245, 245, 220],
                'navy': [0, 0, 128], 'maroon': [128, 0, 0], 'teal': [0, 128, 128],
                'olive': [128, 128, 0], 'lime': [0, 255, 0], 'aqua': [0, 255, 255],
                'silver': [192, 192, 192], 'gold': [255, 215, 0]
            }
            
            color_lower = color.lower()
            
            if color_lower in color_map:
                rgb = color_map[color_lower]
            elif color.startswith('#'):
                # Hex color code
                hex_color = color[1:]
                rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
            else:
                # Default to neutral gray
                rgb = [128, 128, 128]
            
            # Normalize RGB to 0-1 range
            rgb_normalized = [c / 255.0 for c in rgb]
            
            # Convert to HSV for additional features
            hsv = self._rgb_to_hsv(rgb_normalized)
            
            # Combine RGB and HSV
            color_vector = np.array(rgb_normalized + hsv)
            
            return color_vector
            
        except Exception as e:
            logger.error(f"Failed to convert color {color}: {e}")
            return np.array([0.5, 0.5, 0.5, 0.0, 0.0, 0.5])  # Neutral gray
    
    def _rgb_to_hsv(self, rgb: List[float]) -> List[float]:
        """Convert RGB to HSV color space."""
        r, g, b = rgb
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Hue
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360
        
        # Saturation
        s = 0 if max_val == 0 else diff / max_val
        
        # Value
        v = max_val
        
        return [h / 360.0, s, v]  # Normalize hue to 0-1
    
    async def _calculate_color_harmony(self, color_palette: List[str]) -> np.ndarray:
        """Calculate color harmony features for the palette."""
        try:
            if len(color_palette) < 2:
                return np.array([0.5, 0.5, 0.5, 0.5])  # Neutral harmony
            
            # Convert all colors to vectors
            color_vectors = []
            for color in color_palette:
                color_vector = await self._color_to_vector(color)
                color_vectors.append(color_vector)
            
            color_array = np.array(color_vectors)
            
            # Calculate harmony metrics
            # 1. Color diversity (variance in hue)
            hues = color_array[:, 3]  # Hue is the 4th element
            hue_diversity = np.var(hues)
            
            # 2. Saturation consistency
            saturations = color_array[:, 4]  # Saturation is the 5th element
            saturation_consistency = 1.0 - np.var(saturations)
            
            # 3. Value (brightness) balance
            values = color_array[:, 5]  # Value is the 6th element
            value_balance = 1.0 - np.var(values)
            
            # 4. Overall coherence (how well colors work together)
            coherence = (saturation_consistency + value_balance) / 2.0
            
            harmony_features = np.array([
                min(1.0, hue_diversity),
                max(0.0, saturation_consistency),
                max(0.0, value_balance),
                max(0.0, coherence)
            ])
            
            return harmony_features
            
        except Exception as e:
            logger.error(f"Failed to calculate color harmony: {e}")
            return np.array([0.5, 0.5, 0.5, 0.5])
    
    async def _get_material_texture_features(self, material: str) -> List[float]:
        """Get texture features for a material."""
        # Texture property mappings
        texture_properties = {
            'cotton': [0.6, 0.4, 0.7, 0.5],  # [roughness, shine, flexibility, weight]
            'silk': [0.2, 0.9, 0.8, 0.3],
            'wool': [0.7, 0.3, 0.6, 0.7],
            'linen': [0.8, 0.2, 0.5, 0.6],
            'leather': [0.5, 0.6, 0.4, 0.8],
            'denim': [0.9, 0.1, 0.3, 0.8],
            'cashmere': [0.1, 0.4, 0.9, 0.4],
            'polyester': [0.4, 0.5, 0.7, 0.5]
        }
        
        return texture_properties.get(material, [0.5, 0.5, 0.5, 0.5])
    
    # Mock implementations for development
    async def _mock_text_encoding(self, text_prompt: str) -> List[float]:
        """Mock text encoding for development."""
        # Simple hash-based encoding for consistency
        text_hash = hash(text_prompt) % 1000000
        np.random.seed(text_hash)
        
        # Generate consistent embedding based on text content
        embedding = np.random.normal(0, 1, 512).tolist()
        
        # Add some semantic features based on keywords
        fashion_keywords = {
            'minimalist': [0.8, -0.5, 0.3],
            'luxury': [0.6, 0.8, 0.4],
            'casual': [-0.3, -0.2, 0.7],
            'professional': [0.4, 0.6, -0.2],
            'vintage': [-0.6, 0.3, -0.4],
            'modern': [0.7, 0.2, 0.5]
        }
        
        for keyword, features in fashion_keywords.items():
            if keyword in text_prompt.lower():
                for i, feature in enumerate(features):
                    if i < len(embedding):
                        embedding[i] += feature * 0.3
        
        return embedding
    
    async def _mock_image_encoding(self, image: Optional[Image.Image]) -> List[float]:
        """Mock image encoding for development."""
        if image:
            # Use image dimensions and basic properties for consistent encoding
            width, height = image.size
            seed = (width * height) % 1000000
        else:
            seed = 42
        
        np.random.seed(seed)
        return np.random.normal(0, 1, 512).tolist()
    
    async def _mock_sketch_encoding(self, sketch: Optional[Image.Image]) -> List[float]:
        """Mock sketch encoding for development."""
        if sketch:
            # Use sketch properties for encoding
            width, height = sketch.size
            seed = (width + height) % 1000000
        else:
            seed = 123
        
        np.random.seed(seed)
        # Sketch embeddings might be slightly different from regular images
        embedding = np.random.normal(0, 0.8, 512).tolist()
        
        # Add sketch-specific features
        embedding[0] += 0.5  # Indicate this is a sketch
        
        return embedding