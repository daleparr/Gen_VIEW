"""
Data models for KSE Memory Service
Handles memory nodes, temporal context, and retrieval patterns
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, DateTime, Text, JSON, Float, Integer, 
    Boolean, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class MemoryNode(Base):
    """
    Core memory node storing contextual information with embeddings.
    Represents a single piece of knowledge in the KSE substrate.
    """
    __tablename__ = "memory_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Content and metadata
    content_type = Column(String(50), nullable=False)  # text, image, audio, multimodal
    content_text = Column(Text)
    content_metadata = Column(JSON, default=dict)
    
    # Embeddings (stored as JSON for compatibility)
    embedding_vector = Column(JSON)  # Will store list of floats
    embedding_model = Column(String(100))
    embedding_dimension = Column(Integer)
    
    # Temporal context
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    temporal_context = Column(JSON, default=dict)  # Season, trend cycle, etc.
    
    # Relevance and importance
    importance_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Relationships and tags
    tags = Column(ARRAY(String), default=list)
    category = Column(String(100))
    subcategory = Column(String(100))
    
    # Brand and domain context
    brand_id = Column(UUID(as_uuid=True))
    domain = Column(String(50), default="fashion")  # fashion, general, etc.
    
    # Source information
    source_type = Column(String(50))  # generation, feedback, external
    source_id = Column(String(255))
    source_metadata = Column(JSON, default=dict)
    
    # Relationships
    memory_associations = relationship("MemoryAssociation", back_populates="source_node")
    feedback_entries = relationship("MemoryFeedback", back_populates="memory_node")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_memory_content_type', 'content_type'),
        Index('idx_memory_brand_id', 'brand_id'),
        Index('idx_memory_category', 'category'),
        Index('idx_memory_created_at', 'created_at'),
        Index('idx_memory_importance', 'importance_score'),
        Index('idx_memory_tags', 'tags', postgresql_using='gin'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'content_type': self.content_type,
            'content_text': self.content_text,
            'content_metadata': self.content_metadata,
            'embedding_model': self.embedding_model,
            'embedding_dimension': self.embedding_dimension,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'temporal_context': self.temporal_context,
            'importance_score': self.importance_score,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'tags': self.tags,
            'category': self.category,
            'subcategory': self.subcategory,
            'brand_id': str(self.brand_id) if self.brand_id else None,
            'domain': self.domain,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_metadata': self.source_metadata,
        }


class MemoryAssociation(Base):
    """
    Associations between memory nodes representing relationships.
    Forms the basis of the knowledge graph structure.
    """
    __tablename__ = "memory_associations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source and target nodes
    source_node_id = Column(UUID(as_uuid=True), ForeignKey('memory_nodes.id'), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey('memory_nodes.id'), nullable=False)
    
    # Association metadata
    association_type = Column(String(50), nullable=False)  # similarity, sequence, causation, etc.
    strength = Column(Float, default=0.0)  # Association strength 0-1
    confidence = Column(Float, default=0.0)  # Confidence in association 0-1
    
    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_reinforced = Column(DateTime, default=func.now())
    reinforcement_count = Column(Integer, default=1)
    
    # Context
    context_metadata = Column(JSON, default=dict)
    domain_specific_data = Column(JSON, default=dict)
    
    # Relationships
    source_node = relationship("MemoryNode", foreign_keys=[source_node_id])
    target_node = relationship("MemoryNode", foreign_keys=[target_node_id])
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('source_node_id', 'target_node_id', 'association_type'),
        Index('idx_association_source', 'source_node_id'),
        Index('idx_association_target', 'target_node_id'),
        Index('idx_association_type', 'association_type'),
        Index('idx_association_strength', 'strength'),
    )


class MemoryContext(Base):
    """
    Contextual information for memory retrieval and generation.
    Stores session-based and temporal context for better retrieval.
    """
    __tablename__ = "memory_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Context identification
    context_type = Column(String(50), nullable=False)  # session, generation, brand, etc.
    context_id = Column(String(255), nullable=False)  # External ID reference
    
    # Context data
    context_data = Column(JSON, default=dict)
    active_concepts = Column(ARRAY(String), default=list)
    temporal_markers = Column(JSON, default=dict)
    
    # State tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Usage statistics
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_context_type_id', 'context_type', 'context_id'),
        Index('idx_context_active', 'is_active'),
        Index('idx_context_expires', 'expires_at'),
    )


class MemoryFeedback(Base):
    """
    Feedback on memory retrievals and generations.
    Used for reinforcement learning and memory importance scoring.
    """
    __tablename__ = "memory_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to memory node
    memory_node_id = Column(UUID(as_uuid=True), ForeignKey('memory_nodes.id'), nullable=False)
    
    # Feedback data
    feedback_type = Column(String(50), nullable=False)  # positive, negative, neutral
    feedback_score = Column(Float)  # Numeric score if applicable
    feedback_text = Column(Text)
    feedback_metadata = Column(JSON, default=dict)
    
    # Context of feedback
    generation_id = Column(String(255))  # Reference to generation that used this memory
    user_id = Column(String(255))
    session_id = Column(String(255))
    
    # Commercial outcomes
    commercial_impact = Column(JSON, default=dict)  # Sales, engagement, etc.
    outcome_metrics = Column(JSON, default=dict)
    
    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False)
    feedback_timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    memory_node = relationship("MemoryNode", back_populates="feedback_entries")
    
    # Indexes
    __table_args__ = (
        Index('idx_feedback_memory_node', 'memory_node_id'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_generation', 'generation_id'),
        Index('idx_feedback_timestamp', 'feedback_timestamp'),
    )


class MemoryCluster(Base):
    """
    Clusters of related memory nodes for efficient retrieval.
    Represents semantic or temporal groupings of memories.
    """
    __tablename__ = "memory_clusters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Cluster metadata
    cluster_name = Column(String(255))
    cluster_type = Column(String(50), nullable=False)  # semantic, temporal, brand, etc.
    description = Column(Text)
    
    # Cluster properties
    centroid_embedding = Column(JSON)  # Average embedding of cluster members
    cluster_size = Column(Integer, default=0)
    coherence_score = Column(Float, default=0.0)  # How coherent the cluster is
    
    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime)
    
    # Cluster configuration
    max_size = Column(Integer, default=100)
    similarity_threshold = Column(Float, default=0.7)
    
    # Domain context
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    
    # Metadata
    cluster_metadata = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_cluster_type', 'cluster_type'),
        Index('idx_cluster_brand', 'brand_id'),
        Index('idx_cluster_updated', 'updated_at'),
    )


class MemoryClusterMembership(Base):
    """
    Many-to-many relationship between memory nodes and clusters.
    """
    __tablename__ = "memory_cluster_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    memory_node_id = Column(UUID(as_uuid=True), ForeignKey('memory_nodes.id'), nullable=False)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey('memory_clusters.id'), nullable=False)
    
    # Membership properties
    membership_score = Column(Float, default=1.0)  # How well the node fits the cluster
    assigned_at = Column(DateTime, default=func.now(), nullable=False)
    is_core_member = Column(Boolean, default=False)  # Is this a core member of the cluster?
    
    # Relationships
    memory_node = relationship("MemoryNode")
    cluster = relationship("MemoryCluster")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('memory_node_id', 'cluster_id'),
        Index('idx_membership_node', 'memory_node_id'),
        Index('idx_membership_cluster', 'cluster_id'),
        Index('idx_membership_score', 'membership_score'),
    )