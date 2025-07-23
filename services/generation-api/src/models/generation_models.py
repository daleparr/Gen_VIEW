"""
AI Generation models for tracking generation jobs, parameters, and results
Supports both synchronous and asynchronous generation workflows
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from ..core.database import Base


class GenerationStatus(str, Enum):
    """Enumeration of generation job statuses."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class GenerationType(str, Enum):
    """Enumeration of generation types."""
    CAPSULE_COLLECTION = "capsule_collection"
    SINGLE_PRODUCT = "single_product"
    PRODUCT_VARIATION = "product_variation"
    STYLE_TRANSFER = "style_transfer"
    DESIGN_EVOLUTION = "design_evolution"


class ModelType(str, Enum):
    """Enumeration of AI model types."""
    STYLEGAN3 = "stylegan3"
    STABLE_DIFFUSION = "stable_diffusion"
    CLIP = "clip"
    NERF = "nerf"
    CUSTOM = "custom"


class GenerationJob(Base):
    """AI generation job tracking and management."""
    __tablename__ = "generation_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    generation_type = Column(String(50), nullable=False)  # GenerationType enum
    
    # Relationships
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Generation parameters
    input_parameters = Column(JSON, nullable=False)  # All input parameters
    model_config = Column(JSON)  # Model-specific configuration
    generation_constraints = Column(JSON)  # Rules and limitations
    
    # Multi-modal inputs
    text_prompt = Column(Text)
    reference_images = Column(ARRAY(String))  # URLs to reference images
    style_references = Column(JSON)  # Style transfer references
    design_dna_input = Column(JSON)  # Design DNA constraints
    
    # AI model configuration
    primary_model = Column(String(50))  # ModelType enum
    model_version = Column(String(100))
    secondary_models = Column(JSON)  # Additional models used
    
    # Generation settings
    num_outputs = Column(Integer, default=1)
    quality_level = Column(String(50), default="standard")  # draft, standard, high, ultra
    creativity_level = Column(Float, default=0.7)  # 0-1 scale
    brand_adherence = Column(Float, default=0.8)  # 0-1 scale
    
    # Execution tracking
    status = Column(String(50), default="pending")  # GenerationStatus enum
    progress = Column(Float, default=0.0)  # 0-1 completion percentage
    current_step = Column(String(255))  # Current processing step
    
    # Timing
    queued_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_completion = Column(DateTime(timezone=True))
    
    # Performance metrics
    generation_time = Column(Float)  # Seconds
    compute_cost = Column(Float)  # Estimated compute cost
    memory_usage = Column(Float)  # Peak memory usage in GB
    gpu_utilization = Column(Float)  # Average GPU utilization
    
    # Results
    output_count = Column(Integer, default=0)
    success_rate = Column(Float)  # Percentage of successful outputs
    average_quality_score = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    collection = relationship("Collection", back_populates="generations")
    outputs = relationship("GenerationOutput", back_populates="job")
    feedback = relationship("GenerationFeedback", back_populates="job")


class GenerationOutput(Base):
    """Individual outputs from generation jobs."""
    __tablename__ = "generation_outputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("generation_jobs.id"), nullable=False)
    
    # Output identification
    output_index = Column(Integer, nullable=False)  # Index within job
    output_type = Column(String(50))  # image, design, specification
    
    # Generated content
    content_url = Column(String(500))  # URL to generated content
    content_data = Column(JSON)  # Structured data representation
    thumbnail_url = Column(String(500))  # Preview image URL
    
    # Generation metadata
    generation_parameters = Column(JSON)  # Parameters used for this output
    model_outputs = Column(JSON)  # Raw model outputs and intermediate results
    processing_steps = Column(JSON)  # Step-by-step processing log
    
    # Quality assessment
    quality_score = Column(Float)  # Overall quality assessment
    technical_quality = Column(Float)  # Technical execution quality
    aesthetic_quality = Column(Float)  # Aesthetic appeal
    brand_alignment = Column(Float)  # Alignment with brand DNA
    commercial_viability = Column(Float)  # Predicted market success
    
    # CLIP-based assessments
    clip_score = Column(Float)  # CLIP similarity to prompt
    style_consistency = Column(Float)  # Consistency with style references
    novelty_score = Column(Float)  # How novel/creative the output is
    
    # User interaction
    user_rating = Column(Float)  # User-provided rating
    is_favorite = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    
    # Product association
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))  # If converted to product
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("GenerationJob", back_populates="outputs")
    feedback = relationship("GenerationFeedback", back_populates="output")


class GenerationFeedback(Base):
    """User feedback on generation outputs for learning and improvement."""
    __tablename__ = "generation_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("generation_jobs.id"))
    output_id = Column(UUID(as_uuid=True), ForeignKey("generation_outputs.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Feedback content
    rating = Column(Float, nullable=False)  # 1-5 scale
    feedback_type = Column(String(50))  # like, dislike, detailed, commercial
    
    # Detailed feedback
    comments = Column(Text)
    specific_aspects = Column(JSON)  # Detailed aspect ratings
    improvement_suggestions = Column(JSON)  # Specific improvement suggestions
    
    # Commercial feedback
    would_purchase = Column(Boolean)
    price_expectation = Column(Float)
    target_market_fit = Column(Float)
    
    # Behavioral data
    time_spent_viewing = Column(Float)  # Seconds
    interaction_count = Column(Integer)  # Number of interactions
    shared = Column(Boolean, default=False)
    
    # Learning integration
    feedback_weight = Column(Float, default=1.0)  # Weight for learning algorithms
    used_for_training = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("GenerationJob", back_populates="feedback")
    output = relationship("GenerationOutput", back_populates="feedback")


class ModelPerformance(Base):
    """Model performance tracking and optimization."""
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model identification
    model_type = Column(String(50), nullable=False)  # ModelType enum
    model_version = Column(String(100), nullable=False)
    model_config_hash = Column(String(64))  # Hash of configuration
    
    # Performance metrics
    average_generation_time = Column(Float)
    average_quality_score = Column(Float)
    success_rate = Column(Float)
    user_satisfaction = Column(Float)
    
    # Resource utilization
    average_memory_usage = Column(Float)
    average_gpu_utilization = Column(Float)
    average_compute_cost = Column(Float)
    
    # Quality metrics by category
    technical_quality_avg = Column(Float)
    aesthetic_quality_avg = Column(Float)
    brand_alignment_avg = Column(Float)
    commercial_viability_avg = Column(Float)
    
    # Usage statistics
    total_generations = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)
    failed_generations = Column(Integer, default=0)
    
    # Time period
    measurement_start = Column(DateTime(timezone=True))
    measurement_end = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GenerationQueue(Base):
    """Queue management for generation jobs."""
    __tablename__ = "generation_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("generation_jobs.id"), nullable=False)
    
    # Queue management
    priority = Column(Integer, default=5)  # 1-10 scale, higher = more priority
    queue_position = Column(Integer)
    estimated_wait_time = Column(Float)  # Seconds
    
    # Resource requirements
    required_gpu_memory = Column(Float)  # GB
    required_compute_time = Column(Float)  # Estimated seconds
    required_models = Column(ARRAY(String))  # Required model types
    
    # Scheduling
    scheduled_start = Column(DateTime(timezone=True))
    resource_allocation = Column(JSON)  # Allocated resources
    
    # Status
    queue_status = Column(String(50), default="waiting")  # waiting, allocated, processing
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())