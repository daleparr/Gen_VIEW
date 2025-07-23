"""
Memory API routes for KSE Memory Service
Core endpoints for memory storage, retrieval, and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ...main import get_memory_manager
from ...services.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class StoreMemoryRequest(BaseModel):
    content: Union[str, Dict[str, Any]] = Field(..., description="Content to store")
    content_type: str = Field(default="text", description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    brand_id: Optional[str] = Field(default=None, description="Associated brand ID")
    source_type: str = Field(default="generation", description="Source of the memory")
    source_id: Optional[str] = Field(default=None, description="ID of the source")
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Initial importance score")


class RetrieveMemoriesRequest(BaseModel):
    query: Union[str, Dict[str, Any]] = Field(..., description="Query content")
    query_type: str = Field(default="text", description="Type of query")
    brand_id: Optional[str] = Field(default=None, description="Filter by brand ID")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum similarity threshold")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    include_associations: bool = Field(default=True, description="Include memory associations")


class AddFeedbackRequest(BaseModel):
    memory_node_id: str = Field(..., description="ID of the memory node")
    feedback_type: str = Field(..., description="Type of feedback (positive, negative, neutral)")
    feedback_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Numeric feedback score")
    feedback_text: Optional[str] = Field(default=None, description="Textual feedback")
    generation_id: Optional[str] = Field(default=None, description="ID of generation that used this memory")
    user_id: Optional[str] = Field(default=None, description="User providing feedback")
    commercial_impact: Optional[Dict[str, Any]] = Field(default=None, description="Commercial outcome data")


class MemoryResponse(BaseModel):
    id: str
    success: bool
    message: str


class MemoriesResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


class InsightsResponse(BaseModel):
    insights: Dict[str, Any]
    generated_at: str


@router.post("/store", response_model=MemoryResponse)
async def store_memory(
    request: StoreMemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> MemoryResponse:
    """
    Store a new memory in the KSE memory system.
    
    This endpoint allows storing various types of content (text, images, multimodal)
    with associated metadata and importance scoring.
    """
    try:
        start_time = datetime.utcnow()
        
        memory_id = await memory_manager.store_memory(
            content=request.content,
            content_type=request.content_type,
            metadata=request.metadata,
            brand_id=request.brand_id,
            source_type=request.source_type,
            source_id=request.source_id,
            importance_score=request.importance_score
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"Stored memory {memory_id} in {processing_time:.2f}ms")
        
        return MemoryResponse(
            id=memory_id,
            success=True,
            message=f"Memory stored successfully in {processing_time:.2f}ms"
        )
        
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {str(e)}")


@router.post("/retrieve", response_model=MemoriesResponse)
async def retrieve_memories(
    request: RetrieveMemoriesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> MemoriesResponse:
    """
    Retrieve relevant memories based on a query.
    
    This endpoint performs semantic search across stored memories using
    vector similarity and returns the most relevant results.
    """
    try:
        start_time = datetime.utcnow()
        
        memories = await memory_manager.retrieve_memories(
            query=request.query,
            query_type=request.query_type,
            brand_id=request.brand_id,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            filters=request.filters,
            include_associations=request.include_associations
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"Retrieved {len(memories)} memories in {processing_time:.2f}ms")
        
        return MemoriesResponse(
            memories=memories,
            total_count=len(memories),
            query_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.get("/retrieve", response_model=MemoriesResponse)
async def retrieve_memories_get(
    query: str = Query(..., description="Query text"),
    query_type: str = Query(default="text", description="Type of query"),
    brand_id: Optional[str] = Query(default=None, description="Filter by brand ID"),
    top_k: int = Query(default=10, ge=1, le=100, description="Number of results"),
    similarity_threshold: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum similarity"),
    include_associations: bool = Query(default=True, description="Include associations"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> MemoriesResponse:
    """
    Retrieve memories using GET request (simplified interface).
    
    This is a convenience endpoint for simple text-based queries.
    """
    try:
        start_time = datetime.utcnow()
        
        memories = await memory_manager.retrieve_memories(
            query=query,
            query_type=query_type,
            brand_id=brand_id,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            include_associations=include_associations
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return MemoriesResponse(
            memories=memories,
            total_count=len(memories),
            query_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memories: {str(e)}")


@router.post("/feedback", response_model=MemoryResponse)
async def add_memory_feedback(
    request: AddFeedbackRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> MemoryResponse:
    """
    Add feedback to a memory for reinforcement learning.
    
    This endpoint allows providing positive, negative, or neutral feedback
    on memory retrievals to improve future recommendations.
    """
    try:
        feedback_id = await memory_manager.add_memory_feedback(
            memory_node_id=request.memory_node_id,
            feedback_type=request.feedback_type,
            feedback_score=request.feedback_score,
            feedback_text=request.feedback_text,
            generation_id=request.generation_id,
            user_id=request.user_id,
            commercial_impact=request.commercial_impact
        )
        
        logger.info(f"Added feedback {feedback_id} to memory {request.memory_node_id}")
        
        return MemoryResponse(
            id=feedback_id,
            success=True,
            message="Feedback added successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to add feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(e)}")


@router.get("/insights", response_model=InsightsResponse)
async def get_memory_insights(
    brand_id: Optional[str] = Query(default=None, description="Filter by brand ID"),
    start_date: Optional[str] = Query(default=None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(default=None, description="End date (ISO format)"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> InsightsResponse:
    """
    Get insights about memory patterns and trends.
    
    This endpoint provides analytics on memory usage, patterns,
    and temporal trends for a given brand or globally.
    """
    try:
        # Parse date range if provided
        time_range = None
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                time_range = (start_dt, end_dt)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
        
        insights = await memory_manager.get_memory_insights(
            brand_id=brand_id,
            time_range=time_range
        )
        
        return InsightsResponse(
            insights=insights,
            generated_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/stats")
async def get_memory_stats(
    brand_id: Optional[str] = Query(default=None, description="Filter by brand ID"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> Dict[str, Any]:
    """
    Get basic statistics about stored memories.
    
    Returns counts, distributions, and basic metrics.
    """
    try:
        # Get basic insights (subset of full insights)
        insights = await memory_manager.get_memory_insights(brand_id=brand_id)
        
        # Extract basic stats
        stats = {
            "total_memories": insights.get("total_memories", 0),
            "content_type_distribution": insights.get("content_type_distribution", {}),
            "importance_statistics": insights.get("importance_statistics", {}),
            "clustering": insights.get("clustering", {})
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> Dict[str, Any]:
    """
    Delete a specific memory (placeholder implementation).
    
    Note: This is a placeholder. In a production system, you might want
    to soft-delete or archive memories instead of hard deletion.
    """
    try:
        # Placeholder implementation
        logger.info(f"Delete request for memory {memory_id}")
        
        return {
            "success": True,
            "message": f"Memory {memory_id} deletion requested (not implemented)",
            "memory_id": memory_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.get("/memory/{memory_id}")
async def get_memory_by_id(
    memory_id: str,
    include_associations: bool = Query(default=False, description="Include associations"),
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> Dict[str, Any]:
    """
    Get a specific memory by ID (placeholder implementation).
    
    This would retrieve a single memory node by its ID.
    """
    try:
        # Placeholder implementation
        logger.info(f"Get request for memory {memory_id}")
        
        return {
            "message": f"Get memory {memory_id} not fully implemented",
            "memory_id": memory_id,
            "include_associations": include_associations
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory: {str(e)}")