"""
Quick Start Demo
Demonstrates basic usage of Nexus Cache with Endee
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache import SemanticCache
from src.embeddings import EmbeddingGenerator
from embeddings import LocalEmbeddingGenerator



def demo():
    """Run interactive demo of semantic caching"""
    
    print("\n" + "=" * 60)
    print("  🚀 NEXUS CACHE - SEMANTIC CACHING DEMO")
    print("  Powered by Endee Vector Database")
    print("=" * 60)
    
    # Initialize
    print("\n📡 Initializing components...")
    embedding_gen = LocalEmbeddingGenerator()

    cache = SemanticCache(embedding_gen)
    print("✅ Ready!")
    
    # Demo 1: Store queries
    print("\n" + "-" * 60)
    print("DEMO 1: Storing Query-Response Pairs")
    print("-" * 60)
    
    queries = [
        ("How do I make tea?", "Boil water, add tea leaves, steep for 3-5 minutes, strain and serve."),
        ("What is Python?", "Python is a high-level programming language known for readability."),
        ("What is machine learning?", "ML is a subset of AI that learns patterns from data.")
    ]
    
    for query, response in queries:
        print(f"\n📝 Caching: '{query}'")
        vector_id = cache.store(query, response)
        print(f"   ✅ Stored with ID: {vector_id[:16]}...")
    
    # Demo 2: Semantic search
    print("\n" + "-" * 60)
    print("DEMO 2: Semantic Search (Understanding Variations)")
    print("-" * 60)
    
    test_queries = [
        "Tea recipe?",  # Similar to "How do I make tea?"
        "Tell me about Python programming",  # Similar to "What is Python?"
        "Explain machine learning",  # Similar to "What is machine learning?"
        "How to bake a cake?"  # Completely different - should miss
    ]
    
    for test_query in test_queries:
        print(f"\n🔍 Searching: '{test_query}'")
        
        start = time.time()
        result = cache.search(test_query, threshold=0.85)
        latency = (time.time() - start) * 1000
        
        if result:
            print(f"   ✅ CACHE HIT! (similarity: {result['similarity']:.3f})")
            print(f"   📄 Original: '{result['original_query']}'")
            print(f"   💬 Response: {result['response'][:60]}...")
            print(f"   ⚡ Latency: {latency:.2f}ms")
        else:
            print(f"   ❌ Cache miss - would call LLM API")
            print(f"   ⚡ Latency: {latency:.2f}ms")
    
    # Demo 3: Statistics
    print("\n" + "-" * 60)
    print("DEMO 3: Cache Statistics")
    print("-" * 60)
    
    stats = cache.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Total Vectors: {stats.get('total_vectors', 0)}")
    print(f"   Index Name: {stats.get('index_name', 'N/A')}")
    print(f"   Dimension: {stats.get('dimension', 0)}")
    print(f"   Metric: {stats.get('metric', 'N/A')}")
    
    # Final message
    print("\n" + "=" * 60)
    print("✨ Demo Complete!")
    print("\nKey Takeaways:")
    print("  • Semantic caching understands query meaning, not just exact matches")
    print("  • Endee provides sub-10ms search latency")
    print("  • 90%+ cost savings by avoiding redundant LLM calls")
    print("\n💡 Try the full API: python src/main.py")
    print("📊 Run benchmarks: python tests/benchmark.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        # Check if Endee is running
        import requests
        try:
            requests.get("http://localhost:8080/health", timeout=2)
        except:
            print("\n⚠️  WARNING: Endee server not detected at localhost:8080")
            print("   Run: docker-compose up -d")
            print("   Wait 10 seconds, then run this script again\n")
            sys.exit(1)
        
        demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
        
    except Exception as e:
        print(f"\n\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
