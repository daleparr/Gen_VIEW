"""
Memory Manager for KSE Memory Service
Core orchestrator for memory storage, retrieval, and management operations
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from ..core.database import get_db_session
from ..core.redis_client import get_redis_manager
from ..models.memory_models import (
    MemoryNode, MemoryAssociation, MemoryContext, 
    MemoryFeedback, MemoryCluster, MemoryClusterMembership
)
from .embedding_service import EmbeddingService
from .knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Core memory manager that orchestrates all memory operations.
    Handles storage, retrieval, clustering, and temporal reasoning.
    """
    
    def __init__(self, embedding_service: EmbeddingService, knowledge_graph_service: KnowledgeGraphService):
        self.embedding_service = embedding_service
        self.knowledge_graph_service = knowledge_graph_service
        self.redis_manager = None
        
        # Memory configuration
        self.similarity_threshold = 0.7
        self.max_memory_nodes = 100000
        self.cluster_update_interval = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize the memory manager."""
        try:
            logger.info("Initializing Memory Manager...")
            
            # Initialize Redis manager
            self.redis_manager = await get_redis_manager()
            
            # Start background tasks
            asyncio.create_task(self._periodic_cluster_update())
            asyncio.create_task(self._periodic_memory_cleanup())
            
            logger.info("Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Memory Manager: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Memory Manager...")
    
    async def store_memory(
        self,
        content: Union[str, Dict[str, Any]],
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        brand_id: Optional[str] = None,
        source_type: str = "generation",
        source_id: Optional[str] = None,
        importance_score: float = 0.5
    ) -> str:
        """
        Store a new memory node.
        
        Args:
            content: The content to store (text or structured data)
            content_type: Type of content (text, image, multimodal, etc.)
            metadata: Additional metadata
            brand_id: Associated brand ID
            source_type: Source of the memory (generation, feedback, external)
            source_id: ID of the source
            importance_score: Initial importance score (0-1)
            
        Returns:
            Memory node ID
        """
        try:
            # Generate embedding based on content type
            if content_type == "text":
                embedding = await self.embedding_service.encode_text(content)
            elif content_type == "multimodal":
                embedding = await self.embedding_service.encode_multimodal(content)
            else:
                # For other types, use text representation
                text_content = str(content) if not isinstance(content, str) else content
                embedding = await self.embedding_service.encode_text(text_content)
            
            # Create memory node
            memory_node = MemoryNode(
                content_type=content_type,
                content_text=content if isinstance(content, str) else None,
                content_metadata=content if isinstance(content, dict) else (metadata or {}),
                embedding_vector=embedding.tolist(),
                embedding_model=self.embedding_service.settings.embedding_model,
                embedding_dimension=len(embedding),
                importance_score=importance_score,
                brand_id=uuid.UUID(brand_id) if brand_id else None,
                source_type=source_type,
                source_id=source_id,
                source_metadata=metadata or {}
            )
            
            # Store in database
            async with get_db_session() as session:
                session.add(memory_node)
                await session.commit()
                await session.refresh(memory_node)
                
                memory_id = str(memory_node.id)
            
            # Store embedding in ChromaDB
            await self.embedding_service.store_embedding(
                embedding_id=memory_id,
                embedding=embedding,
                collection_name="memory_embeddings",
                metadata={
                    'content_type': content_type,
                    'brand_id': brand_id,
                    'source_type': source_type,
                    'importance_score': importance_score,
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            # Find and create associations with similar memories
            await self._create_memory_associations(memory_id, embedding, brand_id)
            
            # Update knowledge graph
            await self.knowledge_graph_service.process_memory_node(memory_node.to_dict())
            
            # Trigger clustering update
            await self._trigger_clustering_update(memory_id, embedding)
            
            logger.info(f"Stored memory node: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_memories(
        self,
        query: Union[str, Dict[str, Any]],
        query_type: str = "text",
        brand_id: Optional[str] = None,
        top_k: int = 10,
        similarity_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_associations: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on a query.
        
        Args:
            query: Query content (text or structured)
            query_type: Type of query (text, multimodal)
            brand_id: Filter by brand ID
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            filters: Additional filters
            include_associations: Whether to include memory associations
            
        Returns:
            List of relevant memory nodes with metadata
        """
        try:
            # Generate query embedding
            if query_type == "text":
                query_embedding = await self.embedding_service.encode_text(query)
            elif query_type == "multimodal":
                query_embedding = await self.embedding_service.encode_multimodal(query)
            else:
                query_text = str(query) if not isinstance(query, str) else query
                query_embedding = await self.embedding_service.encode_text(query_text)
            
            # Set similarity threshold
            threshold = similarity_threshold or self.similarity_threshold
            
            # Build ChromaDB filters
            chroma_filters = {}
            if brand_id:
                chroma_filters['brand_id'] = brand_id
            if filters:
                chroma_filters.update(filters)
            
            # Search for similar embeddings
            similar_embeddings = await self.embedding_service.find_similar_embeddings(
                query_embedding=query_embedding,
                collection_name="memory_embeddings",
                top_k=top_k * 2,  # Get more to filter by threshold
                threshold=threshold,
                filters=chroma_filters if chroma_filters else None
            )
            
            if not similar_embeddings:
                return []
            
            # Get memory node IDs
            memory_ids = [result['id'] for result in similar_embeddings[:top_k]]
            
            # Fetch full memory nodes from database
            async with get_db_session() as session:
                # Build query
                query_stmt = select(MemoryNode).where(MemoryNode.id.in_([uuid.UUID(mid) for mid in memory_ids]))
                
                if include_associations:
                    query_stmt = query_stmt.options(selectinload(MemoryNode.memory_associations))
                
                result = await session.execute(query_stmt)
                memory_nodes = result.scalars().all()
            
            # Update access statistics
            await self._update_access_stats(memory_ids)
            
            # Combine with similarity scores and format results
            results = []
            similarity_map = {result['id']: result['similarity'] for result in similar_embeddings}
            
            for node in memory_nodes:
                node_dict = node.to_dict()
                node_dict['similarity_score'] = similarity_map.get(str(node.id), 0.0)
                
                if include_associations:
                    node_dict['associations'] = [
                        {
                            'target_node_id': str(assoc.target_node_id),
                            'association_type': assoc.association_type,
                            'strength': assoc.strength,
                            'confidence': assoc.confidence
                        }
                        for assoc in node.memory_associations
                    ]
                
                results.append(node_dict)
            
            # Sort by similarity score
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Retrieved {len(results)} memories for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            raise
    
    async def add_memory_feedback(
        self,
        memory_node_id: str,
        feedback_type: str,
        feedback_score: Optional[float] = None,
        feedback_text: Optional[str] = None,
        generation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        commercial_impact: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add feedback to a memory node for reinforcement learning.
        
        Args:
            memory_node_id: ID of the memory node
            feedback_type: Type of feedback (positive, negative, neutral)
            feedback_score: Numeric feedback score
            feedback_text: Textual feedback
            generation_id: ID of generation that used this memory
            user_id: User providing feedback
            commercial_impact: Commercial outcome data
            
        Returns:
            Feedback entry ID
        """
        try:
            # Create feedback entry
            feedback = MemoryFeedback(
                memory_node_id=uuid.UUID(memory_node_id),
                feedback_type=feedback_type,
                feedback_score=feedback_score,
                feedback_text=feedback_text,
                generation_id=generation_id,
                user_id=user_id,
                commercial_impact=commercial_impact or {}
            )
            
            async with get_db_session() as session:
                session.add(feedback)
                await session.commit()
                await session.refresh(feedback)
                
                feedback_id = str(feedback.id)
            
            # Update memory node importance based on feedback
            await self._update_memory_importance(memory_node_id, feedback_type, feedback_score)
            
            # Update knowledge graph with feedback
            await self.knowledge_graph_service.process_feedback({
                'memory_node_id': memory_node_id,
                'feedback_type': feedback_type,
                'feedback_score': feedback_score,
                'commercial_impact': commercial_impact
            })
            
            logger.info(f"Added feedback {feedback_id} to memory {memory_node_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"Failed to add memory feedback: {e}")
            raise
    
    async def get_memory_insights(
        self,
        brand_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        insight_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get insights about memory patterns and trends.
        
        Args:
            brand_id: Filter by brand ID
            time_range: Time range for analysis
            insight_types: Types of insights to generate
            
        Returns:
            Dictionary of insights and analytics
        """
        try:
            insights = {}
            
            async with get_db_session() as session:
                # Base query
                base_query = select(MemoryNode)
                if brand_id:
                    base_query = base_query.where(MemoryNode.brand_id == uuid.UUID(brand_id))
                if time_range:
                    base_query = base_query.where(
                        and_(
                            MemoryNode.created_at >= time_range[0],
                            MemoryNode.created_at <= time_range[1]
                        )
                    )
                
                # Memory statistics
                total_memories = await session.scalar(select(func.count()).select_from(base_query.subquery()))
                insights['total_memories'] = total_memories
                
                # Content type distribution
                content_type_query = (
                    select(MemoryNode.content_type, func.count())
                    .select_from(base_query.subquery())
                    .group_by(MemoryNode.content_type)
                )
                content_types = await session.execute(content_type_query)
                insights['content_type_distribution'] = dict(content_types.all())
                
                # Importance score statistics
                importance_stats = await session.execute(
                    select(
                        func.avg(MemoryNode.importance_score),
                        func.min(MemoryNode.importance_score),
                        func.max(MemoryNode.importance_score)
                    ).select_from(base_query.subquery())
                )
                avg_imp, min_imp, max_imp = importance_stats.first()
                insights['importance_statistics'] = {
                    'average': float(avg_imp) if avg_imp else 0.0,
                    'minimum': float(min_imp) if min_imp else 0.0,
                    'maximum': float(max_imp) if max_imp else 0.0
                }
                
                # Most accessed memories
                top_accessed = await session.execute(
                    base_query.order_by(desc(MemoryNode.access_count)).limit(10)
                )
                insights['most_accessed'] = [
                    {
                        'id': str(node.id),
                        'content_type': node.content_type,
                        'access_count': node.access_count,
                        'importance_score': node.importance_score
                    }
                    for node in top_accessed.scalars().all()
                ]
                
                # Recent memories
                recent_memories = await session.execute(
                    base_query.order_by(desc(MemoryNode.created_at)).limit(10)
                )
                insights['recent_memories'] = [
                    {
                        'id': str(node.id),
                        'content_type': node.content_type,
                        'created_at': node.created_at.isoformat(),
                        'importance_score': node.importance_score
                    }
                    for node in recent_memories.scalars().all()
                ]
            
            # Add temporal patterns from knowledge graph
            temporal_insights = await self.knowledge_graph_service.get_temporal_insights(brand_id)
            insights['temporal_patterns'] = temporal_insights
            
            # Add clustering insights
            clustering_insights = await self._get_clustering_insights(brand_id)
            insights['clustering'] = clustering_insights
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get memory insights: {e}")
            raise
    
    async def _create_memory_associations(
        self,
        memory_id: str,
        embedding: np.ndarray,
        brand_id: Optional[str]
    ):
        """Create associations with similar existing memories."""
        try:
            # Find similar memories
            similar_memories = await self.embedding_service.find_similar_embeddings(
                query_embedding=embedding,
                collection_name="memory_embeddings",
                top_k=20,
                threshold=0.8,  # Higher threshold for associations
                filters={'brand_id': brand_id} if brand_id else None
            )
            
            associations = []
            for similar in similar_memories:
                if similar['id'] != memory_id:  # Don't associate with self
                    association = MemoryAssociation(
                        source_node_id=uuid.UUID(memory_id),
                        target_node_id=uuid.UUID(similar['id']),
                        association_type='similarity',
                        strength=similar['similarity'],
                        confidence=similar['similarity']
                    )
                    associations.append(association)
            
            if associations:
                async with get_db_session() as session:
                    session.add_all(associations)
                    await session.commit()
                
                logger.debug(f"Created {len(associations)} associations for memory {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to create memory associations: {e}")
    
    async def _update_access_stats(self, memory_ids: List[str]):
        """Update access statistics for memory nodes."""
        try:
            async with get_db_session() as session:
                # Update access count and last accessed time
                for memory_id in memory_ids:
                    await session.execute(
                        MemoryNode.__table__.update()
                        .where(MemoryNode.id == uuid.UUID(memory_id))
                        .values(
                            access_count=MemoryNode.access_count + 1,
                            last_accessed=datetime.utcnow()
                        )
                    )
                await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update access stats: {e}")
    
    async def _update_memory_importance(
        self,
        memory_node_id: str,
        feedback_type: str,
        feedback_score: Optional[float]
    ):
        """Update memory importance based on feedback."""
        try:
            # Calculate importance adjustment
            if feedback_type == "positive":
                adjustment = 0.1 + (feedback_score or 0) * 0.1
            elif feedback_type == "negative":
                adjustment = -0.1 - (feedback_score or 0) * 0.1
            else:
                adjustment = 0.0
            
            async with get_db_session() as session:
                # Get current importance
                result = await session.execute(
                    select(MemoryNode.importance_score)
                    .where(MemoryNode.id == uuid.UUID(memory_node_id))
                )
                current_importance = result.scalar()
                
                if current_importance is not None:
                    # Update importance (clamp between 0 and 1)
                    new_importance = max(0.0, min(1.0, current_importance + adjustment))
                    
                    await session.execute(
                        MemoryNode.__table__.update()
                        .where(MemoryNode.id == uuid.UUID(memory_node_id))
                        .values(importance_score=new_importance)
                    )
                    await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update memory importance: {e}")
    
    async def _trigger_clustering_update(self, memory_id: str, embedding: np.ndarray):
        """Trigger clustering update for new memory."""
        try:
            # This would implement clustering logic
            # For now, we'll add to Redis queue for background processing
            await self.redis_manager.add_to_set("clustering_queue", memory_id)
            
        except Exception as e:
            logger.error(f"Failed to trigger clustering update: {e}")
    
    async def _get_clustering_insights(self, brand_id: Optional[str]) -> Dict[str, Any]:
        """Get insights about memory clustering."""
        try:
            async with get_db_session() as session:
                # Count clusters
                cluster_query = select(func.count()).select_from(MemoryCluster)
                if brand_id:
                    cluster_query = cluster_query.where(MemoryCluster.brand_id == uuid.UUID(brand_id))
                
                cluster_count = await session.scalar(cluster_query)
                
                # Get cluster size distribution
                size_query = (
                    select(MemoryCluster.cluster_size, func.count())
                    .group_by(MemoryCluster.cluster_size)
                )
                if brand_id:
                    size_query = size_query.where(MemoryCluster.brand_id == uuid.UUID(brand_id))
                
                size_distribution = await session.execute(size_query)
                
                return {
                    'total_clusters': cluster_count,
                    'size_distribution': dict(size_distribution.all())
                }
        
        except Exception as e:
            logger.error(f"Failed to get clustering insights: {e}")
            return {}
    
    async def _periodic_cluster_update(self):
        """Periodic background task to update memory clusters."""
        while True:
            try:
                await asyncio.sleep(self.cluster_update_interval)
                
                # Get memories that need clustering
                queue_members = await self.redis_manager.get_set("clustering_queue")
                
                if queue_members:
                    logger.info(f"Processing {len(queue_members)} memories for clustering")
                    
                    # Process clustering (simplified implementation)
                    for memory_id in queue_members[:10]:  # Process in batches
                        await self._process_memory_clustering(memory_id)
                        await self.redis_manager.remove_from_set("clustering_queue", memory_id)
                
            except Exception as e:
                logger.error(f"Error in periodic cluster update: {e}")
    
    async def _periodic_memory_cleanup(self):
        """Periodic cleanup of old or low-importance memories."""
        while True:
            try:
                await asyncio.sleep(3600 * 24)  # Daily cleanup
                
                # Cleanup logic would go here
                # For now, just log
                logger.info("Performing periodic memory cleanup")
                
            except Exception as e:
                logger.error(f"Error in periodic memory cleanup: {e}")
    
    async def _process_memory_clustering(self, memory_id: str):
        """Process clustering for a specific memory."""
        try:
            # Simplified clustering implementation
            # In a full implementation, this would use ML clustering algorithms
            logger.debug(f"Processing clustering for memory {memory_id}")
            
        except Exception as e:
            logger.error(f"Failed to process memory clustering: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the memory manager."""
        try:
            health = {
                'status': 'healthy',
                'embedding_service': await self.embedding_service.health_check(),
                'knowledge_graph_service': await self.knowledge_graph_service.health_check()
            }
            
            # Check database connectivity
            try:
                async with get_db_session() as session:
                    result = await session.execute(select(func.count()).select_from(MemoryNode))
                    memory_count = result.scalar()
                    health['memory_count'] = memory_count
                    health['database'] = 'connected'
            except Exception as e:
                health['database'] = f'error: {str(e)}'
            
            # Check Redis connectivity
            health['redis'] = 'connected' if await self.redis_manager.health_check() else 'disconnected'
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }