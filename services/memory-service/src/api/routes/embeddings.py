"""
Embeddings API routes for KSE Memory Service
Endpoints for embedding generation and similarity operations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Union
from pydantic import BaseModel, Field
import logging

from ...main import get_embedding_service
from ...services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


class EmbedTextRequest(BaseModel):
    texts: Union[str, List[str]] = Field(..., description="Text(s) to embed")
    normalize: bool = Field(default=True, description="Whether to normalize embeddings")


class EmbedMultimodalRequest(BaseModel):
    inputs: Dict[str, Any] = Field(..., description="Multimodal inputs (text, image)")
    normalize: bool = Field(default=True, description="Whether to normalize embeddings")


class SimilarityRequest(BaseModel):
    embedding1: List[float] = Field(..., description="First embedding")
    embedding2: List[float] = Field(..., description="Second embedding")
    metric: str = Field(default="cosine", description="Similarity metric")


@router.post("/text")
async def embed_text(
    request: EmbedTextRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Generate embeddings for text input(s)."""
    try:
        embeddings = await embedding_service.encode_text(
            texts=request.texts,
            normalize=request.normalize
        )
        
        # Convert numpy arrays to lists for JSON serialization
        if isinstance(embeddings, list):
            embeddings_list = [emb.tolist() for emb in embeddings]
        else:
            embeddings_list = embeddings.tolist()
        
        return {
            "embeddings": embeddings_list,
            "count": len(embeddings_list) if isinstance(embeddings_list[0], list) else 1,
            "dimension": len(embeddings_list[0]) if isinstance(embeddings_list[0], list) else len(embeddings_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to embed text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal")
async def embed_multimodal(
    request: EmbedMultimodalRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Generate embeddings for multimodal inputs."""
    try:
        embedding = await embedding_service.encode_multimodal(
            inputs=request.inputs,
            normalize=request.normalize
        )
        
        return {
            "embedding": embedding.tolist(),
            "dimension": len(embedding)
        }
        
    except Exception as e:
        logger.error(f"Failed to embed multimodal input: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity")
async def compute_similarity(
    request: SimilarityRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Compute similarity between two embeddings."""
    try:
        import numpy as np
        
        emb1 = np.array(request.embedding1)
        emb2 = np.array(request.embedding2)
        
        similarity = await embedding_service.compute_similarity(
            embedding1=emb1,
            embedding2=emb2,
            metric=request.metric
        )
        
        return {
            "similarity": float(similarity),
            "metric": request.metric
        }
        
    except Exception as e:
        logger.error(f"Failed to compute similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_embedding_stats(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Get statistics about stored embeddings."""
    try:
        stats = await embedding_service.get_embedding_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))