"""
Main rendering API routes for NeRF Rendering Service
Handles rendering jobs, status tracking, and result retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
import uuid
import numpy as np
from datetime import datetime

from ...main import get_rendering_manager, get_nerf_service
from ...core.redis_client import get_rendering_queue
from ...services.rendering_manager import RenderingManager
from ...services.nerf_service import NeRFService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class RenderImageRequest(BaseModel):
    model_id: str = Field(..., description="ID of the NeRF model to use")
    camera_pose: List[List[float]] = Field(..., description="4x4 camera pose matrix")
    intrinsics: Dict[str, float] = Field(..., description="Camera intrinsics (fx, fy, cx, cy)")
    resolution: Optional[List[int]] = Field(default=None, description="Image resolution [width, height]")
    quality: str = Field(default="medium", description="Render quality (low, medium, high)")
    priority: int = Field(default=0, description="Job priority (0=normal, higher=priority)")


class Render360Request(BaseModel):
    model_id: str = Field(..., description="ID of the NeRF model to use")
    intrinsics: Dict[str, float] = Field(..., description="Camera intrinsics")
    radius: float = Field(default=3.0, description="Camera distance from origin")
    num_frames: int = Field(default=120, ge=24, le=360, description="Number of frames")
    resolution: Optional[List[int]] = Field(default=None, description="Video resolution")
    quality: str = Field(default="medium", description="Render quality")


class RenderJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None


class RenderResultResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    processing_time: Optional[float] = None


@router.post("/image", response_model=RenderJobResponse)
async def render_image(
    request: RenderImageRequest,
    background_tasks: BackgroundTasks,
    rendering_manager: RenderingManager = Depends(get_rendering_manager)
) -> RenderJobResponse:
    """
    Submit a NeRF image rendering job.
    
    This endpoint queues a rendering job for processing and returns immediately
    with a job ID that can be used to track progress and retrieve results.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Convert camera pose to numpy array
        camera_pose = np.array(request.camera_pose)
        if camera_pose.shape != (4, 4):
            raise HTTPException(
                status_code=400, 
                detail="Camera pose must be a 4x4 matrix"
            )
        
        # Prepare job data
        job_data = {
            "type": "render_image",
            "model_id": request.model_id,
            "camera_pose": camera_pose.tolist(),
            "intrinsics": request.intrinsics,
            "resolution": tuple(request.resolution) if request.resolution else None,
            "quality": request.quality
        }
        
        # Submit job
        success = await rendering_manager.submit_render_job(
            job_id=job_id,
            job_data=job_data,
            priority=request.priority
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to submit rendering job"
            )
        
        # Estimate processing time based on quality and resolution
        estimated_time = _estimate_render_time(request.quality, request.resolution)
        
        logger.info(f"Submitted image rendering job: {job_id}")
        
        return RenderJobResponse(
            job_id=job_id,
            status="queued",
            message="Rendering job submitted successfully",
            estimated_time=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit render job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit render job: {str(e)}")


@router.post("/360-video", response_model=RenderJobResponse)
async def render_360_video(
    request: Render360Request,
    background_tasks: BackgroundTasks,
    rendering_manager: RenderingManager = Depends(get_rendering_manager)
) -> RenderJobResponse:
    """
    Submit a 360-degree video rendering job.
    
    This endpoint creates a rotating camera path around the NeRF model
    and renders multiple frames to create a video.
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Prepare job data
        job_data = {
            "type": "render_360_video",
            "model_id": request.model_id,
            "intrinsics": request.intrinsics,
            "radius": request.radius,
            "num_frames": request.num_frames,
            "resolution": tuple(request.resolution) if request.resolution else None,
            "quality": request.quality
        }
        
        # Submit job with higher priority for videos
        success = await rendering_manager.submit_render_job(
            job_id=job_id,
            job_data=job_data,
            priority=1  # Higher priority for video jobs
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to submit video rendering job"
            )
        
        # Estimate processing time (longer for videos)
        estimated_time = _estimate_render_time(request.quality, request.resolution) * request.num_frames
        
        logger.info(f"Submitted 360° video rendering job: {job_id}")
        
        return RenderJobResponse(
            job_id=job_id,
            status="queued",
            message="360° video rendering job submitted successfully",
            estimated_time=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit video render job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit video render job: {str(e)}")


@router.get("/job/{job_id}", response_model=RenderResultResponse)
async def get_render_job_status(
    job_id: str,
    rendering_manager: RenderingManager = Depends(get_rendering_manager)
) -> RenderResultResponse:
    """
    Get the status and results of a rendering job.
    
    Returns the current status of the job and the results if completed.
    """
    try:
        job_status = await rendering_manager.get_job_status(job_id)
        
        if job_status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Format response based on job status
        if job_status["status"] == "completed":
            return RenderResultResponse(
                job_id=job_id,
                status="completed",
                result=job_status["data"]["result"],
                created_at=datetime.fromtimestamp(
                    job_status["data"]["original_data"]["created_at"]
                ).isoformat(),
                completed_at=datetime.fromtimestamp(
                    job_status["data"]["completed_at"]
                ).isoformat(),
                processing_time=job_status["data"]["completed_at"] - 
                              job_status["data"]["original_data"]["created_at"]
            )
        elif job_status["status"] == "failed":
            return RenderResultResponse(
                job_id=job_id,
                status="failed",
                error=job_status["data"]["error"],
                created_at=datetime.fromtimestamp(
                    job_status["data"]["original_data"]["created_at"]
                ).isoformat()
            )
        else:  # active/queued
            return RenderResultResponse(
                job_id=job_id,
                status=job_status["status"],
                created_at=datetime.fromtimestamp(
                    job_status["data"]["created_at"]
                ).isoformat()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/jobs")
async def list_render_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    rendering_manager: RenderingManager = Depends(get_rendering_manager)
) -> Dict[str, Any]:
    """
    List rendering jobs with optional status filtering.
    
    Returns a list of jobs with their current status and metadata.
    """
    try:
        jobs = await rendering_manager.list_jobs(status=status, limit=limit)
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "status_filter": status
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.delete("/job/{job_id}")
async def cancel_render_job(
    job_id: str,
    rendering_manager: RenderingManager = Depends(get_rendering_manager)
) -> Dict[str, Any]:
    """
    Cancel a queued or active rendering job.
    
    Note: Jobs that are already processing may not be immediately cancelled.
    """
    try:
        success = await rendering_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found or cannot be cancelled"
            )
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/queue/stats")
async def get_queue_stats() -> Dict[str, Any]:
    """Get statistics about the rendering queue."""
    try:
        rendering_queue = await get_rendering_queue()
        stats = await rendering_queue.get_queue_stats()
        
        return {
            "queue_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


@router.post("/direct/image")
async def render_image_direct(
    request: RenderImageRequest,
    nerf_service: NeRFService = Depends(get_nerf_service)
) -> Dict[str, Any]:
    """
    Render an image directly without queuing (for testing/development).
    
    WARNING: This bypasses the queue system and may block the API.
    Use only for testing or when immediate results are needed.
    """
    try:
        # Convert camera pose to numpy array
        camera_pose = np.array(request.camera_pose)
        resolution = tuple(request.resolution) if request.resolution else None
        
        # Render image directly
        start_time = datetime.utcnow()
        image = await nerf_service.render_image(
            model_id=request.model_id,
            camera_pose=camera_pose,
            intrinsics=request.intrinsics,
            resolution=resolution
        )
        end_time = datetime.utcnow()
        
        if image is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to render image"
            )
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Convert image to base64 for JSON response
        import base64
        from PIL import Image
        import io
        
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "status": "completed",
            "result": {
                "image_base64": image_base64,
                "format": "PNG",
                "resolution": list(image.shape[:2][::-1])  # width, height
            },
            "processing_time": processing_time,
            "timestamp": end_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render image directly: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to render image: {str(e)}")


def _estimate_render_time(quality: str, resolution: Optional[List[int]]) -> int:
    """Estimate rendering time in seconds based on quality and resolution."""
    base_time = {
        "low": 5,
        "medium": 15,
        "high": 45
    }.get(quality, 15)
    
    if resolution:
        # Scale by resolution (assuming 512x512 as baseline)
        pixels = resolution[0] * resolution[1]
        baseline_pixels = 512 * 512
        scale_factor = pixels / baseline_pixels
        base_time = int(base_time * scale_factor)
    
    return base_time