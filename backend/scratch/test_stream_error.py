import asyncio
from orchestrator.core import KronxOrchestrator

async def main():
    k = KronxOrchestrator()
    print("Testing stream output...")
    async for chunk in k.stream("What is 2 + 2?", "Friend", "en", "conv-1", []):
        print(chunk, end="", flush=True)
    print("\n--- DONE ---")

if __name__ == "__main__":
    asyncio.run(main())
