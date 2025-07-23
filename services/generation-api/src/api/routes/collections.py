"""
Collections API routes for managing fashion collections, brands, and products
Provides CRUD operations and collection-specific functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ...core.database import get_db
from ...models.fashion_models import Brand, Collection, Product, GarmentType, Season
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

router = APIRouter()


class BrandCreate(BaseModel):
    """Brand creation model."""
    name: str = Field(..., description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    design_dna: Optional[Dict[str, Any]] = Field(None, description="Core design principles")
    target_demographic: Optional[Dict[str, Any]] = Field(None, description="Target demographic")
    brand_values: Optional[Dict[str, Any]] = Field(None, description="Brand values")
    color_palette: Optional[Dict[str, Any]] = Field(None, description="Preferred colors")
    silhouette_preferences: Optional[Dict[str, Any]] = Field(None, description="Fit preferences")
    fabric_preferences: Optional[Dict[str, Any]] = Field(None, description="Material preferences")
    price_range: Optional[Dict[str, Any]] = Field(None, description="Price range by category")
    market_segment: Optional[str] = Field(None, description="Market segment")


class BrandResponse(BaseModel):
    """Brand response model."""
    id: str
    name: str
    description: Optional[str] = None
    design_dna: Optional[Dict[str, Any]] = None
    target_demographic: Optional[Dict[str, Any]] = None
    brand_values: Optional[Dict[str, Any]] = None
    color_palette: Optional[Dict[str, Any]] = None
    silhouette_preferences: Optional[Dict[str, Any]] = None
    fabric_preferences: Optional[Dict[str, Any]] = None
    price_range: Optional[Dict[str, Any]] = None
    market_segment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class CollectionCreate(BaseModel):
    """Collection creation model."""
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    brand_id: str = Field(..., description="Brand ID")
    season: Optional[str] = Field(None, description="Season")
    year: Optional[int] = Field(None, description="Year")
    collection_type: Optional[str] = Field("main", description="Collection type")
    theme: Optional[str] = Field(None, description="Theme")
    inspiration: Optional[str] = Field(None, description="Inspiration")
    mood_board: Optional[Dict[str, Any]] = Field(None, description="Mood board data")
    generation_config: Optional[Dict[str, Any]] = Field(None, description="AI generation settings")
    design_constraints: Optional[Dict[str, Any]] = Field(None, description="Design constraints")
    target_pieces: int = Field(5, description="Number of pieces to generate")


class CollectionResponse(BaseModel):
    """Collection response model."""
    id: str
    name: str
    description: Optional[str] = None
    brand_id: str
    season: Optional[str] = None
    year: Optional[int] = None
    collection_type: Optional[str] = None
    theme: Optional[str] = None
    inspiration: Optional[str] = None
    mood_board: Optional[Dict[str, Any]] = None
    generation_config: Optional[Dict[str, Any]] = None
    design_constraints: Optional[Dict[str, Any]] = None
    target_pieces: int
    status: str
    generation_progress: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Product response model."""
    id: str
    name: str
    description: Optional[str] = None
    brand_id: str
    collection_id: Optional[str] = None
    garment_type: str
    category: Optional[str] = None
    design_dna: Optional[Dict[str, Any]] = None
    silhouette: Optional[Dict[str, Any]] = None
    materials: Optional[Dict[str, Any]] = None
    colors: Optional[Dict[str, Any]] = None
    patterns: Optional[Dict[str, Any]] = None
    target_price: Optional[float] = None
    generated_by_ai: bool
    design_score: Optional[float] = None
    brand_alignment_score: Optional[float] = None
    commercial_viability_score: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Brand endpoints
@router.post("/brands", response_model=BrandResponse)
async def create_brand(brand: BrandCreate, db: AsyncSession = Depends(get_db)):
    """Create a new brand."""
    try:
        db_brand = Brand(
            id=uuid.uuid4(),
            **brand.dict()
        )
        
        db.add(db_brand)
        await db.commit()
        await db.refresh(db_brand)
        
        return BrandResponse.from_orm(db_brand)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create brand: {str(e)}")


@router.get("/brands", response_model=List[BrandResponse])
async def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    market_segment: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List brands with optional filtering."""
    try:
        query = select(Brand).where(Brand.is_active == is_active)
        
        if market_segment:
            query = query.where(Brand.market_segment == market_segment)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        brands = result.scalars().all()
        
        return [BrandResponse.from_orm(brand) for brand in brands]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list brands: {str(e)}")


@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific brand by ID."""
    try:
        result = await db.execute(select(Brand).where(Brand.id == brand_id))
        brand = result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return BrandResponse.from_orm(brand)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand: {str(e)}")


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(brand_id: str, brand_update: BrandCreate, db: AsyncSession = Depends(get_db)):
    """Update a brand."""
    try:
        result = await db.execute(select(Brand).where(Brand.id == brand_id))
        db_brand = result.scalar_one_or_none()
        
        if not db_brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        for field, value in brand_update.dict(exclude_unset=True).items():
            setattr(db_brand, field, value)
        
        await db.commit()
        await db.refresh(db_brand)
        
        return BrandResponse.from_orm(db_brand)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update brand: {str(e)}")


