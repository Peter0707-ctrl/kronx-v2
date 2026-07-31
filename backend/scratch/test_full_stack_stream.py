import asyncio
import httpx

async def main():
    payload = {
        'message': 'Who are you?',
        'mode': 'Friend',
        'language': 'en',
        'conversation_id': 'test-conv',
        'history': []
    }
    print("Testing SSE streaming from http://localhost:8000/api/chat/stream...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", "http://localhost:8000/api/chat/stream", json=payload) as response:
            print("Status Code:", response.status_code)
            async for line in response.aiter_lines():
                if line:
                    print("RECEIVED LINE:", repr(line))

if __name__ == "__main__":
    asyncio.run(main())
