"""
Generation API routes for AI-powered fashion generation
Supports capsule collection generation, single products, and style variations
Multi-modal input processing with KSE Memory integration
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, WebSocket
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio

from ...services.generation_service import GenerationService
from ...services.model_manager import ModelManager
from ...services.kse_memory_service import KSEMemoryService
from ...services.multimodal_processor import MultiModalProcessor
from ...core.database import get_db
from ...core.redis_client import redis_manager
from ...models.generation_models import GenerationType, GenerationStatus
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class MultiModalInputs(BaseModel):
    """Multi-modal input structure for generation requests."""
    text_prompt: Optional[str] = None
    reference_images: Optional[List[str]] = None
    sketch_inputs: Optional[List[str]] = None
    color_palette: Optional[List[str]] = None
    material_preferences: Optional[List[str]] = None
    style_vectors: Optional[List[float]] = None
    brand_context: Optional[Dict[str, Any]] = None


class BrandParameters(BaseModel):
    """Brand-specific generation parameters."""
    brand_id: str
    design_dna_adherence: float = Field(0.8, ge=0.0, le=1.0)
    target_demographic: Optional[str] = None
    price_point: Optional[str] = None
    sustainability_requirements: Optional[Dict[str, Any]] = None
    seasonal_constraints: Optional[Dict[str, Any]] = None


class CapsuleGenerationRequest(BaseModel):
    """Enhanced capsule collection generation request with multi-modal inputs."""
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    
    # Multi-modal inputs
    inputs: MultiModalInputs
    brand_parameters: BrandParameters
    
    # Generation settings
    target_pieces: int = Field(5, ge=3, le=15)
    quality_level: str = Field("standard", description="draft, standard, high, ultra")
    creativity_level: float = Field(0.7, ge=0.0, le=1.0)
    
    # KSE Memory settings
    use_memory_context: bool = Field(True, description="Use KSE memory for context")
    memory_depth: int = Field(5, ge=1, le=20, description="Number of past generations to consider")
    
    # Commercial optimization
    optimize_for_commercial: bool = Field(False, description="Optimize for predicted commercial success")
    target_conversion_rate: Optional[float] = Field(None, ge=0.0, le=1.0)


class GenerationResponse(BaseModel):
    """Enhanced generation response with KSE context."""
    task_id: str
    status: str
    estimated_completion: str
    kse_context_retrieved: bool
    memory_nodes_accessed: int
    commercial_predictions_enabled: bool
    websocket_url: str


@router.post("/api/v1/generate/capsule", response_model=GenerationResponse)
async def generate_capsule_collection(
    request: CapsuleGenerationRequest,
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    kse_memory: KSEMemoryService = Depends(),
    multimodal_processor: MultiModalProcessor = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a capsule collection with multi-modal inputs and KSE memory integration.
    Implements the core generation endpoint structure as specified.
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Multi-modal input processing
        processed_inputs = await process_multimodal_inputs(
            request.inputs, 
            multimodal_processor
        )
        
        # KSE Memory retrieval
        design_dna = None
        memory_nodes_accessed = 0
        
        if request.use_memory_context:
            design_dna = await kse_memory.retrieve_relevant_context(
                processed_inputs,
                brand_id=request.brand_parameters.brand_id,
                depth=request.memory_depth
            )
            memory_nodes_accessed = len(design_dna.get('memory_nodes', []))
        
        # Generation task queuing
        generation_params = {
            'task_id': task_id,
            'inputs': processed_inputs,
            'design_dna': design_dna,
            'brand_parameters': request.brand_parameters.dict(),
            'generation_settings': {
                'target_pieces': request.target_pieces,
                'quality_level': request.quality_level,
                'creativity_level': request.creativity_level,
                'optimize_for_commercial': request.optimize_for_commercial,
                'target_conversion_rate': request.target_conversion_rate
            }
        }
        
        # Queue the generation task
        await generation_queue.enqueue(generation_params)
        
        # Store initial task state
        await redis_manager.set(
            f"generation_task:{task_id}",
            {
                "status": GenerationStatus.QUEUED,
                "progress": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "request": request.dict(),
                "kse_context_retrieved": design_dna is not None,
                "memory_nodes_accessed": memory_nodes_accessed
            },
            expire=3600
        )
        
        # Start background generation
        background_tasks.add_task(
            generation_service.generate_capsule_collection_enhanced,
            task_id=task_id,
            params=generation_params,
            db=db
        )
        
        return GenerationResponse(
            task_id=task_id,
            status=GenerationStatus.QUEUED,
            estimated_completion="30s",
            kse_context_retrieved=design_dna is not None,
            memory_nodes_accessed=memory_nodes_accessed,
            commercial_predictions_enabled=request.optimize_for_commercial,
            websocket_url=f"/ws/generation/{task_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue generation: {str(e)}")


async def process_multimodal_inputs(
    inputs: MultiModalInputs, 
    processor: MultiModalProcessor
) -> Dict[str, Any]:
    """
    Process multi-modal inputs into a unified representation.
    """
    processed = {
        'modalities': [],
        'embeddings': {},
        'metadata': {}
    }
    
    # Process text prompt
    if inputs.text_prompt:
        text_embedding = await processor.encode_text(inputs.text_prompt)
        processed['embeddings']['text'] = text_embedding
        processed['modalities'].append('text')
        processed['metadata']['text_prompt'] = inputs.text_prompt
    
    # Process reference images
    if inputs.reference_images:
        image_embeddings = []
        for img_url in inputs.reference_images:
            embedding = await processor.encode_image(img_url)
            image_embeddings.append(embedding)
        
        processed['embeddings']['images'] = image_embeddings
        processed['modalities'].append('images')
        processed['metadata']['reference_images'] = inputs.reference_images
    
    # Process sketch inputs
    if inputs.sketch_inputs:
        sketch_embeddings = []
        for sketch_url in inputs.sketch_inputs:
            embedding = await processor.encode_sketch(sketch_url)
            sketch_embeddings.append(embedding)
        
        processed['embeddings']['sketches'] = sketch_embeddings
        processed['modalities'].append('sketches')
        processed['metadata']['sketch_inputs'] = inputs.sketch_inputs
    
    # Process structured inputs
    if inputs.color_palette:
        color_embedding = await processor.encode_colors(inputs.color_palette)
        processed['embeddings']['colors'] = color_embedding
        processed['modalities'].append('colors')
        processed['metadata']['color_palette'] = inputs.color_palette
    
    if inputs.material_preferences:
        material_embedding = await processor.encode_materials(inputs.material_preferences)
        processed['embeddings']['materials'] = material_embedding
        processed['modalities'].append('materials')
        processed['metadata']['material_preferences'] = inputs.material_preferences
    
    # Process style vectors
    if inputs.style_vectors:
        processed['embeddings']['style'] = inputs.style_vectors
        processed['modalities'].append('style')
        processed['metadata']['style_vector_dim'] = len(inputs.style_vectors)
    
    # Add brand context
    if inputs.brand_context:
        processed['metadata']['brand_context'] = inputs.brand_context
    
    return processed


@router.websocket("/ws/generation/{task_id}")
async def generation_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time generation status updates.
    """
    await websocket.accept()
    
    try:
        while True:
            # Get current task status
            task_data = await redis_manager.get(f"generation_task:{task_id}")
            
            if not task_data:
                await websocket.send_json({
                    "error": "Task not found",
                    "task_id": task_id
                })
                break
            
            # Send status update
            await websocket.send_json({
                "task_id": task_id,
                "status": task_data.get("status"),
                "progress": task_data.get("progress", 0.0),
                "current_step": task_data.get("current_step"),
                "outputs_ready": task_data.get("outputs_ready", 0),
                "total_outputs": task_data.get("total_outputs", 0),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check if generation is complete
            if task_data.get("status") in [
                GenerationStatus.COMPLETED, 
                GenerationStatus.FAILED, 
                GenerationStatus.CANCELLED
            ]:
                # Send final results
                if task_data.get("status") == GenerationStatus.COMPLETED:
                    results = await redis_manager.get(f"generation_results:{task_id}")
                    if results:
                        await websocket.send_json({
                            "task_id": task_id,
                            "status": "completed",
                            "results": results
                        })
                break
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except Exception as e:
        await websocket.send_json({
            "error": str(e),
            "task_id": task_id
        })
    finally:
        await websocket.close()


@router.post("/api/v1/generate/single-product")
async def generate_single_product_enhanced(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    kse_memory: KSEMemoryService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced single product generation with KSE memory integration."""
    task_id = str(uuid.uuid4())
    
    # Process inputs and retrieve memory context
    processed_inputs = await process_multimodal_inputs(
        MultiModalInputs(**request.get('inputs', {})),
        MultiModalProcessor()
    )
    
    design_dna = await kse_memory.retrieve_relevant_context(
        processed_inputs,
        brand_id=request.get('brand_id'),
        depth=3
    )
    
    # Queue generation
    background_tasks.add_task(
        generation_service.generate_single_product_enhanced,
        task_id=task_id,
        inputs=processed_inputs,
        design_dna=design_dna,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": GenerationStatus.QUEUED,
        "estimated_completion": "15s",
        "websocket_url": f"/ws/generation/{task_id}"
    }


@router.post("/api/v1/generate/style-transfer")
async def generate_style_transfer_enhanced(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    generation_service: GenerationService = Depends(),
    kse_memory: KSEMemoryService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced style transfer with memory-guided style adaptation."""
    task_id = str(uuid.uuid4())
    
    # Process source and target inputs
    source_inputs = await process_multimodal_inputs(
        MultiModalInputs(**request.get('source_inputs', {})),
        MultiModalProcessor()
    )
    
    target_inputs = await process_multimodal_inputs(
        MultiModalInputs(**request.get('target_inputs', {})),
        MultiModalProcessor()
    )
    
    # Retrieve style memory context
    style_memory = await kse_memory.retrieve_style_context(
        source_inputs,
        target_inputs,
        brand_id=request.get('brand_id')
    )
    
    # Queue style transfer
    background_tasks.add_task(
        generation_service.generate_style_transfer_enhanced,
        task_id=task_id,
        source_inputs=source_inputs,
        target_inputs=target_inputs,
        style_memory=style_memory,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": GenerationStatus.QUEUED,
        "estimated_completion": "20s",
        "websocket_url": f"/ws/generation/{task_id}"
    }


@router.get("/api/v1/generate/memory-insights/{brand_id}")
async def get_memory_insights(
    brand_id: str,
    kse_memory: KSEMemoryService = Depends()
):
    """Get KSE memory insights for a specific brand."""
    insights = await kse_memory.get_brand_memory_insights(brand_id)
    
    return {
        "brand_id": brand_id,
        "total_memory_nodes": insights.get("total_nodes", 0),
        "recent_generations": insights.get("recent_generations", []),
        "design_evolution": insights.get("design_evolution", {}),
        "commercial_performance": insights.get("commercial_performance", {}),
        "temporal_patterns": insights.get("temporal_patterns", {})
    }


@router.post("/api/v1/generate/feedback")
async def submit_generation_feedback(
    feedback: Dict[str, Any],
    kse_memory: KSEMemoryService = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback for generation results to improve future outputs."""
    generation_id = feedback.get("generation_id")
    commercial_outcomes = feedback.get("commercial_outcomes")
    user_ratings = feedback.get("user_ratings")
    
    # Store feedback in KSE memory
    await kse_memory.integrate_feedback(
        generation_id=generation_id,
        commercial_outcomes=commercial_outcomes,
        user_ratings=user_ratings,
        db=db
    )
    
    return {
        "status": "feedback_integrated",
        "generation_id": generation_id,
        "learning_update": "KSE memory updated with feedback"
    }


# Generation queue implementation
class GenerationQueue:
    """Enhanced generation queue with priority and resource management."""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.priority_queue = asyncio.PriorityQueue()
        self.processing = {}
    
    async def enqueue(self, params: Dict[str, Any], priority: int = 5):
        """Enqueue generation task with priority."""
        task_id = params['task_id']
        
        if priority > 7:  # High priority
            await self.priority_queue.put((priority, task_id, params))
        else:
            await self.queue.put((task_id, params))
        
        # Update Redis with queue position
        queue_position = self.queue.qsize() + self.priority_queue.qsize()
        await redis_manager.set(
            f"generation_task:{task_id}",
            {"queue_position": queue_position},
            expire=3600
        )
    
    async def dequeue(self):
        """Dequeue next task respecting priority."""
        if not self.priority_queue.empty():
            priority, task_id, params = await self.priority_queue.get()
            return task_id, params
        elif not self.queue.empty():
            task_id, params = await self.queue.get()
            return task_id, params
        else:
            return None, None


# Global generation queue instance
generation_queue = GenerationQueue()