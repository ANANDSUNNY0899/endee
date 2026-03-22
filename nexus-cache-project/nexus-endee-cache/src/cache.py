"""
Semantic Cache Implementation
Uses Endee Vector Database for storing and retrieving query-response pairs
"""

import hashlib
import logging
from typing import Optional, Dict, Any
import numpy as np

from endee import Endee, Precision
from embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic caching layer using vector similarity search
    
    Stores query-response pairs as embeddings in Endee Vector Database
    and retrieves them using cosine similarity matching.
    """
    
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator,
        index_name: str = "semantic_cache",
        dimension: int = 384  # text-embedding-3-small dimension
    ):
        """
        Initialize semantic cache
        
        Args:
            embedding_generator: Instance of EmbeddingGenerator
            index_name: Name of the vector index
            dimension: Embedding dimension
        """
        self.embedding_generator = embedding_generator
        self.index_name = index_name
        self.dimension = dimension
        
        # Initialize Endee client (connects to localhost:8080 by default)
        self.endee_client = Endee()
        
        # Create index if it doesn't exist
        self._initialize_index()
        
        logger.info(
            f"SemanticCache initialized: "
            f"index={index_name}, dimension={dimension}"
        )
    
    def _initialize_index(self):
        """Create Endee index if it doesn't exist"""
        try:
            # Check if index exists
            indexes = self.endee_client.list_indexes()
            
            # Handle both formats: list of strings or list of dicts
            if isinstance(indexes, list) and len(indexes) > 0:
                if isinstance(indexes[0], dict):
                    index_names = [idx["name"] for idx in indexes]
                else:
                    index_names = indexes  # Already a list of strings
            else:
                index_names = []
            
            if self.index_name not in index_names:
                # Create new index
                self.endee_client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    space_type="cosine",  # Cosine similarity for semantic search
                    precision=Precision.INT8  # Memory-efficient quantization
                )
                logger.info(f"Created new index: {self.index_name}")
            else:
                logger.info(f"Using existing index: {self.index_name}")
            
            # Get index reference for queries
            self.index = self.endee_client.get_index(self.index_name)
                
        except Exception as e:
            logger.error(f"Error initializing index: {str(e)}")
            raise
    
    def _generate_vector_id(self, query: str) -> str:
        """
        Generate unique ID for a query using hash
        
        Args:
            query: Query text
            
        Returns:
            Unique vector ID
        """
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    def store(self, query: str, response: str) -> str:
        """
        Store a query-response pair in the cache
        
        Args:
            query: User query text
            response: Corresponding response text
            
        Returns:
            Vector ID of stored embedding
        """
        try:
            # Generate embedding for query
            embedding = self.embedding_generator.generate(query)
            
            # Create vector ID
            vector_id = self._generate_vector_id(query)
            
            # Store in Endee with metadata
            self.index.upsert([{
                "id": vector_id,
                "vector": embedding.tolist(),
                "meta": {
                    "query": query,
                    "response": response,
                    "query_length": len(query),
                    "response_length": len(response)
                }
            }])
            
            logger.debug(f"Stored vector {vector_id} for query: {query[:50]}...")
            
            return vector_id
            
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            raise
    
    def search(
        self,
        query: str,
        threshold: float = 0.85,
        top_k: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Search for semantically similar cached queries
        
        Args:
            query: Query text to search for
            threshold: Minimum similarity score (0.0 to 1.0)
            top_k: Number of results to return
            
        Returns:
            Dictionary with cached response if found, None otherwise
        """
        try:
            # Generate embedding for search query
            query_embedding = self.embedding_generator.generate(query)
            
            # Search Endee
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_vectors=False  # Don't need vectors in results
            )
            
            # Check if we have results above threshold
            if results and len(results) > 0:
                best_match = results[0]
                similarity = best_match["similarity"]
                
                if similarity >= threshold:
                    # Cache hit!
                    metadata = best_match["meta"]
                    
                    logger.debug(
                        f"Cache hit: similarity={similarity:.3f}, "
                        f"original_query={metadata['query'][:50]}..."
                    )
                    
                    return {
                        "similarity": similarity,
                        "response": metadata["response"],
                        "original_query": metadata["query"],
                        "vector_id": best_match["id"]
                    }
                else:
                    logger.debug(
                        f"Below threshold: similarity={similarity:.3f} < {threshold}"
                    )
            
            # Cache miss
            return None
            
        except Exception as e:
            logger.error(f"Error searching cache: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            info = self.index.describe()
            
            return {
                "total_vectors": info.get("total_vectors", 0),
                "index_name": self.index_name,
                "dimension": self.dimension,
                "metric": "cosine"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def clear(self):
        """Clear all cached entries"""
        try:
            self.endee_client.delete_index(self.index_name)
            self._initialize_index()
            logger.info("Cache cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            raise
    
    def batch_store(self, pairs: list[tuple[str, str]]) -> list[str]:
        """
        Store multiple query-response pairs efficiently
        
        Args:
            pairs: List of (query, response) tuples
            
        Returns:
            List of vector IDs
        """
        try:
            vectors = []
            vector_ids = []
            
            for query, response in pairs:
                embedding = self.embedding_generator.generate(query)
                vector_id = self._generate_vector_id(query)
                
                vectors.append({
                    "id": vector_id,
                    "vector": embedding.tolist(),
                    "meta": {
                        "query": query,
                        "response": response,
                        "query_length": len(query),
                        "response_length": len(response)
                    }
                })
                
                vector_ids.append(vector_id)
            
            # Batch upsert to Endee
            self.index.upsert(vectors)
            
            logger.info(f"Batch stored {len(pairs)} query-response pairs")
            
            return vector_ids
            
        except Exception as e:
            logger.error(f"Error in batch store: {str(e)}")
            raise
