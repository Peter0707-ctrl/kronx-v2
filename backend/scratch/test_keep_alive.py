import time
import httpx

client = httpx.Client(timeout=30.0)
t0 = time.time()

with client.stream('POST', 'http://localhost:11434/api/chat', json={'model': 'qwen2:0.5b', 'messages': [{'role': 'user', 'content': 'Hello'}], 'stream': True, 'keep_alive': -1}) as res:
    print(f"Warmup 1 completed in {time.time() - t0:.2f}s")

t1 = time.time()
with client.stream('POST', 'http://localhost:11434/api/chat', json={'model': 'qwen2:0.5b', 'messages': [{'role': 'user', 'content': 'What is python?'}], 'stream': True, 'keep_alive': -1}) as res:
    for line in res.iter_lines():
        if line:
            print(f"IMMEDIATE RESPONSE (Warm): {time.time() - t1:.2f}s")
            break
