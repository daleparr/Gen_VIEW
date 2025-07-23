"""
Generation API routes for AI-powered fashion generation
Supports capsule collection generation, single products, and style variations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from ...services.generation_service import GenerationService
from ...services.model_manager import ModelManager
from ...core.database import get_db
from ...core.redis_client import redis_manager
from ...models.generation_models import GenerationType, GenerationStatus
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class GenerationRequest(BaseModel):
    """Base generation request model."""
    name: str = Field(..., description="Name for the generation job")
    description: Optional[str] = Field(None, description="Description of the generation")
    generation_type: str = Field(..., description="Type of generation")
    
    # Input parameters
    text_prompt: Optional[str] = Field(None, description="Text description/prompt")
    style_references: Optional[List[str]] = Field(None, description="URLs to style reference images")
    brand_id: Optional[str] = Field(None, description="Brand ID for brand-specific generation")
    collection_id: Optional[str] = Field(None, description="Collection ID if part of a collection")
    
    # Generation settings
    num_outputs: int = Field(1, ge=1, le=10, description="Number of outputs to generate")
    quality_level: str = Field("standard", description="Quality level: draft, standard, high, ultra")
    creativity_level: float = Field(0.7, ge=0.0, le=1.0, description="Creativity level (0-1)")
    brand_adherence: float = Field(0.8, ge=0.0, le=1.0, description="Brand adherence level (0-1)")
    
    # Additional parameters
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional generation parameters")


class CapsuleCollectionRequest(GenerationRequest):
    """Capsule collection generation request."""
    generation_type: str = Field("capsule_collection", const=True)
    target_pieces: int = Field(5, ge=3, le=15, description="Number of pieces in the collection")
    season: Optional[str] = Field(None, description="Target season")
    theme: Optional[str] = Field(None, description="Collection theme")
    price_range: Optional[Dict[str, float]] = Field(None, description="Target price range")


class SingleProductRequest(GenerationRequest):
    """Single product generation request."""
    generation_type: str = Field("single_product", const=True)
    garment_type: str = Field(..., description="Type of garment to generate")
    target_price: Optional[float] = Field(None, description="Target price point")
    size_range: Optional[List[str]] = Field(None, description="Target size range")


class StyleTransferRequest(GenerationRequest):
    """Style transfer generation request."""
    generation_type: str = Field("style_transfer", const=True)
    source_image: str = Field(..., description="URL to source image")
    target_style: str = Field(..., description="Target style description or reference")


class GenerationResponse(BaseModel):
    """Generation job response model."""
    job_id: str
    status: str
    message: str
    estimated_completion: Optional[datetime] = None
    progress: float = 0.0


class GenerationStatusResponse(BaseModel):
    """Generation status response model."""
    job_id: str
    status: str
    progress: float
    current_step: Optional[str] = None
    outputs_ready: int = 0
    total_outputs: int
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


class GenerationOutput(BaseModel):
    """Generated output model."""
    output_id: str
    output_index: int
    output_type: str
    content_url: str
    thumbnail_url: Optional[str] = None
    quality_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class GenerationResults(BaseModel):
    """Generation results response."""
    job_id: str
    status: str
    outputs: List[GenerationOutput]
    metadata: Dict[str, Any]


@router.post("/capsule-collection", response_model=GenerationResponse)
async def generate_capsule_collection(
    request: CapsuleCollectionRequest,
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a capsule collection based on the provided parameters.
    This creates a cohesive set of fashion pieces that work together.
    """
    try:
        # Create generation job
        job_id = str(uuid.uuid4())
        
        # Queue the generation task
        background_tasks.add_task(
            generation_service.generate_capsule_collection,
            job_id=job_id,
            request=request,
            db=db
        )
        
        # Store job in Redis for quick status lookup
        await redis_manager.set(
            f"generation_job:{job_id}",
            {
                "status": GenerationStatus.QUEUED,
                "progress": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "request": request.dict()
            },
            expire=3600  # 1 hour
        )
        
        return GenerationResponse(
            job_id=job_id,
            status=GenerationStatus.QUEUED,
            message="Capsule collection generation queued successfully",
            estimated_completion=None,  # Will be calculated by the service
            progress=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue generation: {str(e)}")


@router.post("/single-product", response_model=GenerationResponse)
async def generate_single_product(
    request: SingleProductRequest,
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a single fashion product based on the provided parameters.
    """
    try:
        job_id = str(uuid.uuid4())
        
        background_tasks.add_task(
            generation_service.generate_single_product,
            job_id=job_id,
            request=request,
            db=db
        )
        
        await redis_manager.set(
            f"generation_job:{job_id}",
            {
                "status": GenerationStatus.QUEUED,
                "progress": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "request": request.dict()
            },
            expire=3600
        )
        
        return GenerationResponse(
            job_id=job_id,
            status=GenerationStatus.QUEUED,
            message="Single product generation queued successfully",
            progress=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue generation: {str(e)}")


@router.post("/style-transfer", response_model=GenerationResponse)
async def generate_style_transfer(
    request: StyleTransferRequest,
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Apply style transfer to create variations of existing designs.
    """
    try:
        job_id = str(uuid.uuid4())
        
        background_tasks.add_task(
            generation_service.generate_style_transfer,
            job_id=job_id,
            request=request,
            db=db
        )
        
        await redis_manager.set(
            f"generation_job:{job_id}",
            {
                "status": GenerationStatus.QUEUED,
                "progress": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "request": request.dict()
            },
            expire=3600
        )
        
        return GenerationResponse(
            job_id=job_id,
            status=GenerationStatus.QUEUED,
            message="Style transfer generation queued successfully",
            progress=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue generation: {str(e)}")


@router.get("/status/{job_id}", response_model=GenerationStatusResponse)
async def get_generation_status(job_id: str):
    """
    Get the current status of a generation job.
    """
    try:
        # First check Redis for quick status
        cached_status = await redis_manager.get(f"generation_job:{job_id}")
        
        if not cached_status:
            raise HTTPException(status_code=404, detail="Generation job not found")
        
        return GenerationStatusResponse(
            job_id=job_id,
            status=cached_status.get("status", "unknown"),
            progress=cached_status.get("progress", 0.0),
            current_step=cached_status.get("current_step"),
            outputs_ready=cached_status.get("outputs_ready", 0),
            total_outputs=cached_status.get("total_outputs", 1),
            estimated_completion=cached_status.get("estimated_completion"),
            error_message=cached_status.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/results/{job_id}", response_model=GenerationResults)
async def get_generation_results(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the results of a completed generation job.
    """
    try:
        # Check if job exists and is completed
        cached_status = await redis_manager.get(f"generation_job:{job_id}")
        
        if not cached_status:
            raise HTTPException(status_code=404, detail="Generation job not found")
        
        if cached_status.get("status") != GenerationStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Generation job is not completed. Current status: {cached_status.get('status')}"
            )
        
        # Get results from database
        # This would query the generation_outputs table
        # For now, return a mock response
        outputs = [
            GenerationOutput(
                output_id=str(uuid.uuid4()),
                output_index=i,
                output_type="image",
                content_url=f"https://storage.example.com/generations/{job_id}/output_{i}.jpg",
                thumbnail_url=f"https://storage.example.com/generations/{job_id}/thumb_{i}.jpg",
                quality_score=0.85,
                metadata={"model": "stylegan3", "seed": 12345 + i}
            )
            for i in range(cached_status.get("total_outputs", 1))
        ]
        
        return GenerationResults(
            job_id=job_id,
            status=cached_status.get("status"),
            outputs=outputs,
            metadata={
                "generation_time": cached_status.get("generation_time", 30.5),
                "model_used": "stylegan3",
                "quality_level": cached_status.get("request", {}).get("quality_level", "standard")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.delete("/cancel/{job_id}")
async def cancel_generation(job_id: str):
    """
    Cancel a pending or running generation job.
    """
    try:
        # Check if job exists
        cached_status = await redis_manager.get(f"generation_job:{job_id}")
        
        if not cached_status:
            raise HTTPException(status_code=404, detail="Generation job not found")
        
        current_status = cached_status.get("status")
        if current_status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job with status: {current_status}"
            )
        
        # Update status to cancelled
        cached_status["status"] = GenerationStatus.CANCELLED
        cached_status["cancelled_at"] = datetime.utcnow().isoformat()
        
        await redis_manager.set(f"generation_job:{job_id}", cached_status, expire=3600)
        
        return {
            "job_id": job_id,
            "status": GenerationStatus.CANCELLED,
            "message": "Generation job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel generation: {str(e)}")


@router.get("/queue/status")
async def get_queue_status():
    """
    Get the current status of the generation queue.
    """
    try:
        # This would query the actual queue status
        # For now, return mock data
        return {
            "queue_length": 3,
            "processing_jobs": 2,
            "average_wait_time": 45.0,  # seconds
            "estimated_capacity": {
                "capsule_collection": 2,
                "single_product": 5,
                "style_transfer": 8
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@router.post("/upload-reference")
async def upload_reference_image(file: UploadFile = File(...)):
    """
    Upload a reference image for use in generation.
    Returns a URL that can be used in generation requests.
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # In a real implementation, you would:
        # 1. Validate image format and size
        # 2. Upload to cloud storage (S3, GCS, etc.)
        # 3. Return the public URL
        
        # For now, return a mock URL
        file_id = str(uuid.uuid4())
        mock_url = f"https://storage.example.com/references/{file_id}.jpg"
        
        return {
            "file_id": file_id,
            "url": mock_url,
            "filename": file.filename,
            "size": file.size if hasattr(file, 'size') else None,
            "content_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")