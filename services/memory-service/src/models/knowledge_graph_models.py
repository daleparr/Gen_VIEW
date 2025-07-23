"""
Knowledge Graph Models for KSE Memory Service
Handles temporal knowledge graphs, concept relationships, and reasoning patterns
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


class ConceptNode(Base):
    """
    Represents abstract concepts in the knowledge graph.
    These are higher-level semantic entities that can be associated with memory nodes.
    """
    __tablename__ = "concept_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Concept identification
    concept_name = Column(String(255), nullable=False)
    concept_type = Column(String(100), nullable=False)  # style, color, material, silhouette, etc.
    concept_category = Column(String(100))  # fashion, aesthetic, technical, etc.
    
    # Concept properties
    description = Column(Text)
    properties = Column(JSON, default=dict)
    aliases = Column(ARRAY(String), default=list)
    
    # Semantic representation
    embedding_vector = Column(JSON)  # Concept embedding
    embedding_model = Column(String(100))
    
    # Temporal dynamics
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    trend_score = Column(Float, default=0.0)  # How trending this concept is
    seasonality = Column(JSON, default=dict)  # Seasonal patterns
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    popularity_score = Column(Float, default=0.0)
    
    # Domain context
    domain = Column(String(50), default="fashion")
    brand_specific = Column(Boolean, default=False)
    brand_id = Column(UUID(as_uuid=True))
    
    # Relationships
    concept_relationships = relationship("ConceptRelationship", 
                                       foreign_keys="ConceptRelationship.source_concept_id",
                                       back_populates="source_concept")
    
    # Indexes
    __table_args__ = (
        Index('idx_concept_name', 'concept_name'),
        Index('idx_concept_type', 'concept_type'),
        Index('idx_concept_category', 'concept_category'),
        Index('idx_concept_trend', 'trend_score'),
        Index('idx_concept_brand', 'brand_id'),
        UniqueConstraint('concept_name', 'concept_type', 'brand_id', name='uq_concept_brand'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'concept_name': self.concept_name,
            'concept_type': self.concept_type,
            'concept_category': self.concept_category,
            'description': self.description,
            'properties': self.properties,
            'aliases': self.aliases,
            'embedding_model': self.embedding_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'trend_score': self.trend_score,
            'seasonality': self.seasonality,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'popularity_score': self.popularity_score,
            'domain': self.domain,
            'brand_specific': self.brand_specific,
            'brand_id': str(self.brand_id) if self.brand_id else None,
        }


class ConceptRelationship(Base):
    """
    Relationships between concepts in the knowledge graph.
    Represents semantic, temporal, and causal relationships.
    """
    __tablename__ = "concept_relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source and target concepts
    source_concept_id = Column(UUID(as_uuid=True), ForeignKey('concept_nodes.id'), nullable=False)
    target_concept_id = Column(UUID(as_uuid=True), ForeignKey('concept_nodes.id'), nullable=False)
    
    # Relationship properties
    relationship_type = Column(String(50), nullable=False)  # is_a, part_of, similar_to, causes, etc.
    relationship_strength = Column(Float, default=0.0)  # 0-1 strength
    confidence = Column(Float, default=0.0)  # Confidence in relationship
    
    # Directional properties
    is_bidirectional = Column(Boolean, default=False)
    inverse_relationship = Column(String(50))  # Inverse relationship type
    
    # Temporal dynamics
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_reinforced = Column(DateTime, default=func.now())
    reinforcement_count = Column(Integer, default=1)
    temporal_pattern = Column(JSON, default=dict)  # When this relationship is strongest
    
    # Context and metadata
    context_metadata = Column(JSON, default=dict)
    evidence_sources = Column(ARRAY(String), default=list)  # Sources that support this relationship
    
    # Domain specificity
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    
    # Relationships
    source_concept = relationship("ConceptNode", foreign_keys=[source_concept_id])
    target_concept = relationship("ConceptNode", foreign_keys=[target_concept_id])
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('source_concept_id', 'target_concept_id', 'relationship_type'),
        Index('idx_rel_source', 'source_concept_id'),
        Index('idx_rel_target', 'target_concept_id'),
        Index('idx_rel_type', 'relationship_type'),
        Index('idx_rel_strength', 'relationship_strength'),
        Index('idx_rel_brand', 'brand_id'),
    )


class TemporalPattern(Base):
    """
    Temporal patterns and trends in the knowledge graph.
    Tracks how concepts and relationships change over time.
    """
    __tablename__ = "temporal_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Pattern identification
    pattern_name = Column(String(255), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # seasonal, cyclical, trending, declining
    
    # Associated entities
    entity_type = Column(String(50), nullable=False)  # concept, relationship, memory
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Pattern properties
    pattern_data = Column(JSON, default=dict)  # Time series data, frequencies, etc.
    strength = Column(Float, default=0.0)  # Pattern strength
    confidence = Column(Float, default=0.0)  # Confidence in pattern
    
    # Temporal bounds
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    peak_periods = Column(JSON, default=list)  # When pattern peaks
    
    # Pattern metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_validated = Column(DateTime)
    
    # Context
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    metadata = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_pattern_type', 'pattern_type'),
        Index('idx_pattern_entity', 'entity_type', 'entity_id'),
        Index('idx_pattern_strength', 'strength'),
        Index('idx_pattern_brand', 'brand_id'),
        Index('idx_pattern_dates', 'start_date', 'end_date'),
    )


class ReasoningRule(Base):
    """
    Rules for reasoning and inference in the knowledge graph.
    Defines how to derive new knowledge from existing patterns.
    """
    __tablename__ = "reasoning_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # inference, constraint, transformation
    rule_category = Column(String(100))  # temporal, semantic, causal, etc.
    
    # Rule definition
    rule_logic = Column(JSON, nullable=False)  # Formal rule representation
    conditions = Column(JSON, default=list)  # Conditions for rule application
    actions = Column(JSON, default=list)  # Actions to take when rule fires
    
    # Rule properties
    priority = Column(Integer, default=0)  # Rule priority for conflict resolution
    confidence_threshold = Column(Float, default=0.5)  # Minimum confidence to apply
    is_active = Column(Boolean, default=True)
    
    # Performance metrics
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    application_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    last_applied = Column(DateTime)
    
    # Context
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    metadata = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_rule_type', 'rule_type'),
        Index('idx_rule_category', 'rule_category'),
        Index('idx_rule_active', 'is_active'),
        Index('idx_rule_priority', 'priority'),
        Index('idx_rule_brand', 'brand_id'),
    )


class InferenceResult(Base):
    """
    Results of reasoning and inference operations.
    Tracks what new knowledge was derived and how.
    """
    __tablename__ = "inference_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Inference context
    inference_session_id = Column(String(255))  # Groups related inferences
    rule_id = Column(UUID(as_uuid=True), ForeignKey('reasoning_rules.id'))
    
    # Input and output
    input_entities = Column(JSON, default=list)  # What entities were used as input
    output_entities = Column(JSON, default=list)  # What new entities were created/modified
    inference_type = Column(String(50))  # concept_creation, relationship_inference, etc.
    
    # Results
    result_data = Column(JSON, default=dict)  # The actual inference results
    confidence_score = Column(Float, default=0.0)
    evidence_strength = Column(Float, default=0.0)
    
    # Validation
    created_at = Column(DateTime, default=func.now(), nullable=False)
    validated_at = Column(DateTime)
    validation_result = Column(String(50))  # confirmed, rejected, pending
    validation_feedback = Column(JSON, default=dict)
    
    # Context
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    metadata = Column(JSON, default=dict)
    
    # Relationships
    reasoning_rule = relationship("ReasoningRule")
    
    # Indexes
    __table_args__ = (
        Index('idx_inference_session', 'inference_session_id'),
        Index('idx_inference_rule', 'rule_id'),
        Index('idx_inference_type', 'inference_type'),
        Index('idx_inference_confidence', 'confidence_score'),
        Index('idx_inference_validation', 'validation_result'),
        Index('idx_inference_brand', 'brand_id'),
    )


class KnowledgeGraphSnapshot(Base):
    """
    Snapshots of the knowledge graph state at specific points in time.
    Used for versioning, rollback, and temporal analysis.
    """
    __tablename__ = "knowledge_graph_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Snapshot metadata
    snapshot_name = Column(String(255))
    snapshot_type = Column(String(50), default="periodic")  # periodic, manual, pre_update, etc.
    description = Column(Text)
    
    # Snapshot data (compressed JSON)
    concepts_snapshot = Column(JSON)  # Serialized concept nodes
    relationships_snapshot = Column(JSON)  # Serialized relationships
    patterns_snapshot = Column(JSON)  # Serialized temporal patterns
    
    # Statistics
    concept_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    pattern_count = Column(Integer, default=0)
    
    # Temporal information
    created_at = Column(DateTime, default=func.now(), nullable=False)
    snapshot_timestamp = Column(DateTime, default=func.now())
    
    # Context
    domain = Column(String(50), default="fashion")
    brand_id = Column(UUID(as_uuid=True))
    version = Column(String(50))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_snapshot_type', 'snapshot_type'),
        Index('idx_snapshot_timestamp', 'snapshot_timestamp'),
        Index('idx_snapshot_brand', 'brand_id'),
        Index('idx_snapshot_version', 'version'),
    )