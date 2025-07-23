"""
KSE Memory Service - Universal AI Substrate Integration
Handles temporal knowledge graphs, cross-modal embeddings, and commercial feedback loops
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import json

from ..core.database import get_db
from ..core.redis_client import redis_manager
from ..core.config import get_settings
from ..models.generation_models import GenerationJob, GenerationOutput, GenerationFeedback
from ..models.fashion_models import Brand, Collection, Product, DesignDNA
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class MultiModalInputs:
    """Multi-modal input structure for KSE processing."""
    def __init__(self, modalities: List[str], embeddings: Dict[str, Any], metadata: Dict[str, Any]):
        self.modalities = modalities
        self.embeddings = embeddings
        self.metadata = metadata


class CommercialOutcomes:
    """Commercial outcome data structure."""
    def __init__(self, conversion_rate: float, revenue: float, user_engagement: Dict[str, Any]):
        self.conversion_rate = conversion_rate
        self.revenue = revenue
        self.user_engagement = user_engagement


class KSEMemoryService:
    """
    KSE Memory SDK integration for universal AI substrate capabilities.
    Implements temporal reasoning, cross-modal learning, and commercial feedback integration.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.chroma_client = None
        self.knowledge_graph = KnowledgeGraph()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.feedback_loop = FeedbackLoop()
        self.temporal_reasoner = TemporalReasoner()
        
        # Initialize connections
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize ChromaDB and other connections."""
        try:
            self.chroma_client = chromadb.HttpClient(
                host=self.settings.chromadb_host,
                port=self.settings.chromadb_port,
                settings=Settings(allow_reset=True)
            )
            
            # Create or get collections
            self.fashion_collection = self.chroma_client.get_or_create_collection(
                name="fashion_embeddings",
                metadata={"description": "Fashion design embeddings"}
            )
            
            self.memory_collection = self.chroma_client.get_or_create_collection(
                name="kse_memory_nodes",
                metadata={"description": "KSE memory nodes with temporal context"}
            )
            
            logger.info("KSE Memory Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize KSE Memory Service: {e}")
            raise
    
    async def store_generation_context(
        self, 
        generation_id: str, 
        inputs: MultiModalInputs,
        outputs: Any,  # GenerationResults
        commercial_data: Optional[CommercialOutcomes] = None
    ):
        """
        Store generation context in KSE Memory with temporal knowledge graph update.
        """
        try:
            timestamp = datetime.utcnow()
            
            # Temporal knowledge graph update
            await self.knowledge_graph.add_generation_node(
                generation_id, inputs, outputs, timestamp
            )
            
            # Cross-modal embedding storage
            embeddings = await self.embedding_service.encode_multimodal(
                inputs, outputs
            )
            await self.vector_store.upsert(generation_id, embeddings)
            
            # Commercial feedback integration
            if commercial_data:
                await self.feedback_loop.integrate_outcomes(
                    generation_id, commercial_data
                )
            
            # Update temporal reasoning patterns
            await self.temporal_reasoner.update_patterns(
                generation_id, inputs, outputs, timestamp
            )
            
            logger.info(f"Stored generation context for {generation_id}")
            
        except Exception as e:
            logger.error(f"Failed to store generation context: {e}")
            raise
    
    async def retrieve_relevant_context(
        self,
        inputs: Dict[str, Any],
        brand_id: Optional[str] = None,
        depth: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context from KSE Memory for generation guidance.
        """
        try:
            # Convert inputs to embeddings for similarity search
            query_embedding = await self.embedding_service.encode_query(inputs)
            
            # Retrieve similar memory nodes
            memory_nodes = await self.vector_store.similarity_search(
                query_embedding, 
                limit=depth,
                filters={"brand_id": brand_id} if brand_id else None
            )
            
            # Get temporal context
            temporal_context = await self.temporal_reasoner.get_temporal_context(
                memory_nodes, brand_id
            )
            
            # Retrieve design DNA evolution
            design_evolution = await self.knowledge_graph.get_design_evolution(
                brand_id, depth
            )
            
            # Compile relevant context
            context = {
                "memory_nodes": memory_nodes,
                "temporal_context": temporal_context,
                "design_evolution": design_evolution,
                "brand_consistency_patterns": await self._get_brand_patterns(brand_id),
                "commercial_insights": await self._get_commercial_insights(brand_id),
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
            # Cache context for quick access
            await redis_manager.set(
                f"kse_context:{hash(str(inputs))}", 
                context, 
                expire=1800  # 30 minutes
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant context: {e}")
            return {"memory_nodes": [], "error": str(e)}
    
    async def retrieve_style_context(
        self,
        source_inputs: Dict[str, Any],
        target_inputs: Dict[str, Any],
        brand_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve style-specific context for style transfer operations."""
        try:
            # Encode both source and target
            source_embedding = await self.embedding_service.encode_query(source_inputs)
            target_embedding = await self.embedding_service.encode_query(target_inputs)
            
            # Find style bridge patterns
            style_bridges = await self.vector_store.find_style_bridges(
                source_embedding, target_embedding, brand_id
            )
            
            # Get successful style transfer history
            transfer_history = await self.knowledge_graph.get_style_transfer_history(
                source_inputs, target_inputs, brand_id
            )
            
            return {
                "style_bridges": style_bridges,
                "transfer_history": transfer_history,
                "style_compatibility_score": await self._calculate_style_compatibility(
                    source_embedding, target_embedding
                ),
                "recommended_parameters": await self._get_style_transfer_params(
                    style_bridges, transfer_history
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve style context: {e}")
            return {"error": str(e)}
    
    async def integrate_feedback(
        self,
        generation_id: str,
        commercial_outcomes: Optional[Dict[str, Any]] = None,
        user_ratings: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ):
        """Integrate feedback to improve future generations."""
        try:
            # Store feedback in database
            if db:
                feedback_entry = GenerationFeedback(
                    id=uuid.uuid4(),
                    job_id=generation_id,
                    rating=user_ratings.get("overall_rating", 0) if user_ratings else None,
                    comments=user_ratings.get("comments") if user_ratings else None,
                    would_purchase=commercial_outcomes.get("would_purchase") if commercial_outcomes else None,
                    created_at=datetime.utcnow()
                )
                db.add(feedback_entry)
                await db.commit()
            
            # Update KSE memory with feedback
            await self.feedback_loop.process_feedback(
                generation_id, commercial_outcomes, user_ratings
            )
            
            # Update temporal patterns based on feedback
            await self.temporal_reasoner.integrate_feedback(
                generation_id, commercial_outcomes, user_ratings
            )
            
            # Trigger learning updates
            await self._trigger_learning_update(generation_id, commercial_outcomes, user_ratings)
            
            logger.info(f"Integrated feedback for generation {generation_id}")
            
        except Exception as e:
            logger.error(f"Failed to integrate feedback: {e}")
            raise
    
    async def get_brand_memory_insights(self, brand_id: str) -> Dict[str, Any]:
        """Get comprehensive memory insights for a brand."""
        try:
            # Get recent generations
            recent_generations = await self.knowledge_graph.get_recent_generations(
                brand_id, limit=10
            )
            
            # Analyze design evolution
            design_evolution = await self.temporal_reasoner.analyze_design_evolution(
                brand_id
            )
            
            # Get commercial performance patterns
            commercial_performance = await self.feedback_loop.get_performance_patterns(
                brand_id
            )
            
            # Analyze temporal patterns
            temporal_patterns = await self.temporal_reasoner.get_temporal_patterns(
                brand_id
            )
            
            # Calculate memory statistics
            total_nodes = await self.vector_store.count_brand_nodes(brand_id)
            
            return {
                "total_nodes": total_nodes,
                "recent_generations": recent_generations,
                "design_evolution": design_evolution,
                "commercial_performance": commercial_performance,
                "temporal_patterns": temporal_patterns,
                "memory_health": await self._assess_memory_health(brand_id),
                "learning_velocity": await self._calculate_learning_velocity(brand_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get brand memory insights: {e}")
            return {"error": str(e)}
    
    async def _get_brand_patterns(self, brand_id: Optional[str]) -> Dict[str, Any]:
        """Get brand consistency patterns from memory."""
        if not brand_id:
            return {}
        
        try:
            # Query brand-specific patterns from vector store
            patterns = await self.vector_store.get_brand_patterns(brand_id)
            return patterns
        except Exception as e:
            logger.warning(f"Failed to get brand patterns: {e}")
            return {}
    
    async def _get_commercial_insights(self, brand_id: Optional[str]) -> Dict[str, Any]:
        """Get commercial performance insights."""
        if not brand_id:
            return {}
        
        try:
            insights = await self.feedback_loop.get_commercial_insights(brand_id)
            return insights
        except Exception as e:
            logger.warning(f"Failed to get commercial insights: {e}")
            return {}
    
    async def _calculate_style_compatibility(
        self, 
        source_embedding: List[float], 
        target_embedding: List[float]
    ) -> float:
        """Calculate compatibility score between style embeddings."""
        try:
            # Cosine similarity
            source_array = np.array(source_embedding)
            target_array = np.array(target_embedding)
            
            similarity = np.dot(source_array, target_array) / (
                np.linalg.norm(source_array) * np.linalg.norm(target_array)
            )
            
            return float(similarity)
        except Exception:
            return 0.5  # Default neutral compatibility
    
    async def _get_style_transfer_params(
        self, 
        style_bridges: List[Dict], 
        transfer_history: List[Dict]
    ) -> Dict[str, Any]:
        """Get recommended parameters for style transfer."""
        # Analyze successful transfers to recommend parameters
        if not transfer_history:
            return {"strength": 0.7, "guidance_scale": 7.5}
        
        # Calculate optimal parameters based on history
        successful_transfers = [t for t in transfer_history if t.get("success_score", 0) > 0.8]
        
        if successful_transfers:
            avg_strength = np.mean([t.get("strength", 0.7) for t in successful_transfers])
            avg_guidance = np.mean([t.get("guidance_scale", 7.5) for t in successful_transfers])
            
            return {
                "strength": float(avg_strength),
                "guidance_scale": float(avg_guidance),
                "recommended_steps": 50,
                "confidence": len(successful_transfers) / len(transfer_history)
            }
        
        return {"strength": 0.7, "guidance_scale": 7.5, "confidence": 0.0}
    
    async def _trigger_learning_update(
        self,
        generation_id: str,
        commercial_outcomes: Optional[Dict[str, Any]],
        user_ratings: Optional[Dict[str, Any]]
    ):
        """Trigger learning updates based on feedback."""
        try:
            # Queue learning update task
            learning_task = {
                "generation_id": generation_id,
                "commercial_outcomes": commercial_outcomes,
                "user_ratings": user_ratings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await redis_manager.add_to_list("kse_learning_queue", learning_task)
            
            # Trigger immediate pattern updates for high-impact feedback
            if commercial_outcomes and commercial_outcomes.get("conversion_rate", 0) > 0.8:
                await self.temporal_reasoner.priority_pattern_update(generation_id)
                
        except Exception as e:
            logger.warning(f"Failed to trigger learning update: {e}")
    
    async def _assess_memory_health(self, brand_id: str) -> Dict[str, Any]:
        """Assess the health of brand memory."""
        try:
            # Check memory node distribution
            node_count = await self.vector_store.count_brand_nodes(brand_id)
            recent_activity = await self.knowledge_graph.get_recent_activity(brand_id, days=30)
            
            # Calculate health metrics
            health_score = min(1.0, node_count / 100)  # Normalize to 0-1
            activity_score = min(1.0, len(recent_activity) / 10)
            
            return {
                "overall_health": (health_score + activity_score) / 2,
                "node_count": node_count,
                "recent_activity": len(recent_activity),
                "recommendations": await self._get_health_recommendations(health_score, activity_score)
            }
            
        except Exception as e:
            logger.warning(f"Failed to assess memory health: {e}")
            return {"overall_health": 0.5, "error": str(e)}
    
    async def _calculate_learning_velocity(self, brand_id: str) -> Dict[str, Any]:
        """Calculate how quickly the system is learning for this brand."""
        try:
            # Get feedback integration rate
            recent_feedback = await self.feedback_loop.get_recent_feedback(brand_id, days=30)
            
            # Calculate learning metrics
            feedback_rate = len(recent_feedback) / 30  # Per day
            improvement_trend = await self.temporal_reasoner.calculate_improvement_trend(brand_id)
            
            return {
                "feedback_rate": feedback_rate,
                "improvement_trend": improvement_trend,
                "learning_velocity": feedback_rate * improvement_trend,
                "velocity_category": self._categorize_velocity(feedback_rate * improvement_trend)
            }
            
        except Exception as e:
            logger.warning(f"Failed to calculate learning velocity: {e}")
            return {"learning_velocity": 0.0, "error": str(e)}
    
    def _categorize_velocity(self, velocity: float) -> str:
        """Categorize learning velocity."""
        if velocity > 0.8:
            return "rapid"
        elif velocity > 0.5:
            return "moderate"
        elif velocity > 0.2:
            return "slow"
        else:
            return "minimal"
    
    async def _get_health_recommendations(
        self, 
        health_score: float, 
        activity_score: float
    ) -> List[str]:
        """Get recommendations for improving memory health."""
        recommendations = []
        
        if health_score < 0.5:
            recommendations.append("Increase generation volume to build memory base")
        
        if activity_score < 0.3:
            recommendations.append("More frequent user feedback needed")
            
        if health_score > 0.8 and activity_score > 0.8:
            recommendations.append("Memory system is healthy - consider advanced features")
            
        return recommendations


class KnowledgeGraph:
    """Temporal knowledge graph for tracking design relationships."""
    
    async def add_generation_node(
        self, 
        generation_id: str, 
        inputs: MultiModalInputs, 
        outputs: Any, 
        timestamp: datetime
    ):
        """Add a generation node to the knowledge graph."""
        try:
            node_data = {
                "id": generation_id,
                "type": "generation",
                "timestamp": timestamp.isoformat(),
                "inputs": {
                    "modalities": inputs.modalities,
                    "metadata": inputs.metadata
                },
                "outputs": {
                    "count": len(outputs) if hasattr(outputs, '__len__') else 1,
                    "quality_scores": getattr(outputs, 'quality_scores', [])
                }
            }
            
            # Store in Redis as graph node
            await redis_manager.set(
                f"kg_node:{generation_id}", 
                node_data, 
                expire=86400 * 365  # 1 year
            )
            
            # Add to brand-specific graph
            brand_id = inputs.metadata.get('brand_context', {}).get('brand_id')
            if brand_id:
                await redis_manager.add_to_list(f"kg_brand:{brand_id}", generation_id)
            
        except Exception as e:
            logger.error(f"Failed to add generation node: {e}")
    
    async def get_design_evolution(self, brand_id: Optional[str], depth: int) -> Dict[str, Any]:
        """Get design evolution patterns for a brand."""
        if not brand_id:
            return {}
        
        try:
            # Get recent generations for brand
            generation_ids = await redis_manager.get_list(f"kg_brand:{brand_id}", 0, depth)
            
            evolution_data = []
            for gen_id in generation_ids:
                node_data = await redis_manager.get(f"kg_node:{gen_id}")
                if node_data:
                    evolution_data.append(node_data)
            
            # Analyze evolution patterns
            return {
                "generations": evolution_data,
                "evolution_trends": self._analyze_evolution_trends(evolution_data),
                "consistency_score": self._calculate_consistency_score(evolution_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get design evolution: {e}")
            return {}
    
    def _analyze_evolution_trends(self, evolution_data: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in design evolution."""
        if len(evolution_data) < 2:
            return {"trend": "insufficient_data"}
        
        # Analyze quality score trends
        quality_trends = []
        for data in evolution_data:
            scores = data.get("outputs", {}).get("quality_scores", [])
            if scores:
                quality_trends.append(np.mean(scores))
        
        if len(quality_trends) >= 2:
            trend_direction = "improving" if quality_trends[-1] > quality_trends[0] else "declining"
            trend_strength = abs(quality_trends[-1] - quality_trends[0])
            
            return {
                "trend": trend_direction,
                "strength": trend_strength,
                "quality_progression": quality_trends
            }
        
        return {"trend": "stable"}
    
    def _calculate_consistency_score(self, evolution_data: List[Dict]) -> float:
        """Calculate brand consistency across generations."""
        if len(evolution_data) < 2:
            return 1.0
        
        # Simple consistency metric based on modality usage
        modality_sets = []
        for data in evolution_data:
            modalities = set(data.get("inputs", {}).get("modalities", []))
            modality_sets.append(modalities)
        
        # Calculate intersection over union for consistency
        if modality_sets:
            intersection = set.intersection(*modality_sets)
            union = set.union(*modality_sets)
            consistency = len(intersection) / len(union) if union else 1.0
            return consistency
        
        return 1.0
    
    async def get_recent_generations(self, brand_id: str, limit: int = 10) -> List[Dict]:
        """Get recent generations for a brand."""
        try:
            generation_ids = await redis_manager.get_list(f"kg_brand:{brand_id}", 0, limit)
            
            generations = []
            for gen_id in generation_ids:
                node_data = await redis_manager.get(f"kg_node:{gen_id}")
                if node_data:
                    generations.append(node_data)
            
            return generations
            
        except Exception as e:
            logger.error(f"Failed to get recent generations: {e}")
            return []
    
    async def get_style_transfer_history(
        self, 
        source_inputs: Dict, 
        target_inputs: Dict, 
        brand_id: Optional[str]
    ) -> List[Dict]:
        """Get history of similar style transfers."""
        # Mock implementation - in reality would query graph for similar transfers
        return [
            {
                "transfer_id": "mock_transfer_1",
                "success_score": 0.85,
                "strength": 0.7,
                "guidance_scale": 7.5,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        ]
    
    async def get_recent_activity(self, brand_id: str, days: int = 30) -> List[Dict]:
        """Get recent activity for a brand."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            generation_ids = await redis_manager.get_list(f"kg_brand:{brand_id}", 0, 100)
            
            recent_activity = []
            for gen_id in generation_ids:
                node_data = await redis_manager.get(f"kg_node:{gen_id}")
                if node_data:
                    node_timestamp = datetime.fromisoformat(node_data["timestamp"])
                    if node_timestamp > cutoff_date:
                        recent_activity.append(node_data)
            
            return recent_activity
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []


class EmbeddingService:
    """Service for encoding multi-modal inputs into embeddings."""
    
    async def encode_multimodal(self, inputs: MultiModalInputs, outputs: Any) -> Dict[str, List[float]]:
        """Encode multi-modal inputs and outputs into embeddings."""
        embeddings = {}
        
        # Encode each modality
        for modality in inputs.modalities:
            if modality in inputs.embeddings:
                embeddings[modality] = inputs.embeddings[modality]
        
        # Add output embeddings
        embeddings["output"] = await self._encode_outputs(outputs)
        
        return embeddings
    
    async def encode_query(self, inputs: Dict[str, Any]) -> List[float]:
        """Encode query inputs for similarity search."""
        # Mock implementation - combine all available embeddings
        combined_embedding = []
        
        if "embeddings" in inputs:
            for modality, embedding in inputs["embeddings"].items():
                if isinstance(embedding, list) and len(embedding) > 0:
                    if isinstance(embedding[0], list):
                        # Multiple embeddings, take the first one
                        combined_embedding.extend(embedding[0][:100])  # Limit size
                    else:
                        combined_embedding.extend(embedding[:100])  # Limit size
        
        # Pad or truncate to standard size
        target_size = 512
        if len(combined_embedding) < target_size:
            combined_embedding.extend([0.0] * (target_size - len(combined_embedding)))
        else:
            combined_embedding = combined_embedding[:target_size]
        
        return combined_embedding
    
    async def _encode_outputs(self, outputs: Any) -> List[float]:
        """Encode generation outputs."""
        # Mock implementation - would use actual model to encode outputs
        return [0.1] * 512  # Standard embedding size


class VectorStore:
    """Vector storage and similarity search for KSE memory."""
    
    async def upsert(self, generation_id: str, embeddings: Dict[str, List[float]]):
        """Store embeddings in vector database."""
        try:
            # Combine all embeddings into a single vector
            combined_embedding = []
            metadata = {"generation_id": generation_id, "modalities": list(embeddings.keys())}
            
            for modality, embedding in embeddings.items():
                if isinstance(embedding, list):
                    combined_embedding.extend(embedding[:100])  # Limit each modality
                    metadata[f"{modality}_dim"] = len(embedding)
            
            # Pad to standard size
            target_size = 512
            if len(combined_embedding) < target_size:
                combined_embedding.extend([0.0] * (target_size - len(combined_embedding)))
            else:
                combined_embedding = combined_embedding[:target_size]
            
            # Store in Redis as backup
            await redis_manager.set(
                f"embedding:{generation_id}",
                {
                    "embedding": combined_embedding,
                    "metadata": metadata
                },
                expire=86400 * 30  # 30 days
            )
            
        except Exception as e:
            logger.error(f"Failed to upsert embeddings: {e}")
    
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        try:
            # Mock implementation - would use actual vector search
            # For now, return some mock similar nodes
            mock_nodes = []
            for i in range(min(limit, 3)):
                mock_nodes.append({
                    "id": f"mock_node_{i}",
                    "similarity_score": 0.8 - (i * 0.1),
                    "metadata": {
                        "generation_id": f"gen_{i}",
                        "modalities": ["text", "image"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            return mock_nodes
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
    
    async def find_style_bridges(
        self, 
        source_embedding: List[float], 
        target_embedding: List[float],
        brand_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find style bridge patterns between source and target."""
        # Mock implementation
        return [
            {
                "bridge_id": "style_bridge_1",
                "compatibility_score": 0.75,
                "intermediate_styles": ["modern_minimal", "contemporary"],
                "success_rate": 0.82
            }
        ]
    
    async def get_brand_patterns(self, brand_id: str) -> Dict[str, Any]:
        """Get brand-specific patterns from vector store."""
        # Mock implementation
        return {
            "dominant_styles": ["minimalist", "contemporary"],
            "color_preferences": ["neutral", "monochrome"],
            "consistency_score": 0.85
        }
    
    async def count_brand_nodes(self, brand_id: str) -> int:
        """Count memory nodes for a brand."""
        try:
            generation_ids = await redis_manager.get_list(f"kg_brand:{brand_id}", 0, -1)
            return len(generation_ids)
        except Exception:
            return 0


class FeedbackLoop:
    """Commercial feedback integration and learning."""
    
    async def integrate_outcomes(self, generation_id: str, commercial_data: CommercialOutcomes):
        """Integrate commercial outcomes into memory."""
        try:
            outcome_data = {
                "generation_id": generation_id,
                "conversion_rate": commercial_data.conversion_rate,
                "revenue": commercial_data.revenue,
                "user_engagement": commercial_data.user_engagement,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in Redis
            await redis_manager.set(
                f"commercial_outcome:{generation_id}",
                outcome_data,
                expire=86400 * 365  # 1 year
            )
            
            # Add to learning queue
            await redis_manager.add_to_list("commercial_learning_queue", outcome_data)
            
        except Exception as e:
            logger.error(f"Failed to integrate commercial outcomes: {e}")
    
    async def process_feedback(
        self,
        generation_id: str,
        commercial_outcomes: Optional[Dict[str, Any]],
        user_ratings: Optional[Dict[str, Any]]
    ):
        """Process feedback for learning updates."""
        try:
            feedback_data = {
                "generation_id": generation_id,
                "commercial_outcomes": commercial_outcomes,
                "user_ratings": user_ratings,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Store processed feedback
            await redis_manager.set(
                f"processed_feedback:{generation_id}",
                feedback_data,
                expire=86400 * 90  # 90 days
            )
            
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
    
    async def get_performance_patterns(self, brand_id: str) -> Dict[str, Any]:
        """Get commercial performance patterns for a brand."""
        # Mock implementation
        return {
            "average_conversion_rate": 0.15,
            "revenue_trend": "increasing",
            "top_performing_styles": ["minimalist", "contemporary"],
            "engagement_metrics": {
                "average_time_on_page": 45.2,
                "bounce_rate": 0.25,
                "social_shares": 12.3
            }
        }
    
    async def get_commercial_insights(self, brand_id: str) -> Dict[str, Any]:
        """Get commercial insights for a brand."""
        return await self.get_performance_patterns(brand_id)
    
    async def get_recent_feedback(self, brand_id: str, days: int = 30) -> List[Dict]:
        """Get recent feedback for a brand."""
        # Mock implementation - would query actual feedback
        return [
            {
                "generation_id": "gen_1",
                "rating": 4.5,
                "commercial_success": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]


class TemporalReasoner:
    """Temporal reasoning for design evolution and pattern recognition."""
    
    async def update_patterns(
        self,
        generation_id: str,
        inputs: MultiModalInputs,
        outputs: Any,
        timestamp: datetime
    ):
        """Update temporal patterns based on new generation."""
        try:
            pattern_data = {
                "generation_id": generation_id,
                "timestamp": timestamp.isoformat(),
                "modalities": inputs.modalities,
                "metadata": inputs.metadata
            }
            
            # Add to temporal pattern tracking
            await redis_manager.add_to_list("temporal_patterns", pattern_data)
            
        except Exception as e:
            logger.error(f"Failed to update temporal patterns: {e}")
    
    async def get_temporal_context(
        self, 
        memory_nodes: List[Dict], 
        brand_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get temporal context from memory nodes."""
        return {
            "temporal_coherence": 0.85,
            "evolution_stage": "mature",
            "seasonal_patterns": ["spring_minimal", "summer_light"],
            "trend_alignment": 0.78
        }
    
    async def integrate_feedback(
        self,
        generation_id: str,
        commercial_outcomes: Optional[Dict[str, Any]],
        user_ratings: Optional[Dict[str, Any]]
    ):
        """Integrate feedback into temporal reasoning."""
        try:
            feedback_integration = {
                "generation_id": generation_id,
                "feedback_type": "commercial" if commercial_outcomes else "user",
                "impact_score": self._calculate_feedback_impact(commercial_outcomes, user_ratings),
                "integrated_at": datetime.utcnow().isoformat()
            }
            
            await redis_manager.add_to_list("temporal_feedback", feedback_integration)
            
        except Exception as e:
            logger.error(f"Failed to integrate temporal feedback: {e}")
    
    def _calculate_feedback_impact(
        self,
        commercial_outcomes: Optional[Dict[str, Any]],
        user_ratings: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate impact score of feedback."""
        impact = 0.5  # Base impact
        
        if commercial_outcomes:
            conversion_rate = commercial_outcomes.get("conversion_rate", 0)
            impact += conversion_rate * 0.3
        
        if user_ratings:
            rating = user_ratings.get("overall_rating", 3) / 5.0  # Normalize to 0-1
            impact += rating * 0.2
        
        return min(1.0, impact)
    
    async def analyze_design_evolution(self, brand_id: str) -> Dict[str, Any]:
        """Analyze design evolution patterns for a brand."""
        return {
            "evolution_velocity": 0.65,
            "consistency_trend": "stable",
            "innovation_index": 0.72,
            "market_alignment": 0.81
        }
    
    async def get_temporal_patterns(self, brand_id: str) -> Dict[str, Any]:
        """Get temporal patterns for a brand."""
        return {
            "seasonal_cycles": ["spring_fresh", "summer_light", "fall_rich", "winter_cozy"],
            "trend_cycles": ["3_month_micro", "6_month_seasonal", "12_month_annual"],
            "innovation_rhythm": "quarterly_updates",
            "consistency_patterns": "high_brand_coherence"
        }
    
    async def priority_pattern_update(self, generation_id: str):
        """Trigger priority pattern update for high-impact feedback."""
        try:
            await redis_manager.add_to_list("priority_pattern_updates", {
                "generation_id": generation_id,
                "priority": "high",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to trigger priority pattern update: {e}")
    
    async def calculate_improvement_trend(self, brand_id: str) -> float:
        """Calculate improvement trend for a brand."""
        # Mock implementation - would analyze actual performance over time
        return 0.75  # Positive improvement trend