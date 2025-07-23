"""
Fashion domain models for products, collections, and design DNA
Supporting the fashion-specific functionality while abstracting KSE substrate
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from ..core.database import Base


class GarmentType(str, Enum):
    """Enumeration of garment types."""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"
    UNDERWEAR = "underwear"


class Season(str, Enum):
    """Enumeration of fashion seasons."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    RESORT = "resort"
    PRE_FALL = "pre_fall"


class Brand(Base):
    """Brand model for fashion houses and labels."""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    
    # Brand DNA and characteristics
    design_dna = Column(JSON)  # Core design principles and aesthetic
    target_demographic = Column(JSON)  # Age, income, lifestyle
    brand_values = Column(JSON)  # Sustainability, luxury, accessibility
    
    # Visual characteristics
    color_palette = Column(JSON)  # Preferred colors and combinations
    silhouette_preferences = Column(JSON)  # Fit preferences and shapes
    fabric_preferences = Column(JSON)  # Material preferences and quality
    
    # Market positioning
    price_range = Column(JSON)  # Min/max pricing by category
    market_segment = Column(String(100))  # luxury, premium, mid-market, fast-fashion
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    collections = relationship("Collection", back_populates="brand")
    products = relationship("Product", back_populates="brand")


class Collection(Base):
    """Fashion collection model (seasonal or thematic groupings)."""
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Collection metadata
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    season = Column(String(50))  # Season enum
    year = Column(Integer)
    collection_type = Column(String(100))  # main, capsule, collaboration
    
    # Design theme and inspiration
    theme = Column(String(255))
    inspiration = Column(Text)
    mood_board = Column(JSON)  # References, colors, textures
    
    # Generation parameters
    generation_config = Column(JSON)  # AI generation settings
    design_constraints = Column(JSON)  # Rules and limitations
    target_pieces = Column(Integer, default=5)  # Number of pieces to generate
    
    # Status and workflow
    status = Column(String(50), default="draft")  # draft, generating, review, approved
    generation_progress = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    brand = relationship("Brand", back_populates="collections")
    products = relationship("Product", back_populates="collection")
    generations = relationship("GenerationJob", back_populates="collection")


class Product(Base):
    """Individual fashion product/garment model."""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Product categorization
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    garment_type = Column(String(50), nullable=False)  # GarmentType enum
    category = Column(String(100))  # More specific categorization
    
    # Design specifications
    design_dna = Column(JSON)  # Product-specific design DNA
    silhouette = Column(JSON)  # Shape, fit, proportions
    materials = Column(JSON)  # Fabric types, weights, finishes
    colors = Column(JSON)  # Color variations and combinations
    patterns = Column(JSON)  # Prints, textures, embellishments
    
    # Technical specifications
    sizes = Column(JSON)  # Available size range
    measurements = Column(JSON)  # Detailed measurements by size
    construction_details = Column(JSON)  # Seams, closures, techniques
    
    # Pricing and production
    target_price = Column(Float)
    cost_estimate = Column(Float)
    production_complexity = Column(Float)  # 0-1 scale
    
    # AI generation metadata
    generated_by_ai = Column(Boolean, default=False)
    generation_parameters = Column(JSON)
    parent_generation_id = Column(UUID(as_uuid=True), ForeignKey("generation_jobs.id"))
    
    # Quality and performance metrics
    design_score = Column(Float)  # AI-assessed design quality
    brand_alignment_score = Column(Float)  # How well it fits brand DNA
    commercial_viability_score = Column(Float)  # Predicted market success
    
    # Status and workflow
    status = Column(String(50), default="concept")  # concept, designed, prototyped, production
    approval_status = Column(String(50), default="pending")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    brand = relationship("Brand", back_populates="products")
    collection = relationship("Collection", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    variations = relationship("ProductVariation", back_populates="product")


class ProductImage(Base):
    """Product image storage and metadata."""
    __tablename__ = "product_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Image metadata
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(50))  # sketch, render, photo, technical
    view_angle = Column(String(50))  # front, back, side, detail
    
    # Rendering metadata (for AI-generated images)
    rendered_by_ai = Column(Boolean, default=False)
    rendering_parameters = Column(JSON)
    lighting_setup = Column(JSON)
    background_type = Column(String(100))
    
    # Quality metrics
    image_quality_score = Column(Float)
    photorealism_score = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    product = relationship("Product", back_populates="images")


class ProductVariation(Base):
    """Product variations (colors, sizes, materials)."""
    __tablename__ = "product_variations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Variation details
    variation_type = Column(String(50))  # color, size, material
    variation_value = Column(String(255))
    variation_data = Column(JSON)  # Additional variation-specific data
    
    # Pricing and availability
    price_modifier = Column(Float, default=0.0)  # Price difference from base
    availability = Column(Boolean, default=True)
    
    # Visual representation
    image_url = Column(String(500))
    color_hex = Column(String(7))  # For color variations
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="variations")


class DesignDNA(Base):
    """Design DNA tracking for temporal coherence and brand consistency."""
    __tablename__ = "design_dna"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # DNA identification
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    # DNA characteristics
    aesthetic_vector = Column(JSON)  # High-dimensional aesthetic representation
    style_attributes = Column(JSON)  # Structured style characteristics
    color_dna = Column(JSON)  # Color preferences and combinations
    silhouette_dna = Column(JSON)  # Shape and fit preferences
    material_dna = Column(JSON)  # Fabric and texture preferences
    
    # Temporal tracking
    evolution_history = Column(JSON)  # How DNA has changed over time
    influence_sources = Column(JSON)  # What influenced this DNA
    
    # Performance metrics
    commercial_success_correlation = Column(Float)
    brand_alignment_strength = Column(Float)
    uniqueness_score = Column(Float)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    version = Column(Integer, default=1)