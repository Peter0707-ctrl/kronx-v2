import time
import httpx

client = httpx.Client(timeout=30.0)
t0 = time.time()
t_first = None
count = 0

with client.stream('POST', 'http://localhost:11434/api/chat', json={'model': 'llama3.2:1b', 'messages': [{'role': 'user', 'content': 'Hello'}], 'stream': True}) as resp:
    print(f"Connection established in: {time.time() - t0:.2f}s")
    for line in resp.iter_lines():
        if line:
            if t_first is None:
                t_first = time.time() - t0
                print(f"FIRST TOKEN ARRIVED IN: {t_first:.2f}s")
            count += 1

print(f"Stream complete in: {time.time() - t0:.2f}s across {count} chunks.")
