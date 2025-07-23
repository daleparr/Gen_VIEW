"""
Embedding Service for KSE Memory Service
Handles multi-modal embedding generation, similarity computation, and vector operations
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple
import torch
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
import chromadb
from chromadb.config import Settings
import json
import hashlib
from datetime import datetime

from ..core.config import get_settings
from ..core.redis_client import get_redis_manager

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and managing multi-modal embeddings.
    Supports text, image, and combined embeddings for the KSE memory system.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_manager = None
        
        # Models
        self.text_model: Optional[SentenceTransformer] = None
        self.multimodal_model: Optional[CLIPModel] = None
        self.multimodal_processor: Optional[CLIPProcessor] = None
        
        # ChromaDB client
        self.chroma_client: Optional[chromadb.HttpClient] = None
        self.collections: Dict[str, Any] = {}
        
        # Cache settings
        self.cache_embeddings = True
        self.cache_ttl = 3600 * 24  # 24 hours
        
        # Performance settings
        self.batch_size = self.settings.batch_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    async def initialize(self):
        """Initialize the embedding service with models and connections."""
        try:
            logger.info("Initializing Embedding Service...")
            
            # Initialize Redis manager
            self.redis_manager = await get_redis_manager()
            
            # Initialize ChromaDB client
            await self._init_chromadb()
            
            # Load models
            await self._load_models()
            
            logger.info("Embedding Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Embedding Service: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Embedding Service...")
        # Models are automatically cleaned up by garbage collection
    
    async def _init_chromadb(self):
        """Initialize ChromaDB client and collections."""
        try:
            self.chroma_client = chromadb.HttpClient(
                host=self.settings.chromadb_host,
                port=self.settings.chromadb_port,
                settings=Settings(allow_reset=True)
            )
            
            # Create or get collections
            collection_names = [
                "memory_embeddings",
                "concept_embeddings", 
                "temporal_embeddings",
                "brand_embeddings"
            ]
            
            for name in collection_names:
                collection = self.chroma_client.get_or_create_collection(
                    name=f"{self.settings.chromadb_collection_prefix}_{name}",
                    metadata={"description": f"KSE {name}"}
                )
                self.collections[name] = collection
            
            logger.info("ChromaDB collections initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _load_models(self):
        """Load embedding models."""
        try:
            # Load text embedding model
            logger.info(f"Loading text model: {self.settings.embedding_model}")
            self.text_model = SentenceTransformer(self.settings.embedding_model)
            self.text_model.to(self.device)
            
            # Load multimodal model (CLIP)
            logger.info("Loading multimodal model: CLIP")
            self.multimodal_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.multimodal_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.multimodal_model.to(self.device)
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    async def encode_text(
        self, 
        texts: Union[str, List[str]], 
        normalize: bool = True,
        use_cache: bool = True
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Encode text(s) into embeddings.
        
        Args:
            texts: Single text or list of texts to encode
            normalize: Whether to normalize embeddings
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding(s) as numpy array(s)
        """
        try:
            # Handle single text input
            single_input = isinstance(texts, str)
            if single_input:
                texts = [texts]
            
            embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            # Check cache for each text
            if use_cache and self.cache_embeddings:
                for i, text in enumerate(texts):
                    cache_key = self._get_cache_key("text", text)
                    cached_embedding = await self.redis_manager.get(cache_key)
                    
                    if cached_embedding is not None:
                        embeddings.append(np.array(cached_embedding))
                    else:
                        embeddings.append(None)
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = texts
                uncached_indices = list(range(len(texts)))
                embeddings = [None] * len(texts)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                logger.debug(f"Generating embeddings for {len(uncached_texts)} texts")
                
                # Generate embeddings in batches
                new_embeddings = []
                for i in range(0, len(uncached_texts), self.batch_size):
                    batch = uncached_texts[i:i + self.batch_size]
                    batch_embeddings = await asyncio.get_event_loop().run_in_executor(
                        None, self._encode_text_batch, batch, normalize
                    )
                    new_embeddings.extend(batch_embeddings)
                
                # Cache new embeddings and update results
                for i, embedding in enumerate(new_embeddings):
                    idx = uncached_indices[i]
                    embeddings[idx] = embedding
                    
                    if use_cache and self.cache_embeddings:
                        cache_key = self._get_cache_key("text", uncached_texts[i])
                        await self.redis_manager.set(
                            cache_key, 
                            embedding.tolist(), 
                            ttl=self.cache_ttl
                        )
            
            # Return single embedding or list
            if single_input:
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise
    
    def _encode_text_batch(self, texts: List[str], normalize: bool) -> List[np.ndarray]:
        """Encode a batch of texts (runs in thread executor)."""
        embeddings = self.text_model.encode(
            texts, 
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return [emb for emb in embeddings]
    
    async def encode_multimodal(
        self,
        inputs: Dict[str, Any],
        normalize: bool = True,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Encode multimodal inputs (text + image) into embeddings.
        
        Args:
            inputs: Dictionary with 'text' and/or 'image' keys
            normalize: Whether to normalize embeddings
            use_cache: Whether to use cached embeddings
            
        Returns:
            Combined embedding as numpy array
        """
        try:
            # Create cache key from inputs
            cache_key = None
            if use_cache and self.cache_embeddings:
                cache_key = self._get_cache_key("multimodal", inputs)
                cached_embedding = await self.redis_manager.get(cache_key)
                if cached_embedding is not None:
                    return np.array(cached_embedding)
            
            # Generate embedding
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._encode_multimodal_sync, inputs, normalize
            )
            
            # Cache result
            if cache_key and self.cache_embeddings:
                await self.redis_manager.set(
                    cache_key, 
                    embedding.tolist(), 
                    ttl=self.cache_ttl
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to encode multimodal inputs: {e}")
            raise
    
    def _encode_multimodal_sync(self, inputs: Dict[str, Any], normalize: bool) -> np.ndarray:
        """Encode multimodal inputs synchronously."""
        text = inputs.get('text', '')
        image = inputs.get('image')  # PIL Image or image path
        
        # Process inputs
        processed_inputs = self.multimodal_processor(
            text=[text] if text else None,
            images=[image] if image else None,
            return_tensors="pt",
            padding=True
        )
        
        # Move to device
        for key in processed_inputs:
            if hasattr(processed_inputs[key], 'to'):
                processed_inputs[key] = processed_inputs[key].to(self.device)
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.multimodal_model(**processed_inputs)
            
            # Combine text and image embeddings if both present
            if text and image:
                text_embeds = outputs.text_embeds
                image_embeds = outputs.image_embeds
                # Average the embeddings
                combined_embeds = (text_embeds + image_embeds) / 2
            elif text:
                combined_embeds = outputs.text_embeds
            elif image:
                combined_embeds = outputs.image_embeds
            else:
                raise ValueError("No valid inputs provided")
            
            embedding = combined_embeds.cpu().numpy().squeeze()
            
            if normalize:
                embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
    
    async def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = "cosine"
    ) -> float:
        """
        Compute similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric ('cosine', 'euclidean', 'dot')
            
        Returns:
            Similarity score
        """
        try:
            if metric == "cosine":
                # Cosine similarity
                dot_product = np.dot(embedding1, embedding2)
                norm1 = np.linalg.norm(embedding1)
                norm2 = np.linalg.norm(embedding2)
                similarity = dot_product / (norm1 * norm2)
            elif metric == "euclidean":
                # Euclidean distance (converted to similarity)
                distance = np.linalg.norm(embedding1 - embedding2)
                similarity = 1 / (1 + distance)
            elif metric == "dot":
                # Dot product
                similarity = np.dot(embedding1, embedding2)
            else:
                raise ValueError(f"Unknown similarity metric: {metric}")
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            raise
    
    async def find_similar_embeddings(
        self,
        query_embedding: np.ndarray,
        collection_name: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar embeddings in a ChromaDB collection.
        
        Args:
            query_embedding: Query embedding to search for
            collection_name: Name of the collection to search
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters
            
        Returns:
            List of similar embeddings with metadata
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection {collection_name} not found")
            
            collection = self.collections[collection_name]
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filters
            )
            
            # Process results
            similar_embeddings = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    if similarity >= threshold:
                        similar_embeddings.append({
                            'id': results['ids'][0][i],
                            'similarity': similarity,
                            'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                            'embedding': results['embeddings'][0][i] if results['embeddings'] else None
                        })
            
            return similar_embeddings
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            raise
    
    async def store_embedding(
        self,
        embedding_id: str,
        embedding: np.ndarray,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store an embedding in ChromaDB.
        
        Args:
            embedding_id: Unique identifier for the embedding
            embedding: The embedding vector
            collection_name: Name of the collection to store in
            metadata: Optional metadata to store with the embedding
            
        Returns:
            True if successful
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection {collection_name} not found")
            
            collection = self.collections[collection_name]
            
            # Store embedding
            collection.add(
                embeddings=[embedding.tolist()],
                metadatas=[metadata or {}],
                ids=[embedding_id]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            raise
    
    async def batch_store_embeddings(
        self,
        embeddings_data: List[Dict[str, Any]],
        collection_name: str
    ) -> bool:
        """
        Store multiple embeddings in batch.
        
        Args:
            embeddings_data: List of dicts with 'id', 'embedding', 'metadata'
            collection_name: Name of the collection to store in
            
        Returns:
            True if successful
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection {collection_name} not found")
            
            collection = self.collections[collection_name]
            
            # Prepare batch data
            ids = [item['id'] for item in embeddings_data]
            embeddings = [item['embedding'].tolist() for item in embeddings_data]
            metadatas = [item.get('metadata', {}) for item in embeddings_data]
            
            # Store batch
            collection.add(
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to batch store embeddings: {e}")
            raise
    
    def _get_cache_key(self, embedding_type: str, content: Union[str, Dict[str, Any]]) -> str:
        """Generate cache key for embedding."""
        if isinstance(content, str):
            content_hash = hashlib.md5(content.encode()).hexdigest()
        else:
            content_str = json.dumps(content, sort_keys=True)
            content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        return f"embedding:{embedding_type}:{self.settings.embedding_model}:{content_hash}"
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            stats = {}
            
            for name, collection in self.collections.items():
                count = collection.count()
                stats[name] = {
                    'count': count,
                    'collection_name': collection.name
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the embedding service."""
        try:
            health = {
                'status': 'healthy',
                'models_loaded': {
                    'text_model': self.text_model is not None,
                    'multimodal_model': self.multimodal_model is not None
                },
                'chromadb_connected': self.chroma_client is not None,
                'collections': len(self.collections),
                'device': self.device
            }
            
            # Test embedding generation
            try:
                test_embedding = await self.encode_text("test", use_cache=False)
                health['embedding_generation'] = 'working'
                health['embedding_dimension'] = len(test_embedding)
            except Exception as e:
                health['embedding_generation'] = f'error: {str(e)}'
            
            return health
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }