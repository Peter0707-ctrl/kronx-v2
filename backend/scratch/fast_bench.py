import time
import httpx

client = httpx.Client(timeout=30.0)
models = ['qwen2:0.5b', 'smollm:360m', 'tinyllama:1.1b']

for m in models:
    t0 = time.time()
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': 'Hi'}],
        'stream': True,
        'keep_alive': -1,
        'options': {'num_ctx': 256, 'num_predict': 150, 'num_thread': 4}
    }
    with client.stream('POST', 'http://localhost:11434/api/chat', json=payload) as res:
        for line in res.iter_lines():
            if line:
                print(f"Model {m:<14}: First token in {time.time()-t0:.2f}s")
                break
