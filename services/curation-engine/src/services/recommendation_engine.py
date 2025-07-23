"""
Recommendation Engine Service for Curation Engine
Provides intelligent recommendations using collaborative filtering, content-based filtering,
and hybrid approaches with fashion-specific intelligence
"""

import asyncio
import logging
import numpy as np
import torch
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

from ..core.config import get_settings
from ..core.redis_client import get_redis_manager

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Advanced recommendation engine for fashion content and products.
    Combines multiple recommendation strategies with fashion domain expertise.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_manager = None
        
        # Recommendation models
        self.collaborative_model = None
        self.content_vectorizer = None
        self.hybrid_weights = {
            "collaborative": 0.4,
            "content_based": 0.3,
            "popularity": 0.15,
            "trend_based": 0.15
        }
        
        # Fashion-specific features
        self.fashion_categories = [
            "tops", "bottoms", "dresses", "outerwear", "shoes", 
            "accessories", "bags", "jewelry", "activewear", "formal"
        ]
        
        self.style_attributes = [
            "casual", "formal", "sporty", "elegant", "bohemian", "minimalist",
            "vintage", "modern", "edgy", "romantic", "preppy", "grunge"
        ]
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour
        self.batch_size = 100
        
        logger.info("Recommendation Engine initialized")
    
    async def initialize(self):
        """Initialize the recommendation engine."""
        try:
            logger.info("Initializing Recommendation Engine...")
            
            # Initialize Redis connection
            self.redis_manager = await get_redis_manager()
            
            # Initialize recommendation models
            await self._initialize_models()
            
            logger.info("Recommendation Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Recommendation Engine: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Recommendation Engine...")
        if self.redis_manager:
            await self.redis_manager.close()
    
    async def get_user_recommendations(
        self,
        user_id: str,
        num_recommendations: int = 10,
        categories: Optional[List[str]] = None,
        style_preferences: Optional[List[str]] = None,
        exclude_seen: bool = True
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations for a user.
        
        Args:
            user_id: User identifier
            num_recommendations: Number of recommendations to return
            categories: Filter by specific fashion categories
            style_preferences: User's style preferences
            exclude_seen: Whether to exclude previously seen items
            
        Returns:
            Personalized recommendations with scores and explanations
        """
        try:
            # Check cache first
            cache_key = f"user_rec:{user_id}:{num_recommendations}:{hash(str(categories))}"
            cached_result = await self._get_cached_recommendations(cache_key)
            if cached_result:
                return cached_result
            
            # Get user profile and history
            user_profile = await self._get_user_profile(user_id)
            user_history = await self._get_user_history(user_id)
            
            # Generate recommendations using hybrid approach
            recommendations = await asyncio.gather(
                self._collaborative_filtering(user_id, user_history, num_recommendations * 2),
                self._content_based_filtering(user_profile, categories, style_preferences, num_recommendations * 2),
                self._popularity_based_recommendations(categories, num_recommendations),
                self._trend_based_recommendations(categories, style_preferences, num_recommendations),
                return_exceptions=True
            )
            
            # Process results
            collab_recs = recommendations[0] if not isinstance(recommendations[0], Exception) else []
            content_recs = recommendations[1] if not isinstance(recommendations[1], Exception) else []
            popularity_recs = recommendations[2] if not isinstance(recommendations[2], Exception) else []
            trend_recs = recommendations[3] if not isinstance(recommendations[3], Exception) else []
            
            # Combine recommendations using hybrid approach
            final_recommendations = await self._combine_recommendations(
                collab_recs, content_recs, popularity_recs, trend_recs,
                user_history if exclude_seen else None,
                num_recommendations
            )
            
            # Add explanations and metadata
            enriched_recommendations = await self._enrich_recommendations(
                final_recommendations, user_profile, user_history
            )
            
            result = {
                "user_id": user_id,
                "recommendations": enriched_recommendations,
                "metadata": {
                    "algorithm": "hybrid",
                    "total_candidates": len(collab_recs) + len(content_recs) + len(popularity_recs) + len(trend_recs),
                    "filters_applied": {
                        "categories": categories,
                        "style_preferences": style_preferences,
                        "exclude_seen": exclude_seen
                    },
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            # Cache result
            await self._cache_recommendations(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user recommendations: {e}")
            raise
    
    async def get_item_recommendations(
        self,
        item_id: str,
        num_recommendations: int = 10,
        recommendation_type: str = "similar"
    ) -> Dict[str, Any]:
        """
        Get item-to-item recommendations.
        
        Args:
            item_id: Item identifier
            num_recommendations: Number of recommendations
            recommendation_type: 'similar', 'complementary', or 'alternative'
            
        Returns:
            Item recommendations with similarity scores
        """
        try:
            # Get item features
            item_features = await self._get_item_features(item_id)
            if not item_features:
                raise ValueError(f"Item {item_id} not found")
            
            # Generate recommendations based on type
            if recommendation_type == "similar":
                recommendations = await self._find_similar_items(item_id, item_features, num_recommendations)
            elif recommendation_type == "complementary":
                recommendations = await self._find_complementary_items(item_id, item_features, num_recommendations)
            elif recommendation_type == "alternative":
                recommendations = await self._find_alternative_items(item_id, item_features, num_recommendations)
            else:
                raise ValueError(f"Unknown recommendation type: {recommendation_type}")
            
            return {
                "item_id": item_id,
                "recommendation_type": recommendation_type,
                "recommendations": recommendations,
                "metadata": {
                    "base_item": item_features,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get item recommendations: {e}")
            raise
    
    async def get_trending_recommendations(
        self,
        time_window: str = "week",
        categories: Optional[List[str]] = None,
        num_recommendations: int = 20
    ) -> Dict[str, Any]:
        """
        Get trending items and recommendations.
        
        Args:
            time_window: 'day', 'week', 'month'
            categories: Filter by categories
            num_recommendations: Number of trending items
            
        Returns:
            Trending recommendations with trend scores
        """
        try:
            # Calculate time window
            now = datetime.utcnow()
            if time_window == "day":
                start_time = now - timedelta(days=1)
            elif time_window == "week":
                start_time = now - timedelta(weeks=1)
            elif time_window == "month":
                start_time = now - timedelta(days=30)
            else:
                raise ValueError(f"Invalid time window: {time_window}")
            
            # Get trending items
            trending_items = await self._calculate_trending_items(start_time, categories)
            
            # Get top recommendations
            top_trending = trending_items[:num_recommendations]
            
            # Enrich with additional data
            enriched_trending = []
            for item in top_trending:
                item_data = await self._get_item_features(item["item_id"])
                if item_data:
                    enriched_item = {
                        **item,
                        "item_data": item_data,
                        "trend_explanation": self._generate_trend_explanation(item)
                    }
                    enriched_trending.append(enriched_item)
            
            return {
                "time_window": time_window,
                "categories": categories,
                "trending_items": enriched_trending,
                "metadata": {
                    "total_candidates": len(trending_items),
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": now.isoformat()
                    },
                    "generated_at": now.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get trending recommendations: {e}")
            raise
    
    async def update_user_interaction(
        self,
        user_id: str,
        item_id: str,
        interaction_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update user interaction data for recommendation learning.
        
        Args:
            user_id: User identifier
            item_id: Item identifier
            interaction_type: 'view', 'like', 'purchase', 'share', etc.
            context: Additional context data
            
        Returns:
            Success status
        """
        try:
            interaction_data = {
                "user_id": user_id,
                "item_id": item_id,
                "interaction_type": interaction_type,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context or {}
            }
            
            # Store interaction
            await self._store_interaction(interaction_data)
            
            # Update user profile
            await self._update_user_profile(user_id, item_id, interaction_type)
            
            # Invalidate relevant caches
            await self._invalidate_user_cache(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user interaction: {e}")
            return False
    
    async def _collaborative_filtering(
        self,
        user_id: str,
        user_history: List[Dict],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendations."""
        try:
            # Get similar users
            similar_users = await self._find_similar_users(user_id, user_history)
            
            # Get items liked by similar users
            candidate_items = defaultdict(float)
            
            for similar_user, similarity_score in similar_users[:20]:  # Top 20 similar users
                user_items = await self._get_user_history(similar_user["user_id"])
                
                for item in user_items:
                    if item["item_id"] not in [h["item_id"] for h in user_history]:
                        # Weight by similarity and interaction strength
                        interaction_weight = self._get_interaction_weight(item["interaction_type"])
                        candidate_items[item["item_id"]] += similarity_score * interaction_weight
            
            # Sort and return top recommendations
            sorted_items = sorted(candidate_items.items(), key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for item_id, score in sorted_items[:num_recommendations]:
                recommendations.append({
                    "item_id": item_id,
                    "score": float(score),
                    "algorithm": "collaborative"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Collaborative filtering failed: {e}")
            return []
    
    async def _content_based_filtering(
        self,
        user_profile: Dict[str, Any],
        categories: Optional[List[str]],
        style_preferences: Optional[List[str]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Content-based filtering recommendations."""
        try:
            # Get user preferences from profile
            preferred_categories = user_profile.get("preferred_categories", [])
            preferred_styles = user_profile.get("preferred_styles", [])
            preferred_colors = user_profile.get("preferred_colors", [])
            
            # Override with explicit preferences if provided
            if categories:
                preferred_categories = categories
            if style_preferences:
                preferred_styles = style_preferences
            
            # Find items matching preferences
            candidate_items = await self._find_items_by_preferences(
                preferred_categories, preferred_styles, preferred_colors
            )
            
            # Score items based on preference match
            scored_items = []
            for item in candidate_items:
                score = self._calculate_content_score(
                    item, preferred_categories, preferred_styles, preferred_colors
                )
                scored_items.append({
                    "item_id": item["item_id"],
                    "score": score,
                    "algorithm": "content_based"
                })
            
            # Sort and return top recommendations
            scored_items.sort(key=lambda x: x["score"], reverse=True)
            return scored_items[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Content-based filtering failed: {e}")
            return []
    
    async def _popularity_based_recommendations(
        self,
        categories: Optional[List[str]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Popularity-based recommendations."""
        try:
            # Get popular items (last 30 days)
            popular_items = await self._get_popular_items(categories, days=30)
            
            recommendations = []
            for item in popular_items[:num_recommendations]:
                recommendations.append({
                    "item_id": item["item_id"],
                    "score": item["popularity_score"],
                    "algorithm": "popularity"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Popularity-based recommendations failed: {e}")
            return []
    
    async def _trend_based_recommendations(
        self,
        categories: Optional[List[str]],
        style_preferences: Optional[List[str]],
        num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Trend-based recommendations."""
        try:
            # Get trending items
            trending_items = await self._calculate_trending_items(
                datetime.utcnow() - timedelta(days=7), categories
            )
            
            # Filter by style preferences if provided
            if style_preferences:
                filtered_items = []
                for item in trending_items:
                    item_data = await self._get_item_features(item["item_id"])
                    if item_data and any(style in item_data.get("styles", []) for style in style_preferences):
                        filtered_items.append(item)
                trending_items = filtered_items
            
            recommendations = []
            for item in trending_items[:num_recommendations]:
                recommendations.append({
                    "item_id": item["item_id"],
                    "score": item["trend_score"],
                    "algorithm": "trend_based"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Trend-based recommendations failed: {e}")
            return []
    
    async def _combine_recommendations(
        self,
        collab_recs: List[Dict],
        content_recs: List[Dict],
        popularity_recs: List[Dict],
        trend_recs: List[Dict],
        user_history: Optional[List[Dict]],
        num_final: int
    ) -> List[Dict[str, Any]]:
        """Combine recommendations from different algorithms."""
        try:
            # Collect all recommendations
            all_recs = defaultdict(lambda: {"scores": {}, "algorithms": []})
            
            # Add collaborative filtering recommendations
            for rec in collab_recs:
                item_id = rec["item_id"]
                all_recs[item_id]["scores"]["collaborative"] = rec["score"]
                all_recs[item_id]["algorithms"].append("collaborative")
            
            # Add content-based recommendations
            for rec in content_recs:
                item_id = rec["item_id"]
                all_recs[item_id]["scores"]["content_based"] = rec["score"]
                all_recs[item_id]["algorithms"].append("content_based")
            
            # Add popularity recommendations
            for rec in popularity_recs:
                item_id = rec["item_id"]
                all_recs[item_id]["scores"]["popularity"] = rec["score"]
                all_recs[item_id]["algorithms"].append("popularity")
            
            # Add trend recommendations
            for rec in trend_recs:
                item_id = rec["item_id"]
                all_recs[item_id]["scores"]["trend_based"] = rec["score"]
                all_recs[item_id]["algorithms"].append("trend_based")
            
            # Calculate hybrid scores
            final_recs = []
            seen_items = set()
            if user_history:
                seen_items = {item["item_id"] for item in user_history}
            
            for item_id, data in all_recs.items():
                if item_id in seen_items:
                    continue
                
                # Calculate weighted hybrid score
                hybrid_score = 0.0
                for algorithm, weight in self.hybrid_weights.items():
                    if algorithm in data["scores"]:
                        # Normalize scores to 0-1 range
                        normalized_score = min(data["scores"][algorithm], 1.0)
                        hybrid_score += weight * normalized_score
                
                final_recs.append({
                    "item_id": item_id,
                    "hybrid_score": hybrid_score,
                    "component_scores": data["scores"],
                    "algorithms": data["algorithms"]
                })
            
            # Sort by hybrid score and return top N
            final_recs.sort(key=lambda x: x["hybrid_score"], reverse=True)
            return final_recs[:num_final]
            
        except Exception as e:
            logger.error(f"Failed to combine recommendations: {e}")
            return []
    
    async def _enrich_recommendations(
        self,
        recommendations: List[Dict],
        user_profile: Dict[str, Any],
        user_history: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Enrich recommendations with additional data and explanations."""
        try:
            enriched = []
            
            for rec in recommendations:
                item_data = await self._get_item_features(rec["item_id"])
                if not item_data:
                    continue
                
                # Generate explanation
                explanation = self._generate_recommendation_explanation(
                    rec, item_data, user_profile, user_history
                )
                
                enriched_rec = {
                    "item_id": rec["item_id"],
                    "score": rec["hybrid_score"],
                    "item_data": item_data,
                    "explanation": explanation,
                    "algorithms_used": rec["algorithms"],
                    "component_scores": rec["component_scores"]
                }
                
                enriched.append(enriched_rec)
            
            return enriched
            
        except Exception as e:
            logger.error(f"Failed to enrich recommendations: {e}")
            return recommendations
    
    def _generate_recommendation_explanation(
        self,
        recommendation: Dict,
        item_data: Dict,
        user_profile: Dict,
        user_history: List[Dict]
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        try:
            explanations = []
            
            # Check which algorithms contributed
            if "collaborative" in recommendation["algorithms"]:
                explanations.append("users with similar taste also liked this")
            
            if "content_based" in recommendation["algorithms"]:
                # Find matching preferences
                matching_categories = set(item_data.get("categories", [])) & set(user_profile.get("preferred_categories", []))
                matching_styles = set(item_data.get("styles", [])) & set(user_profile.get("preferred_styles", []))
                
                if matching_categories:
                    explanations.append(f"matches your interest in {', '.join(matching_categories)}")
                if matching_styles:
                    explanations.append(f"fits your {', '.join(matching_styles)} style")
            
            if "popularity" in recommendation["algorithms"]:
                explanations.append("currently popular")
            
            if "trend_based" in recommendation["algorithms"]:
                explanations.append("trending now")
            
            if explanations:
                return "Recommended because " + " and ".join(explanations)
            else:
                return "Recommended for you"
                
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return "Recommended for you"
    
    def _generate_trend_explanation(self, trending_item: Dict) -> str:
        """Generate explanation for why an item is trending."""
        try:
            trend_score = trending_item.get("trend_score", 0)
            velocity = trending_item.get("velocity", 0)
            
            if velocity > 2.0:
                return f"Rapidly gaining popularity (trend score: {trend_score:.2f})"
            elif velocity > 1.5:
                return f"Growing in popularity (trend score: {trend_score:.2f})"
            elif trend_score > 0.8:
                return f"Consistently popular (trend score: {trend_score:.2f})"
            else:
                return f"Emerging trend (trend score: {trend_score:.2f})"
                
        except Exception as e:
            logger.error(f"Failed to generate trend explanation: {e}")
            return "Trending item"
    
    # Helper methods for data access (these would integrate with actual data sources)
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data."""
        # This would typically query a user database
        # For now, return a mock profile
        return {
            "user_id": user_id,
            "preferred_categories": ["tops", "dresses"],
            "preferred_styles": ["casual", "modern"],
            "preferred_colors": ["black", "white", "blue"],
            "size_preferences": {"tops": "M", "bottoms": "32"},
            "budget_range": {"min": 50, "max": 200}
        }
    
    async def _get_user_history(self, user_id: str) -> List[Dict]:
        """Get user interaction history."""
        # This would typically query an interactions database
        # For now, return mock history
        return [
            {"item_id": f"item_{i}", "interaction_type": "view", "timestamp": datetime.utcnow().isoformat()}
            for i in range(5)
        ]
    
    async def _get_item_features(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item features and metadata."""
        # This would typically query a product database
        # For now, return mock item data
        return {
            "item_id": item_id,
            "title": f"Fashion Item {item_id}",
            "categories": ["tops"],
            "styles": ["casual", "modern"],
            "colors": ["blue"],
            "price": 99.99,
            "brand": "Example Brand",
            "description": "A stylish fashion item"
        }
    
    def _get_interaction_weight(self, interaction_type: str) -> float:
        """Get weight for different interaction types."""
        weights = {
            "purchase": 3.0,
            "add_to_cart": 2.0,
            "like": 1.5,
            "share": 1.2,
            "view": 1.0,
            "click": 0.8
        }
        return weights.get(interaction_type, 1.0)
    
    def _calculate_content_score(
        self,
        item: Dict,
        preferred_categories: List[str],
        preferred_styles: List[str],
        preferred_colors: List[str]
    ) -> float:
        """Calculate content-based similarity score."""
        score = 0.0
        
        # Category match
        item_categories = set(item.get("categories", []))
        category_match = len(item_categories & set(preferred_categories)) / max(len(preferred_categories), 1)
        score += category_match * 0.4
        
        # Style match
        item_styles = set(item.get("styles", []))
        style_match = len(item_styles & set(preferred_styles)) / max(len(preferred_styles), 1)
        score += style_match * 0.3
        
        # Color match
        item_colors = set(item.get("colors", []))
        color_match = len(item_colors & set(preferred_colors)) / max(len(preferred_colors), 1)
        score += color_match * 0.3
        
        return min(score, 1.0)
    
    async def _get_cached_recommendations(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get recommendations from cache."""
        try:
            if self.redis_manager:
                cached_data = await self.redis_manager.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to get cached recommendations: {e}")
        return None
    
    async def _cache_recommendations(self, cache_key: str, recommendations: Dict[str, Any]):
        """Cache recommendations."""
        try:
            if self.redis_manager:
                await self.redis_manager.setex(
                    cache_key, 
                    self.cache_ttl, 
                    json.dumps(recommendations, default=str)
                )
        except Exception as e:
            logger.warning(f"Failed to cache recommendations: {e}")
    
    async def _invalidate_user_cache(self, user_id: str):
        """Invalidate user-specific caches."""
        try:
            if self.redis_manager:
                pattern = f"user_rec:{user_id}:*"
                keys = await self.redis_manager.keys(pattern)
                if keys:
                    await self.redis_manager.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to invalidate user cache: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the recommendation engine."""
        try:
            health = {
                'status': 'healthy',
                'models_initialized': {
                    'collaborative_model': self.collaborative_model is not None,
                    'content_vectorizer': self.content_vectorizer is not None
                },
                'redis_connected': self.redis_manager is not None,
                'cache_ttl': self.cache_ttl,
                'hybrid_weights': self.hybrid_weights
            }
            
            # Test Redis connection
            if self.redis_manager:
                try:
                    await self.redis_manager.ping()
                    health['redis_status'] = 'connected'
                except:
                    health['redis_status'] = 'disconnected'
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # Placeholder methods for full implementation
    async def _initialize_models(self): pass
    async def _find_similar_users(self, user_id: str, user_history: List[Dict]) -> List[Tuple]: return []
    async def _find_items_by_preferences(self, categories, styles, colors) -> List[Dict]: return []
    async def _get_popular_items(self, categories, days) -> List[Dict]: return []
    async def _calculate_trending_items(self, start_time, categories) -> List[Dict]: return []
    async def _find_similar_items(self, item_id, features, num_recs) -> List[Dict]: return []
    async def _find_complementary_items(self, item_id, features, num_recs) -> List[Dict]: return []
    async def _find_alternative_items(self, item_id, features, num_recs) -> List[Dict]: return []
    async def _store_interaction(self, interaction_data): pass
    async def _update_user_profile(self, user_id, item_id, interaction_type): pass