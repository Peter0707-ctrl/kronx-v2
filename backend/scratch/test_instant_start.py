import time
import httpx

client = httpx.Client(timeout=30.0)
t0 = time.time()
t_first = None

payload = {
    'model': 'llama3.2:1b',
    'messages': [{'role': 'user', 'content': 'Hi'}],
    'stream': True,
    'keep_alive': -1,
    'options': {
        'num_ctx': 128,
        'num_predict': 100,
        'num_thread': 4
    }
}

with client.stream('POST', 'http://localhost:11434/api/chat', json=payload) as res:
    for line in res.iter_lines():
        if line and t_first is None:
            t_first = time.time() - t0
            print(f"FIRST TOKEN IN: {t_first:.2f}s")
            break

print(f"Total time to start typing: {t_first:.2f}s")
