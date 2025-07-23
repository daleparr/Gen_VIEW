"""
Quality Assessor Service for Curation Engine
Evaluates fashion content quality using multiple AI models and metrics
"""

import asyncio
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional, Tuple, Union
import cv2
from PIL import Image
import clip
from transformers import pipeline
from sklearn.metrics.pairwise import cosine_similarity
import json

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class QualityAssessor:
    """
    AI-powered quality assessment for fashion content.
    Evaluates visual quality, aesthetic appeal, and fashion relevance.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model storage
        self.clip_model = None
        self.clip_processor = None
        self.aesthetic_model = None
        self.fashion_classifier = None
        
        # Quality metrics
        self.quality_weights = {
            "visual_quality": 0.3,
            "aesthetic_appeal": 0.25,
            "fashion_relevance": 0.2,
            "technical_quality": 0.15,
            "brand_alignment": 0.1
        }
        
        logger.info(f"Quality Assessor initialized on device: {self.device}")
    
    async def initialize(self):
        """Initialize the quality assessment models."""
        try:
            logger.info("Initializing Quality Assessor...")
            
            # Load CLIP model for fashion understanding
            self.clip_model, self.clip_processor = clip.load("ViT-B/32", device=self.device)
            logger.info("CLIP model loaded")
            
            # Initialize aesthetic quality pipeline
            self.aesthetic_model = pipeline(
                "image-classification",
                model="cafeai/cafe_aesthetic",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Aesthetic model loaded")
            
            # Initialize fashion classification pipeline
            self.fashion_classifier = pipeline(
                "image-classification",
                model="patrickjohncyh/fashion-clip",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Fashion classifier loaded")
            
            logger.info("Quality Assessor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Quality Assessor: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Quality Assessor...")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    async def assess_image_quality(
        self,
        image: Union[np.ndarray, Image.Image, str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive quality assessment for fashion images.
        
        Args:
            image: Image as numpy array, PIL Image, or file path
            context: Additional context (brand, category, target audience, etc.)
            
        Returns:
            Quality assessment results with scores and explanations
        """
        try:
            # Normalize image input
            pil_image = self._normalize_image_input(image)
            
            # Run all quality assessments in parallel
            results = await asyncio.gather(
                self._assess_visual_quality(pil_image),
                self._assess_aesthetic_appeal(pil_image),
                self._assess_fashion_relevance(pil_image, context),
                self._assess_technical_quality(pil_image),
                self._assess_brand_alignment(pil_image, context),
                return_exceptions=True
            )
            
            # Process results
            visual_quality = results[0] if not isinstance(results[0], Exception) else {"score": 0.5, "details": {}}
            aesthetic_appeal = results[1] if not isinstance(results[1], Exception) else {"score": 0.5, "details": {}}
            fashion_relevance = results[2] if not isinstance(results[2], Exception) else {"score": 0.5, "details": {}}
            technical_quality = results[3] if not isinstance(results[3], Exception) else {"score": 0.5, "details": {}}
            brand_alignment = results[4] if not isinstance(results[4], Exception) else {"score": 0.5, "details": {}}
            
            # Calculate overall quality score
            overall_score = (
                visual_quality["score"] * self.quality_weights["visual_quality"] +
                aesthetic_appeal["score"] * self.quality_weights["aesthetic_appeal"] +
                fashion_relevance["score"] * self.quality_weights["fashion_relevance"] +
                technical_quality["score"] * self.quality_weights["technical_quality"] +
                brand_alignment["score"] * self.quality_weights["brand_alignment"]
            )
            
            # Generate quality category
            quality_category = self._categorize_quality(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                visual_quality, aesthetic_appeal, fashion_relevance, 
                technical_quality, brand_alignment
            )
            
            return {
                "overall_score": round(overall_score, 3),
                "quality_category": quality_category,
                "component_scores": {
                    "visual_quality": visual_quality,
                    "aesthetic_appeal": aesthetic_appeal,
                    "fashion_relevance": fashion_relevance,
                    "technical_quality": technical_quality,
                    "brand_alignment": brand_alignment
                },
                "recommendations": recommendations,
                "metadata": {
                    "image_size": pil_image.size,
                    "assessment_timestamp": asyncio.get_event_loop().time(),
                    "context": context or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to assess image quality: {e}")
            raise
    
    async def _assess_visual_quality(self, image: Image.Image) -> Dict[str, Any]:
        """Assess visual quality metrics like sharpness, exposure, composition."""
        try:
            # Convert to numpy for analysis
            img_array = np.array(image)
            
            # Sharpness (Laplacian variance)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(sharpness / 1000.0, 1.0)  # Normalize
            
            # Exposure (histogram analysis)
            hist = cv2.calcHist([img_array], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            exposure_score = self._analyze_exposure(hist)
            
            # Composition (rule of thirds, symmetry)
            composition_score = self._analyze_composition(img_array)
            
            # Color balance
            color_balance_score = self._analyze_color_balance(img_array)
            
            # Overall visual quality
            visual_score = (
                sharpness_score * 0.3 +
                exposure_score * 0.3 +
                composition_score * 0.2 +
                color_balance_score * 0.2
            )
            
            return {
                "score": round(visual_score, 3),
                "details": {
                    "sharpness": round(sharpness_score, 3),
                    "exposure": round(exposure_score, 3),
                    "composition": round(composition_score, 3),
                    "color_balance": round(color_balance_score, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Visual quality assessment failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    async def _assess_aesthetic_appeal(self, image: Image.Image) -> Dict[str, Any]:
        """Assess aesthetic appeal using AI models."""
        try:
            # Use aesthetic model
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.aesthetic_model, image
            )
            
            # Extract aesthetic score
            aesthetic_score = 0.5  # Default
            if result and len(result) > 0:
                # Assuming the model returns aesthetic/not_aesthetic labels
                for item in result:
                    if item['label'].lower() in ['aesthetic', 'beautiful', 'high_quality']:
                        aesthetic_score = item['score']
                        break
                    elif item['label'].lower() in ['not_aesthetic', 'ugly', 'low_quality']:
                        aesthetic_score = 1.0 - item['score']
                        break
            
            return {
                "score": round(aesthetic_score, 3),
                "details": {
                    "model_results": result[:3] if result else [],
                    "confidence": round(aesthetic_score, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Aesthetic assessment failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    async def _assess_fashion_relevance(
        self, 
        image: Image.Image, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess fashion relevance and category alignment."""
        try:
            # Use fashion classifier
            fashion_result = await asyncio.get_event_loop().run_in_executor(
                None, self.fashion_classifier, image
            )
            
            # Use CLIP for fashion understanding
            clip_result = await self._clip_fashion_analysis(image, context)
            
            # Combine results
            fashion_score = 0.5
            if fashion_result and len(fashion_result) > 0:
                # Get highest confidence fashion-related prediction
                fashion_score = max(
                    item['score'] for item in fashion_result 
                    if self._is_fashion_category(item['label'])
                )
            
            # Boost score if CLIP agrees
            if clip_result["is_fashion"]:
                fashion_score = min(fashion_score * 1.2, 1.0)
            
            return {
                "score": round(fashion_score, 3),
                "details": {
                    "fashion_categories": fashion_result[:3] if fashion_result else [],
                    "clip_analysis": clip_result,
                    "is_fashion_relevant": fashion_score > 0.6
                }
            }
            
        except Exception as e:
            logger.error(f"Fashion relevance assessment failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    async def _assess_technical_quality(self, image: Image.Image) -> Dict[str, Any]:
        """Assess technical aspects like resolution, compression artifacts."""
        try:
            img_array = np.array(image)
            width, height = image.size
            
            # Resolution score
            total_pixels = width * height
            resolution_score = min(total_pixels / (1024 * 1024), 1.0)  # Normalize to 1MP
            
            # Compression artifacts (JPEG quality estimation)
            compression_score = self._estimate_jpeg_quality(img_array)
            
            # Noise level
            noise_score = self._estimate_noise_level(img_array)
            
            # Dynamic range
            dynamic_range_score = self._analyze_dynamic_range(img_array)
            
            technical_score = (
                resolution_score * 0.3 +
                compression_score * 0.3 +
                noise_score * 0.2 +
                dynamic_range_score * 0.2
            )
            
            return {
                "score": round(technical_score, 3),
                "details": {
                    "resolution": f"{width}x{height}",
                    "resolution_score": round(resolution_score, 3),
                    "compression_quality": round(compression_score, 3),
                    "noise_level": round(1.0 - noise_score, 3),  # Invert for display
                    "dynamic_range": round(dynamic_range_score, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Technical quality assessment failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    async def _assess_brand_alignment(
        self, 
        image: Image.Image, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess alignment with brand guidelines and style."""
        try:
            if not context or "brand_id" not in context:
                return {
                    "score": 0.5,
                    "details": {"message": "No brand context provided"}
                }
            
            brand_id = context["brand_id"]
            
            # Use CLIP to analyze brand alignment
            brand_alignment = await self._clip_brand_analysis(image, brand_id, context)
            
            return {
                "score": round(brand_alignment["score"], 3),
                "details": brand_alignment["details"]
            }
            
        except Exception as e:
            logger.error(f"Brand alignment assessment failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    async def _clip_fashion_analysis(
        self, 
        image: Image.Image, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use CLIP for fashion-specific analysis."""
        try:
            # Fashion-related prompts
            fashion_prompts = [
                "a fashionable clothing item",
                "a stylish garment",
                "a trendy fashion piece",
                "a high-quality fashion product",
                "professional fashion photography"
            ]
            
            non_fashion_prompts = [
                "not fashion related",
                "random object",
                "low quality image",
                "blurry photograph"
            ]
            
            # Encode image and prompts
            image_input = self.clip_processor(images=image, return_tensors="pt").to(self.device)
            text_inputs = clip.tokenize(fashion_prompts + non_fashion_prompts).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input['pixel_values'])
                text_features = self.clip_model.encode_text(text_inputs)
                
                # Calculate similarities
                similarities = torch.cosine_similarity(
                    image_features, text_features, dim=1
                ).cpu().numpy()
            
            # Analyze results
            fashion_scores = similarities[:len(fashion_prompts)]
            non_fashion_scores = similarities[len(fashion_prompts):]
            
            avg_fashion_score = np.mean(fashion_scores)
            avg_non_fashion_score = np.mean(non_fashion_scores)
            
            is_fashion = avg_fashion_score > avg_non_fashion_score
            confidence = abs(avg_fashion_score - avg_non_fashion_score)
            
            return {
                "is_fashion": is_fashion,
                "confidence": float(confidence),
                "fashion_score": float(avg_fashion_score),
                "non_fashion_score": float(avg_non_fashion_score)
            }
            
        except Exception as e:
            logger.error(f"CLIP fashion analysis failed: {e}")
            return {"is_fashion": True, "confidence": 0.5, "error": str(e)}
    
    async def _clip_brand_analysis(
        self, 
        image: Image.Image, 
        brand_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze brand alignment using CLIP."""
        try:
            # This would typically load brand-specific style guidelines
            # For now, we'll use generic brand alignment prompts
            brand_style = context.get("brand_style", "modern and elegant")
            target_audience = context.get("target_audience", "fashion-conscious consumers")
            
            brand_prompts = [
                f"a {brand_style} fashion item",
                f"clothing for {target_audience}",
                f"high-end fashion photography",
                f"professional product photography"
            ]
            
            # Encode and analyze
            image_input = self.clip_processor(images=image, return_tensors="pt").to(self.device)
            text_inputs = clip.tokenize(brand_prompts).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_input['pixel_values'])
                text_features = self.clip_model.encode_text(text_inputs)
                
                similarities = torch.cosine_similarity(
                    image_features, text_features, dim=1
                ).cpu().numpy()
            
            brand_alignment_score = np.mean(similarities)
            
            return {
                "score": float(brand_alignment_score),
                "details": {
                    "brand_id": brand_id,
                    "style_alignment": float(similarities[0]),
                    "audience_alignment": float(similarities[1]) if len(similarities) > 1 else 0.5,
                    "photography_quality": float(similarities[2]) if len(similarities) > 2 else 0.5
                }
            }
            
        except Exception as e:
            logger.error(f"Brand alignment analysis failed: {e}")
            return {"score": 0.5, "details": {"error": str(e)}}
    
    def _normalize_image_input(self, image: Union[np.ndarray, Image.Image, str]) -> Image.Image:
        """Normalize different image input formats to PIL Image."""
        if isinstance(image, str):
            return Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            return Image.fromarray(image).convert("RGB")
        elif isinstance(image, Image.Image):
            return image.convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _analyze_exposure(self, hist: np.ndarray) -> float:
        """Analyze image exposure from histogram."""
        # Simplified exposure analysis
        total_pixels = np.sum(hist)
        
        # Check for clipping
        dark_pixels = np.sum(hist[:50])  # Very dark
        bright_pixels = np.sum(hist[200:])  # Very bright
        
        dark_ratio = dark_pixels / total_pixels
        bright_ratio = bright_pixels / total_pixels
        
        # Good exposure has minimal clipping
        exposure_score = 1.0 - (dark_ratio + bright_ratio) * 2
        return max(0.0, min(1.0, exposure_score))
    
    def _analyze_composition(self, img_array: np.ndarray) -> float:
        """Analyze image composition."""
        # Simplified composition analysis
        # In a full implementation, this would use more sophisticated algorithms
        height, width = img_array.shape[:2]
        
        # Rule of thirds analysis (simplified)
        third_h, third_w = height // 3, width // 3
        
        # Check for interesting content at rule of thirds points
        interest_points = [
            (third_w, third_h), (2 * third_w, third_h),
            (third_w, 2 * third_h), (2 * third_w, 2 * third_h)
        ]
        
        # This is a placeholder - real implementation would analyze edges, contrast, etc.
        composition_score = 0.7  # Default reasonable score
        
        return composition_score
    
    def _analyze_color_balance(self, img_array: np.ndarray) -> float:
        """Analyze color balance."""
        # Calculate mean values for each channel
        mean_r = np.mean(img_array[:, :, 0])
        mean_g = np.mean(img_array[:, :, 1])
        mean_b = np.mean(img_array[:, :, 2])
        
        # Good color balance has similar channel means
        max_diff = max(abs(mean_r - mean_g), abs(mean_g - mean_b), abs(mean_r - mean_b))
        balance_score = 1.0 - (max_diff / 255.0)
        
        return max(0.0, min(1.0, balance_score))
    
    def _estimate_jpeg_quality(self, img_array: np.ndarray) -> float:
        """Estimate JPEG compression quality."""
        # Simplified quality estimation based on high-frequency content
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply high-pass filter
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        high_freq = cv2.filter2D(gray, -1, kernel)
        
        # Calculate variance of high-frequency content
        hf_variance = np.var(high_freq)
        
        # Normalize to 0-1 range (higher variance = better quality)
        quality_score = min(hf_variance / 10000.0, 1.0)
        
        return quality_score
    
    def _estimate_noise_level(self, img_array: np.ndarray) -> float:
        """Estimate image noise level."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Use Laplacian to estimate noise
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise_variance = laplacian.var()
        
        # Convert to quality score (lower noise = higher score)
        noise_score = 1.0 / (1.0 + noise_variance / 1000.0)
        
        return max(0.0, min(1.0, noise_score))
    
    def _analyze_dynamic_range(self, img_array: np.ndarray) -> float:
        """Analyze dynamic range of the image."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Find actual min and max values with significant content
        cumsum = np.cumsum(hist)
        total = cumsum[-1]
        
        # Find 1% and 99% percentiles
        min_val = np.where(cumsum > total * 0.01)[0][0]
        max_val = np.where(cumsum > total * 0.99)[0][0]
        
        # Dynamic range score
        range_score = (max_val - min_val) / 255.0
        
        return max(0.0, min(1.0, range_score))
    
    def _is_fashion_category(self, label: str) -> bool:
        """Check if a label represents a fashion category."""
        fashion_keywords = [
            "shirt", "dress", "pants", "skirt", "jacket", "coat", "shoe", "boot",
            "hat", "bag", "accessory", "jewelry", "clothing", "apparel", "fashion",
            "style", "garment", "outfit", "wear", "textile"
        ]
        
        return any(keyword in label.lower() for keyword in fashion_keywords)
    
    def _categorize_quality(self, score: float) -> str:
        """Categorize quality score into descriptive categories."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Very Good"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        elif score >= 0.5:
            return "Poor"
        else:
            return "Very Poor"
    
    def _generate_recommendations(self, *component_scores) -> List[str]:
        """Generate improvement recommendations based on component scores."""
        recommendations = []
        
        visual_quality, aesthetic_appeal, fashion_relevance, technical_quality, brand_alignment = component_scores
        
        if visual_quality["score"] < 0.7:
            recommendations.append("Improve visual quality: focus on sharpness, exposure, and composition")
        
        if aesthetic_appeal["score"] < 0.7:
            recommendations.append("Enhance aesthetic appeal: consider styling, lighting, and visual harmony")
        
        if fashion_relevance["score"] < 0.7:
            recommendations.append("Increase fashion relevance: ensure content aligns with fashion categories")
        
        if technical_quality["score"] < 0.7:
            recommendations.append("Improve technical quality: use higher resolution and reduce compression")
        
        if brand_alignment["score"] < 0.7:
            recommendations.append("Better brand alignment: ensure consistency with brand style guidelines")
        
        if not recommendations:
            recommendations.append("Quality is good overall - consider minor refinements for excellence")
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the quality assessor."""
        try:
            health = {
                'status': 'healthy',
                'device': str(self.device),
                'models_loaded': {
                    'clip_model': self.clip_model is not None,
                    'aesthetic_model': self.aesthetic_model is not None,
                    'fashion_classifier': self.fashion_classifier is not None
                },
                'cuda_available': torch.cuda.is_available()
            }
            
            if torch.cuda.is_available():
                health['gpu_memory'] = {
                    'allocated': torch.cuda.memory_allocated(self.device),
                    'cached': torch.cuda.memory_reserved(self.device)
                }
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }