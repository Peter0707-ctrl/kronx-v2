import time
import httpx

client = httpx.Client(timeout=30.0)
models = ['qwen2:0.5b', 'tinyllama:1.1b', 'llama3.2:1b']

for model in models:
    t0 = time.time()
    t_first = None
    count = 0
    try:
        with client.stream('POST', 'http://localhost:11434/api/chat', json={'model': model, 'messages': [{'role': 'user', 'content': 'Hello'}], 'stream': True}) as resp:
            for line in resp.iter_lines():
                if line and t_first is None:
                    t_first = time.time() - t0
                    break
        print(f"Model: {model:<15} | First token: {t_first:.2f}s")
    except Exception as e:
        print(f"Model: {model:<15} | Error: {e}")
