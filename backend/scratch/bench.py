import asyncio
import time
from orchestrator.core import KronxOrchestrator

async def main():
    orch = KronxOrchestrator()
    model = await orch.get_active_model()
    print(f"Active model: {model}")
    t0 = time.time()
    count = 0
    async for chunk in orch.stream('Hello', 'Friend', 'sw', 'test_bench', []):
        count += 1
    print(f"Completed in {time.time() - t0:.2f} seconds. Received {count} chunks.")

if __name__ == "__main__":
    asyncio.run(main())
