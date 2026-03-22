"""
Nexus Cache - Semantic Caching API
Main FastAPI application providing semantic cache endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import logging

from src.cache import SemanticCache
from src.embeddings import EmbeddingGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nexus Cache API",
    description="Semantic caching layer powered by Endee Vector Database",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
embedding_generator = EmbeddingGenerator()
semantic_cache = SemanticCache(embedding_generator)

# Statistics tracking
stats = {
    "total_queries": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_latency_ms": 0,
    "cost_saved_usd": 0.0
}

# Pydantic models
class CacheRequest(BaseModel):
    query: str
    response: str

class SearchRequest(BaseModel):
    query: str
    threshold: Optional[float] = 0.85

class SearchResponse(BaseModel):
    cache_hit: bool
    similarity: Optional[float] = None
    response: Optional[str] = None
    latency_ms: float
    original_query: Optional[str] = None
    cost_saved: bool

class StatsResponse(BaseModel):
    total_queries: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    avg_latency_ms: float
    cost_saved_usd: float


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Nexus Cache API",
        "vector_db": "Endee",
        "version": "1.0.0"
    }


@app.post("/cache", status_code=201)
async def cache_query(request: CacheRequest):
    """
    Store a query-response pair in the semantic cache
    
    Args:
        request: Contains query text and corresponding response
        
    Returns:
        Confirmation with vector ID
    """
    try:
        start_time = time.time()
        
        # Generate embedding and store in Endee
        vector_id = semantic_cache.store(request.query, request.response)
        
        latency = (time.time() - start_time) * 1000
        
        logger.info(f"Cached query (ID: {vector_id}) in {latency:.2f}ms")
        
        return {
            "status": "success",
            "vector_id": vector_id,
            "latency_ms": round(latency, 2),
            "query_length": len(request.query),
            "response_length": len(request.response)
        }
        
    except Exception as e:
        logger.error(f"Error caching query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Caching failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_cache(request: SearchRequest):
    """
    Search for semantically similar cached queries
    
    Args:
        request: Contains query text and optional similarity threshold
        
    Returns:
        Cache hit/miss status with response if found
    """
    try:
        start_time = time.time()
        
        # Update stats
        stats["total_queries"] += 1
        
        # Search semantic cache
        result = semantic_cache.search(request.query, threshold=request.threshold)
        
        latency = (time.time() - start_time) * 1000
        stats["total_latency_ms"] += latency
        
        if result:
            # Cache hit
            stats["cache_hits"] += 1
            stats["cost_saved_usd"] += 0.004  # Approximate LLM API cost saved
            
            logger.info(
                f"Cache HIT: similarity={result['similarity']:.3f}, "
                f"latency={latency:.2f}ms"
            )
            
            return SearchResponse(
                cache_hit=True,
                similarity=result["similarity"],
                response=result["response"],
                latency_ms=round(latency, 2),
                original_query=result["original_query"],
                cost_saved=True
            )
        else:
            # Cache miss
            stats["cache_misses"] += 1
            
            logger.info(f"Cache MISS: latency={latency:.2f}ms")
            
            return SearchResponse(
                cache_hit=False,
                latency_ms=round(latency, 2),
                cost_saved=False
            )
            
    except Exception as e:
        logger.error(f"Error searching cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Get cache performance statistics
    
    Returns:
        Detailed statistics about cache performance
    """
    try:
        total = stats["total_queries"]
        hits = stats["cache_hits"]
        
        hit_rate = (hits / total) if total > 0 else 0.0
        avg_latency = (stats["total_latency_ms"] / total) if total > 0 else 0.0
        
        # Get Endee storage stats
        cache_stats = semantic_cache.get_stats()
        
        return StatsResponse(
            total_queries=total,
            cache_hits=hits,
            cache_misses=stats["cache_misses"],
            cache_hit_rate=round(hit_rate, 4),
            avg_latency_ms=round(avg_latency, 2),
            cost_saved_usd=round(stats["cost_saved_usd"], 2)
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@app.delete("/cache/clear")
async def clear_cache():
    """
    Clear all cached entries (use with caution!)
    
    Returns:
        Confirmation of cache clearing
    """
    try:
        semantic_cache.clear()
        
        # Reset stats
        stats.update({
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_latency_ms": 0,
            "cost_saved_usd": 0.0
        })
        
        logger.warning("Cache cleared!")
        
        return {
            "status": "success",
            "message": "Cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Nexus Cache API...")
    logger.info("Endee Vector Database: Connected")
    logger.info("Embedding Model: OpenAI text-embedding-3-small")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
