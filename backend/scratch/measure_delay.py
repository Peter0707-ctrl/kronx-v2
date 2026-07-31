import time
import httpx

client = httpx.Client(timeout=30.0)
t0 = time.time()
t_first = None

payload = {
    'model': 'smollm:360m',
    'messages': [
        {'role': 'system', 'content': 'You are Kronx. Answer in detailed English.'},
        {'role': 'user', 'content': 'Explain quantum computing simply.'}
    ],
    'stream': True,
    'keep_alive': -1,
    'options': {
        'num_ctx': 512,
        'num_predict': 250,
        'num_thread': 4
    }
}

with client.stream('POST', 'http://localhost:11434/api/chat', json=payload) as res:
    print(f"HTTP Connection established: {time.time() - t0:.2f}s")
    for line in res.iter_lines():
        if line and t_first is None:
            t_first = time.time() - t0
            print(f"--> FIRST TOKEN RECEIVED AT: {t_first:.2f}s <--")
            break

print(f"Total time to first token: {time.time() - t0:.2f}s")
