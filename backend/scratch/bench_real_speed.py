import time
import httpx

client = httpx.Client(timeout=30.0)
models = ['tinyllama:latest', 'qwen2:0.5b', 'llama3.2:1b']

for m in models:
    t0 = time.time()
    t_first = None
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': 'Hello! Who are you?'}],
        'stream': True,
        'keep_alive': -1,
        'options': {'num_ctx': 256, 'num_predict': 100, 'num_thread': 4}
    }
    with client.stream('POST', 'http://localhost:11434/api/chat', json=payload) as res:
        for line in res.iter_lines():
            if line and t_first is None:
                t_first = time.time() - t0
                print(f"Model {m:<18}: First token arrived in {t_first:.2f} seconds!")
                break
