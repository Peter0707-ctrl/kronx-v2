import time
import httpx

client = httpx.Client(timeout=30.0)

for num_thread in [1, 2]:
    t0 = time.time()
    resp = client.post(
        'http://localhost:11434/api/chat',
        json={
            'model': 'qwen2:0.5b',
            'messages': [
                {'role': 'system', 'content': 'You are Kronx AI.'},
                {'role': 'user', 'content': 'What is AI?'}
            ],
            'stream': False,
            'options': {
                'num_ctx': 128,
                'num_predict': 50,
                'num_thread': num_thread
            }
        }
    )
    duration = time.time() - t0
    content = resp.json()['message']['content'].strip()
    print(f"Threads: {num_thread} | Time: {duration:.2f}s | Reply: {content[:60]}...")