# Collection endpoints
@router.post("/collections", response_model=CollectionResponse)
async def create_collection(collection: CollectionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new collection."""
    try:
        # Verify brand exists
        result = await db.execute(select(Brand).where(Brand.id == collection.brand_id))
        brand = result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        db_collection = Collection(
            id=uuid.uuid4(),
            **collection.dict()
        )
        
        db.add(db_collection)
        await db.commit()
        await db.refresh(db_collection)
        
        return CollectionResponse.from_orm(db_collection)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")


@router.get("/collections", response_model=List[CollectionResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    brand_id: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List collections with optional filtering."""
    try:
        query = select(Collection)
        
        filters = []
        if brand_id:
            filters.append(Collection.brand_id == brand_id)
        if season:
            filters.append(Collection.season == season)
        if year:
            filters.append(Collection.year == year)
        if status:
            filters.append(Collection.status == status)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        collections = result.scalars().all()
        
        return [CollectionResponse.from_orm(collection) for collection in collections]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
async def get_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific collection by ID."""
    try:
        result = await db.execute(select(Collection).where(Collection.id == collection_id))
        collection = result.scalar_one_or_none()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return CollectionResponse.from_orm(collection)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection: {str(e)}")


@router.get("/collections/{collection_id}/products", response_model=List[ProductResponse])
async def get_collection_products(
    collection_id: str, 
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all products in a collection."""
    try:
        # Verify collection exists
        result = await db.execute(select(Collection).where(Collection.id == collection_id))
        collection = result.scalar_one_or_none()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get products
        query = select(Product).where(Product.collection_id == collection_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        products = result.scalars().all()
        
        return [ProductResponse.from_orm(product) for product in products]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection products: {str(e)}")


# Product endpoints
@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    brand_id: Optional[str] = Query(None),
    collection_id: Optional[str] = Query(None),
    garment_type: Optional[str] = Query(None),
    generated_by_ai: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List products with optional filtering."""
    try:
        query = select(Product).where(Product.is_active == True)
        
        filters = []
        if brand_id:
            filters.append(Product.brand_id == brand_id)
        if collection_id:
            filters.append(Product.collection_id == collection_id)
        if garment_type:
            filters.append(Product.garment_type == garment_type)
        if generated_by_ai is not None:
            filters.append(Product.generated_by_ai == generated_by_ai)
        if status:
            filters.append(Product.status == status)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        products = result.scalars().all()
        
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific product by ID."""
    try:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductResponse.from_orm(product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")


@router.get("/brands/{brand_id}/collections", response_model=List[CollectionResponse])
async def get_brand_collections(
    brand_id: str, 
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all collections for a specific brand."""
    try:
        # Verify brand exists
        result = await db.execute(select(Brand).where(Brand.id == brand_id))
        brand = result.scalar_one_or_none()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Get collections
        query = select(Collection).where(Collection.brand_id == brand_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        collections = result.scalars().all()
        
        return [CollectionResponse.from_orm(collection) for collection in collections]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand collections: {str(e)}")


@router.get("/search/products")
async def search_products(
    q: str = Query(..., description="Search query"),
    brand_id: Optional[str] = Query(None),
    garment_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Search products by name, description, or other attributes."""
    try:
        # Basic text search implementation
        # In a production system, you might use full-text search or Elasticsearch
        query = select(Product).where(
            and_(
                Product.is_active == True,
                or_(
                    Product.name.ilike(f"%{q}%"),
                    Product.description.ilike(f"%{q}%"),
                    Product.category.ilike(f"%{q}%")
                )
            )
        )
        
        filters = []
        if brand_id:
            filters.append(Product.brand_id == brand_id)
        if garment_type:
            filters.append(Product.garment_type == garment_type)
        if min_price:
            filters.append(Product.target_price >= min_price)
        if max_price:
            filters.append(Product.target_price <= max_price)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        products = result.scalars().all()
        
        return {
            "query": q,
            "total_found": len(products),
            "products": [ProductResponse.from_orm(product) for product in products]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")


@router.get("/stats/summary")
async def get_stats_summary(db: AsyncSession = Depends(get_db)):
    """Get summary statistics for the collections system."""
    try:
        # Get counts for each entity type
        brands_result = await db.execute(select(Brand).where(Brand.is_active == True))
        brands_count = len(brands_result.scalars().all())
        
        collections_result = await db.execute(select(Collection))
        collections_count = len(collections_result.scalars().all())
        
        products_result = await db.execute(select(Product).where(Product.is_active == True))
        products_count = len(products_result.scalars().all())
        
        ai_products_result = await db.execute(
            select(Product).where(
                and_(Product.is_active == True, Product.generated_by_ai == True)
            )
        )
        ai_products_count = len(ai_products_result.scalars().all())
        
        return {
            "brands": brands_count,
            "collections": collections_count,
            "products": products_count,
            "ai_generated_products": ai_products_count,
            "ai_generation_rate": ai_products_count / products_count if products_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")