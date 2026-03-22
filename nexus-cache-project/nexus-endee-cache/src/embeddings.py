"""
Embedding Generator
Generates vector embeddings for text using OpenAI's embedding models
"""

import os
import logging
from typing import List
import numpy as np
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI's text-embedding models
    
    Supports both OpenAI API and local embedding models (future)
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
        dimension: int = 384
    ):
        """
        Initialize embedding generator
        
        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key (optional, can use env var)
            dimension: Embedding dimension (384 for small, 1536 for ada-002)
        """
        self.model = model
        self.dimension = dimension
        
        # Initialize OpenAI client
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = OpenAI(api_key=api_key)
        
        logger.info(
            f"EmbeddingGenerator initialized: model={model}, dim={dimension}"
        )
    
    def generate(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            Numpy array of embedding vector
        """
        try:
            # Clean text
            text = text.strip().replace("\n", " ")
            
            if not text:
                raise ValueError("Cannot generate embedding for empty text")
            
            # Call OpenAI API
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimension  # Specify dimension for small model
            )
            
            # Extract embedding
            embedding = response.data[0].embedding
            
            # Convert to numpy array
            embedding_array = np.array(embedding, dtype=np.float32)
            
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            
            return embedding_array
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of input texts
            
        Returns:
            List of numpy arrays (embeddings)
        """
        try:
            # Clean texts
            cleaned_texts = [text.strip().replace("\n", " ") for text in texts]
            
            # Filter empty texts
            valid_texts = [t for t in cleaned_texts if t]
            
            if not valid_texts:
                raise ValueError("No valid texts to embed")
            
            # Call OpenAI API with batch
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                dimensions=self.dimension
            )
            
            # Extract embeddings
            embeddings = [
                np.array(item.embedding, dtype=np.float32)
                for item in response.data
            ]
            
            logger.debug(f"Generated {len(embeddings)} embeddings in batch")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            # Normalize vectors
            vec1_norm = vec1 / np.linalg.norm(vec1)
            vec2_norm = vec2 / np.linalg.norm(vec2)
            
            # Calculate cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            
            # Ensure in range [0, 1]
            similarity = float(np.clip(similarity, 0.0, 1.0))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            raise


class LocalEmbeddingGenerator:
    """
    Alternative: Generate embeddings using local models (e.g., sentence-transformers)
    
    This is for users who want to avoid OpenAI API costs or work offline.
    Requires: pip install sentence-transformers
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding generator
        
        Args:
            model_name: HuggingFace model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(
                f"LocalEmbeddingGenerator initialized: "
                f"model={model_name}, dim={self.dimension}"
            )
            
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    
    def generate(self, text: str) -> np.ndarray:
        """Generate embedding for single text using local model"""
        text = text.strip()
        if not text:
            raise ValueError("Cannot generate embedding for empty text")
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts using local model"""
        cleaned_texts = [t.strip() for t in texts if t.strip()]
        
        if not cleaned_texts:
            raise ValueError("No valid texts to embed")
        
        embeddings = self.model.encode(
            cleaned_texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return [emb.astype(np.float32) for emb in embeddings]
