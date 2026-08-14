import time
import asyncio
import httpx
import os
import sys
from fastapi.testclient import TestClient

# Adjust path to import main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from memory.store import MemoryStore

def run_benchmarks():
    client = TestClient(app)
    
    # 1. Measure Health Response Latency
    health_times = []
    for _ in range(20):
        t0 = time.perf_counter()
        resp = client.get("/health")
        t1 = time.perf_counter()
        assert resp.status_code == 200
        health_times.append((t1 - t0) * 1000)
    avg_health = sum(health_times) / len(health_times)
    
    # 2. Measure System Status Response Latency (cached active model check)
    status_times = []
    # Call first time to populate/cache active model
    client.get("/api/system/status")
    for _ in range(10):
        t0 = time.perf_counter()
        resp = client.get("/api/system/status")
        t1 = time.perf_counter()
        assert resp.status_code == 200
        status_times.append((t1 - t0) * 1000)
    avg_status = sum(status_times) / len(status_times)
    
    # 3. Measure Concurrent memory reads/writes
    store = MemoryStore()
    store.path = "test_perf_store.json"
    if os.path.exists(store.path):
        os.remove(store.path)
    store._ensure_file()
    
    # Write 100 entries sequentially
    t0 = time.perf_counter()
    for i in range(100):
        store.save_memory("perf_conv", f"data_{i}")
    t1 = time.perf_counter()
    write_100_ms = (t1 - t0) * 1000
    
    # Read 100 entries sequentially
    t0 = time.perf_counter()
    for _ in range(100):
        store.get_memories("perf_conv")
    t1 = time.perf_counter()
    read_100_ms = (t1 - t0) * 1000
    
    if os.path.exists(store.path):
        os.remove(store.path)
        
    print(f"BENCHMARK_RESULTS:")
    print(f"avg_health_latency_ms: {avg_health:.2f}")
    print(f"avg_status_latency_ms: {avg_status:.2f}")
    print(f"sequential_100_writes_ms: {write_100_ms:.2f}")
    print(f"sequential_100_reads_ms: {read_100_ms:.2f}")

if __name__ == "__main__":
    run_benchmarks()
