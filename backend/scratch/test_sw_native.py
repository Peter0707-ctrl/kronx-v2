import asyncio
import time
import httpx

async def test_native_swahili():
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2:1b",
        "messages": [
            {"role": "system", "content": "You are Kronx. Respond in simple standard Swahili. Do not use emojis."},
            {"role": "user", "content": "Nisaidie na biashara yangu ya kuku Dar es Salaam"}
        ],
        "stream": True,
        "options": {
            "num_ctx": 1024,
            "num_predict": 300,
            "temperature": 0.6,
            "num_thread": 4
        }
    }
    t0 = time.time()
    t_first = None
    text = ""
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    if t_first is None:
                        t_first = time.time() - t0
                    import json
                    d = json.loads(line)
                    text += d.get("message", {}).get("content", "")
    print(f"First token in: {t_first:.2f}s | Total time: {time.time() - t0:.2f}s")
    print(f"Output text:\n{text}")

if __name__ == "__main__":
    asyncio.run(test_native_swahili())
