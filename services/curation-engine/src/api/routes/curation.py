"""
Main curation API routes for Curation Engine
Handles quality assessment, recommendations, and content curation
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import base64
from PIL import Image
import io

from ...main import get_quality_assessor, get_recommendation_engine
from ...services.quality_assessor import QualityAssessor
from ...services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class QualityAssessmentRequest(BaseModel):
    image_data: Optional[str] = Field(default=None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(default=None, description="URL to image")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class UserRecommendationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    num_recommendations: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    style_preferences: Optional[List[str]] = Field(default=None, description="Style preferences")
    exclude_seen: bool = Field(default=True, description="Exclude previously seen items")


class ItemRecommendationRequest(BaseModel):
    item_id: str = Field(..., description="Item identifier")
    num_recommendations: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    recommendation_type: str = Field(default="similar", description="Type: similar, complementary, alternative")


class TrendingRequest(BaseModel):
    time_window: str = Field(default="week", description="Time window: day, week, month")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    num_recommendations: int = Field(default=20, ge=1, le=100, description="Number of trending items")


class UserInteractionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    item_id: str = Field(..., description="Item identifier")
    interaction_type: str = Field(..., description="Type: view, like, purchase, share, etc.")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


@router.post("/assess-quality")
async def assess_content_quality(
    request: QualityAssessmentRequest = None,
    file: UploadFile = File(None),
    quality_assessor: QualityAssessor = Depends(get_quality_assessor)
) -> Dict[str, Any]:
    """
    Assess the quality of fashion content (image).
    
    Accepts either file upload, base64 data, or image URL.
    Returns comprehensive quality metrics and recommendations.
    """
    try:
        image = None
        
        # Handle different input methods
        if file:
            # File upload
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            
        elif request and request.image_data:
            # Base64 encoded image
            try:
                image_bytes = base64.b64decode(request.image_data)
                image = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")
                
        elif request and request.image_url:
            # Image URL
            raise HTTPException(status_code=501, detail="URL-based assessment not yet implemented")
            
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Perform quality assessment
        context = request.context if request else None
        assessment_result = await quality_assessor.assess_image_quality(image, context)
        
        return {
            "status": "success",
            "assessment": assessment_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.post("/recommendations/user")
async def get_user_recommendations(
    request: UserRecommendationRequest,
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> Dict[str, Any]:
    """
    Get personalized recommendations for a user.
    
    Uses hybrid recommendation approach combining collaborative filtering,
    content-based filtering, popularity, and trend analysis.
    """
    try:
        recommendations = await recommendation_engine.get_user_recommendations(
            user_id=request.user_id,
            num_recommendations=request.num_recommendations,
            categories=request.categories,
            style_preferences=request.style_preferences,
            exclude_seen=request.exclude_seen
        )
        
        return {
            "status": "success",
            "data": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"User recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.post("/recommendations/item")
async def get_item_recommendations(
    request: ItemRecommendationRequest,
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> Dict[str, Any]:
    """
    Get item-to-item recommendations.
    
    Supports similar items, complementary items, and alternatives.
    """
    try:
        if request.recommendation_type not in ["similar", "complementary", "alternative"]:
            raise HTTPException(
                status_code=400, 
                detail="recommendation_type must be 'similar', 'complementary', or 'alternative'"
            )
        
        recommendations = await recommendation_engine.get_item_recommendations(
            item_id=request.item_id,
            num_recommendations=request.num_recommendations,
            recommendation_type=request.recommendation_type
        )
        
        return {
            "status": "success",
            "data": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Item recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.post("/recommendations/trending")
async def get_trending_recommendations(
    request: TrendingRequest,
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> Dict[str, Any]:
    """
    Get trending items and recommendations.
    
    Analyzes trends over specified time windows and returns
    items gaining popularity with trend explanations.
    """
    try:
        if request.time_window not in ["day", "week", "month"]:
            raise HTTPException(
                status_code=400,
                detail="time_window must be 'day', 'week', or 'month'"
            )
        
        trending = await recommendation_engine.get_trending_recommendations(
            time_window=request.time_window,
            categories=request.categories,
            num_recommendations=request.num_recommendations
        )
        
        return {
            "status": "success",
            "data": trending,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trending analysis failed: {str(e)}")


@router.post("/interactions")
async def record_user_interaction(
    request: UserInteractionRequest,
    background_tasks: BackgroundTasks,
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> Dict[str, Any]:
    """
    Record user interaction for recommendation learning.
    
    Updates user profiles and invalidates caches to improve
    future recommendations based on user behavior.
    """
    try:
        # Validate interaction type
        valid_interactions = ["view", "like", "purchase", "share", "add_to_cart", "click", "favorite"]
        if request.interaction_type not in valid_interactions:
            raise HTTPException(
                status_code=400,
                detail=f"interaction_type must be one of: {', '.join(valid_interactions)}"
            )
        
        # Record interaction asynchronously
        success = await recommendation_engine.update_user_interaction(
            user_id=request.user_id,
            item_id=request.item_id,
            interaction_type=request.interaction_type,
            context=request.context
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to record interaction")
        
        return {
            "status": "success",
            "message": "Interaction recorded successfully",
            "interaction": {
                "user_id": request.user_id,
                "item_id": request.item_id,
                "interaction_type": request.interaction_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record interaction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")


@router.get("/user/{user_id}/profile")
async def get_user_curation_profile(
    user_id: str,
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
) -> Dict[str, Any]:
    """
    Get user's curation profile including preferences and statistics.
    
    Returns user preferences, interaction history summary,
    and personalization insights.
    """
    try:
        # Get user profile (this would typically come from the recommendation engine)
        profile = await recommendation_engine._get_user_profile(user_id)
        history = await recommendation_engine._get_user_history(user_id)
        
        # Calculate statistics
        interaction_stats = {}
        for interaction in history:
            interaction_type = interaction.get("interaction_type", "unknown")
            interaction_stats[interaction_type] = interaction_stats.get(interaction_type, 0) + 1
        
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "profile": profile,
                "interaction_statistics": interaction_stats,
                "total_interactions": len(history),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")


@router.get("/analytics/quality-stats")
async def get_quality_analytics(
    time_window: str = "week",
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get analytics on content quality assessments.
    
    Returns statistics on quality scores, common issues,
    and improvement trends over time.
    """
    try:
        # This would typically query assessment history from a database
        # For now, return mock analytics
        
        analytics = {
            "time_window": time_window,
            "categories": categories,
            "quality_distribution": {
                "excellent": 15,
                "very_good": 25,
                "good": 35,
                "fair": 20,
                "poor": 5
            },
            "average_scores": {
                "overall": 0.72,
                "visual_quality": 0.75,
                "aesthetic_appeal": 0.68,
                "fashion_relevance": 0.78,
                "technical_quality": 0.70,
                "brand_alignment": 0.69
            },
            "common_issues": [
                {"issue": "Low resolution", "frequency": 0.35},
                {"issue": "Poor lighting", "frequency": 0.28},
                {"issue": "Composition issues", "frequency": 0.22},
                {"issue": "Color balance", "frequency": 0.18}
            ],
            "trend": "improving",
            "total_assessments": 1250
        }
        
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.get("/analytics/recommendation-stats")
async def get_recommendation_analytics(
    time_window: str = "week"
) -> Dict[str, Any]:
    """
    Get analytics on recommendation performance.
    
    Returns metrics on recommendation accuracy, user engagement,
    and algorithm performance.
    """
    try:
        # This would typically query recommendation performance data
        # For now, return mock analytics
        
        analytics = {
            "time_window": time_window,
            "algorithm_performance": {
                "collaborative": {"accuracy": 0.78, "coverage": 0.65},
                "content_based": {"accuracy": 0.72, "coverage": 0.85},
                "popularity": {"accuracy": 0.68, "coverage": 0.95},
                "trend_based": {"accuracy": 0.75, "coverage": 0.45}
            },
            "user_engagement": {
                "click_through_rate": 0.12,
                "conversion_rate": 0.03,
                "average_session_time": 8.5,
                "return_user_rate": 0.68
            },
            "recommendation_metrics": {
                "total_recommendations": 15420,
                "unique_users": 3250,
                "average_recommendations_per_user": 4.7,
                "user_satisfaction_score": 4.2
            },
            "trending_categories": [
                {"category": "dresses", "growth": 0.25},
                {"category": "accessories", "growth": 0.18},
                {"category": "shoes", "growth": 0.15}
            ]
        }
        
        return {
            "status": "success",
            "data": analytics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendation analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@router.post("/batch/quality-assessment")
async def batch_quality_assessment(
    background_tasks: BackgroundTasks,
    item_ids: List[str] = Field(..., description="List of item IDs to assess"),
    priority: int = Field(default=0, description="Processing priority"),
    quality_assessor: QualityAssessor = Depends(get_quality_assessor)
) -> Dict[str, Any]:
    """
    Submit batch quality assessment job.
    
    Processes multiple items for quality assessment in the background.
    Returns job ID for tracking progress.
    """
    try:
        if len(item_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 items per batch")
        
        # This would typically create a background job
        # For now, return a mock job response
        job_id = f"batch_qa_{int(datetime.utcnow().timestamp())}"
        
        return {
            "status": "success",
            "job_id": job_id,
            "message": f"Batch quality assessment job submitted for {len(item_ids)} items",
            "estimated_completion": "15-30 minutes",
            "items_count": len(item_ids),
            "priority": priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/batch/job/{job_id}")
async def get_batch_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a batch processing job.
    
    Returns current status, progress, and results if completed.
    """
    try:
        # This would typically query job status from a job queue
        # For now, return mock status
        
        status = {
            "job_id": job_id,
            "status": "completed",
            "progress": {
                "total_items": 50,
                "processed_items": 50,
                "failed_items": 2,
                "percentage": 100
            },
            "results": {
                "average_quality_score": 0.74,
                "quality_distribution": {
                    "excellent": 8,
                    "very_good": 15,
                    "good": 18,
                    "fair": 7,
                    "poor": 2
                }
            },
            "created_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T10:25:00Z",
            "processing_time": 1500  # seconds
        }
        
        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/categories")
async def get_fashion_categories() -> Dict[str, Any]:
    """
    Get available fashion categories for filtering and recommendations.
    
    Returns hierarchical list of fashion categories with metadata.
    """
    try:
        categories = {
            "clothing": {
                "tops": ["t-shirts", "shirts", "blouses", "sweaters", "hoodies"],
                "bottoms": ["jeans", "pants", "shorts", "skirts", "leggings"],
                "dresses": ["casual", "formal", "cocktail", "maxi", "mini"],
                "outerwear": ["jackets", "coats", "blazers", "cardigans"],
                "activewear": ["sportswear", "yoga", "running", "gym"]
            },
            "accessories": {
                "bags": ["handbags", "backpacks", "clutches", "totes"],
                "jewelry": ["necklaces", "earrings", "bracelets", "rings"],
                "watches": ["casual", "formal", "sport", "luxury"],
                "sunglasses": ["aviator", "wayfarer", "cat-eye", "round"]
            },
            "footwear": {
                "casual": ["sneakers", "loafers", "flats"],
                "formal": ["heels", "oxfords", "dress-shoes"],
                "athletic": ["running", "training", "hiking"],
                "boots": ["ankle", "knee-high", "combat", "chelsea"]
            }
        }
        
        return {
            "status": "success",
            "data": {
                "categories": categories,
                "total_categories": sum(len(subcats) if isinstance(subcats, dict) else 1 
                                     for cats in categories.values() 
                                     for subcats in cats.values()),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/styles")
async def get_fashion_styles() -> Dict[str, Any]:
    """
    Get available fashion styles for preferences and filtering.
    
    Returns list of fashion styles with descriptions.
    """
    try:
        styles = {
            "casual": "Relaxed, everyday wear suitable for informal occasions",
            "formal": "Professional and elegant attire for business and special events",
            "sporty": "Athletic and active wear designed for movement and comfort",
            "elegant": "Sophisticated and refined pieces with attention to detail",
            "bohemian": "Free-spirited, artistic style with flowing fabrics and patterns",
            "minimalist": "Clean, simple designs with neutral colors and classic cuts",
            "vintage": "Retro-inspired pieces from past decades with timeless appeal",
            "modern": "Contemporary designs with current trends and innovative cuts",
            "edgy": "Bold, unconventional pieces that make a statement",
            "romantic": "Feminine, soft designs with delicate details and flowing silhouettes",
            "preppy": "Classic, collegiate-inspired style with clean lines",
            "grunge": "Alternative style with distressed textures and darker aesthetics"
        }
        
        return {
            "status": "success",
            "data": {
                "styles": styles,
                "total_styles": len(styles),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get styles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get styles: {str(e)}")