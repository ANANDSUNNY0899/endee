"""
Performance Benchmark Script
Tests Endee's performance with semantic caching workload
"""

import time
import random
import statistics
from typing import List, Tuple
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cache import SemanticCache
from embeddings import LocalEmbeddingGenerator


class CacheBenchmark:
    """Benchmark semantic cache performance"""
    
    def __init__(self):
        print("🚀 Initializing Nexus Cache Benchmark...")
        print("=" * 60)
        print("Using FREE local embeddings (all-MiniLM-L6-v2)")
        print("=" * 60)
        
        self.embedding_gen = LocalEmbeddingGenerator()
        self.cache = SemanticCache(self.embedding_gen)
        
        # Test dataset: common queries and variations
        self.test_queries = [
            ("How do I make tea?", "Boil water, add tea leaves, steep for 3-5 minutes, strain and serve."),
            ("What is the capital of France?", "The capital of France is Paris."),
            ("How to install Python?", "Download from python.org and run the installer."),
            ("What is machine learning?", "Machine learning is a subset of AI that learns from data."),
            ("How to write a resume?", "Include contact info, summary, experience, education, and skills."),
            ("What is blockchain?", "A decentralized ledger technology for secure transactions."),
            ("How to learn programming?", "Start with basics, practice coding, build projects, and read documentation."),
            ("What is climate change?", "Long-term shifts in global temperatures and weather patterns."),
            ("How to lose weight?", "Balanced diet, regular exercise, adequate sleep, and hydration."),
            ("What is quantum computing?", "Computing using quantum mechanical phenomena like superposition."),
        ]
        
        # Semantic variations of queries
        self.query_variations = {
            "How do I make tea?": [
                "Tea recipe please",
                "Steps to brew tea",
                "How to prepare tea?",
                "Tea making instructions"
            ],
            "What is the capital of France?": [
                "France's capital city?",
                "Which city is France's capital?",
                "Capital of French Republic",
                "Main city of France"
            ],
            "How to install Python?": [
                "Python installation steps",
                "Installing Python guide",
                "Setup Python on computer",
                "Python download and install"
            ]
        }
    
    def populate_cache(self, count: int = 10):
        """Populate cache with test data"""
        print(f"\n📥 Populating cache with {count} entries...")
        
        queries_to_cache = self.test_queries[:count]
        start = time.time()
        
        for query, response in queries_to_cache:
            self.cache.store(query, response)
        
        elapsed = (time.time() - start) * 1000
        print(f"✅ Cached {count} entries in {elapsed:.2f}ms")
        print(f"   Average: {elapsed/count:.2f}ms per entry")
    
    def benchmark_insert(self, count: int = 100) -> dict:
        """Benchmark insert performance"""
        print(f"\n🔧 Benchmarking INSERT operations ({count} vectors)...")
        
        latencies = []
        
        for i in range(count):
            # Generate unique query
            query = f"Test query number {i} with random content {random.randint(1000, 9999)}"
            response = f"Response for query {i}"
            
            start = time.time()
            self.cache.store(query, response)
            elapsed = (time.time() - start) * 1000
            
            latencies.append(elapsed)
        
        return {
            "operation": "INSERT",
            "count": count,
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p95_ms": self._percentile(latencies, 95),
            "p99_ms": self._percentile(latencies, 99)
        }
    
    def benchmark_search(self, count: int = 100) -> dict:
        """Benchmark search performance"""
        print(f"\n🔍 Benchmarking SEARCH operations ({count} queries)...")
        
        latencies = []
        hits = 0
        misses = 0
        
        # Use variations of cached queries
        test_variations = []
        for original_query, variations in self.query_variations.items():
            test_variations.extend(variations)
        
        for i in range(count):
            # Mix of cache hits and misses
            if i % 2 == 0 and i < len(test_variations):
                query = test_variations[i // 2]
            else:
                query = f"Uncached random query {random.randint(1000, 9999)}"
            
            start = time.time()
            result = self.cache.search(query, threshold=0.85)
            elapsed = (time.time() - start) * 1000
            
            latencies.append(elapsed)
            
            if result:
                hits += 1
            else:
                misses += 1
        
        return {
            "operation": "SEARCH",
            "count": count,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate": hits / count if count > 0 else 0,
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p95_ms": self._percentile(latencies, 95),
            "p99_ms": self._percentile(latencies, 99)
        }
    
    def benchmark_end_to_end(self, queries: int = 50) -> dict:
        """Simulate real-world usage pattern"""
        print(f"\n🌐 Benchmarking END-TO-END workflow ({queries} queries)...")
        
        total_start = time.time()
        
        cache_hits = 0
        cache_misses = 0
        api_calls_saved = 0
        cost_saved = 0.0
        
        for i in range(queries):
            # 70% semantic variations (cache hits expected)
            # 30% truly new queries
            if random.random() < 0.7 and i < len(self.query_variations):
                variations = list(self.query_variations.values())
                if variations:
                    query = random.choice(random.choice(variations))
            else:
                query = f"Completely new query about {random.choice(['AI', 'blockchain', 'cloud', 'security'])} topic {i}"
            
            # Search cache
            result = self.cache.search(query, threshold=0.85)
            
            if result:
                cache_hits += 1
                api_calls_saved += 1
                cost_saved += 0.004  # Approx LLM API cost
            else:
                cache_misses += 1
                # Simulate API call and cache result
                response = f"Generated response for: {query}"
                self.cache.store(query, response)
        
        total_elapsed = (time.time() - total_start) * 1000
        
        return {
            "total_queries": queries,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": cache_hits / queries if queries > 0 else 0,
            "api_calls_saved": api_calls_saved,
            "cost_saved_usd": round(cost_saved, 4),
            "total_time_ms": round(total_elapsed, 2),
            "avg_time_per_query_ms": round(total_elapsed / queries, 2)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_results(self, results: dict):
        """Pretty print benchmark results"""
        print("\n" + "=" * 60)
        
        # Check if this has an 'operation' field (INSERT/SEARCH) or not (END-TO-END)
        if 'operation' in results:
            print(f"📊 {results['operation']} Results")
        else:
            print(f"📊 END-TO-END Results")
        
        print("=" * 60)
        
        for key, value in results.items():
            if key == "operation":
                continue
            
            if isinstance(value, float):
                if "rate" in key:
                    print(f"{key:25} {value:.2%}")
                elif "usd" in key:
                    print(f"{key:25} ${value:.4f}")
                else:
                    print(f"{key:25} {value:.2f}")
            else:
                print(f"{key:25} {value}")
        
        print("=" * 60)
    
    def run_full_benchmark(self):
        """Run complete benchmark suite"""
        print("\n" + "🎯" * 30)
        print("      NEXUS CACHE - ENDEE PERFORMANCE BENCHMARK")
        print("🎯" * 30)
        
        # Populate cache
        self.populate_cache(count=10)
        
        # Run benchmarks
        insert_results = self.benchmark_insert(count=100)
        self.print_results(insert_results)
        
        search_results = self.benchmark_search(count=100)
        self.print_results(search_results)
        
        e2e_results = self.benchmark_end_to_end(queries=100)
        self.print_results(e2e_results)
        
        # Summary
        print("\n" + "✨" * 30)
        print("           BENCHMARK SUMMARY")
        print("✨" * 30)
        print(f"\n✅ INSERT Performance:")
        print(f"   Average Latency: {insert_results['avg_ms']:.2f}ms")
        print(f"   P95 Latency: {insert_results['p95_ms']:.2f}ms")
        
        print(f"\n✅ SEARCH Performance:")
        print(f"   Average Latency: {search_results['avg_ms']:.2f}ms")
        print(f"   Cache Hit Rate: {search_results['hit_rate']:.2%}")
        
        print(f"\n✅ REAL-WORLD Simulation:")
        print(f"   Cache Hit Rate: {e2e_results['hit_rate']:.2%}")
        print(f"   API Calls Saved: {e2e_results['api_calls_saved']}")
        print(f"   Cost Saved: ${e2e_results['cost_saved_usd']:.4f}")
        print(f"   Avg Query Time: {e2e_results['avg_time_per_query_ms']:.2f}ms")
        
        print("\n" + "=" * 60)
        print("🎉 Benchmark Complete!")
        print("=" * 60)


if __name__ == "__main__":
    try:
        benchmark = CacheBenchmark()
        benchmark.run_full_benchmark()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n\n❌ Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)