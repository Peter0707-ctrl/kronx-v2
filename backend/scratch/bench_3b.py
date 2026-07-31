import asyncio
import time
from orchestrator.core import KronxOrchestrator

async def main():
    orch = KronxOrchestrator()
    # Test Llama 3.2 3B speed
    orch._cached_model = "llama3.2:3b"
    print("Testing llama3.2:3b...")
    t0 = time.time()
    count = 0
    async for chunk in orch.stream('Hello', 'Friend', 'sw', 'test_bench', []):
        count += 1
    print(f"Llama 3.2 3B completed in {time.time() - t0:.2f} seconds.")

if __name__ == "__main__":
    asyncio.run(main())
