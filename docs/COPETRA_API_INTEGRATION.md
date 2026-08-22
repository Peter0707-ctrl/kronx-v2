# Copetra AI — Integration Guide

This document explains how to integrate **Copetra AI** into your application using the OpenAI-compatible Developer API.

**Production base URL**

```
https://miraculous-forgiveness-production-10d4.up.railway.app
```

**Chat completions endpoint**

```
POST /api/v1/chat/completions
```

Alias (same handler):

```
POST /api/gateway
```

---

## 1. Prerequisites

1. Create / sign in to a Copetra account.
2. Ask a Copetra **admin** to **Grant API** (Developer access) for your user.
3. Open **Settings → Developer**.
4. Create a project API key (`cpk_…`).
5. Copy the key immediately — it is shown only once.

### Unlimited tokens (selected users)

Users with **Developer API granted** (or `admin` role) receive **unlimited app-side token quotas**.

- Column / flag: `api_unlimited_tokens` (auto-enabled when API is granted)
- You may send a high `max_tokens` (e.g. `8192`)
- Provider (upstream model) limits may still apply

Non-granted accounts cannot call the API or create keys (`403 developer_not_granted`). Granted developers receive **unlimited app-side token quotas**.

---

## 2. Authentication

Send your key with **either** header:

```http
Authorization: Bearer cpk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

or:

```http
x-api-key: cpk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Recommended: use `Authorization: Bearer …` for browsers and SDKs.

---

## 3. Chat Completions (OpenAI-compatible)

### Request

```http
POST /api/v1/chat/completions
Content-Type: application/json
Authorization: Bearer cpk_...
```

```json
{
  "model": "copetra-ai",
  "messages": [
    { "role": "system", "content": "You are a helpful academic assistant." },
    { "role": "user", "content": "Explain photosynthesis in simple terms." }
  ],
  "temperature": 0.4,
  "max_tokens": 2048,
  "stream": false
}
```

| Field | Required | Description |
|--------|----------|-------------|
| `messages` | Yes* | OpenAI-style array of `{ role, content }` |
| `message` / `prompt` / `query` | Alt | Legacy single-string user prompt |
| `model` | No | Defaults to `copetra-ai` |
| `temperature` | No | Default `0.5` |
| `max_tokens` | No | No app-side cap — pass any value (default `8192`); upstream model limits may still apply |
| `stream` | No | `true` for Server-Sent Events (SSE) |
| `callback_url` | No | Async webhook (non-stream only) |

\*Provide `messages` **or** a legacy single prompt field.

### Non-streaming response

```json
{
  "id": "chatcmpl-…",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "copetra-ai",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "…" },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 120,
    "completion_tokens": 80,
    "total_tokens": 200
  },
  "response": "…",
  "status": "success",
  "developer_id": "u-…",
  "project": "My App"
}
```

Read the answer from:

- `choices[0].message.content` (OpenAI style), or  
- `response` (convenience alias)

### Streaming response

Set `"stream": true`. Response is `text/event-stream`:

```
data: {"id":"chatcmpl-…","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}

data: [DONE]
```

**Tip:** Prefer streaming for chat UIs — first tokens arrive sooner and reduce gateway timeouts.

---

## 4. Code examples

### cURL (non-stream)

```bash
curl -X POST "https://miraculous-forgiveness-production-10d4.up.railway.app/api/v1/chat/completions" \
  -H "Authorization: Bearer cpk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "copetra-ai",
    "messages": [
      {"role": "user", "content": "Karibu Singida TTC — introduce yourself briefly."}
    ],
    "max_tokens": 512,
    "stream": false
  }'
```

### cURL (stream)

```bash
curl -N -X POST "https://miraculous-forgiveness-production-10d4.up.railway.app/api/v1/chat/completions" \
  -H "Authorization: Bearer cpk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "copetra-ai",
    "messages": [{"role":"user","content":"List 3 study tips."}],
    "stream": true
  }'
```

### JavaScript (fetch)

```js
const res = await fetch(
  'https://miraculous-forgiveness-production-10d4.up.railway.app/api/v1/chat/completions',
  {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.COPETRA_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'copetra-ai',
      messages: [
        { role: 'system', content: 'You are Copetra AI.' },
        { role: 'user', content: 'Hello!' },
      ],
      temperature: 0.4,
      max_tokens: 2048,
      stream: false,
    }),
  }
)

const data = await res.json()
if (!res.ok) throw new Error(data?.error?.message || 'Copetra request failed')
console.log(data.choices?.[0]?.message?.content || data.response)
```

### Python

```python
import os
import requests

URL = "https://miraculous-forgiveness-production-10d4.up.railway.app/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ['COPETRA_API_KEY']}",
    "Content-Type": "application/json",
}
payload = {
    "model": "copetra-ai",
    "messages": [{"role": "user", "content": "Summarize machine learning in one paragraph."}],
    "max_tokens": 1024,
    "stream": False,
}

r = requests.post(URL, json=payload, headers=headers, timeout=120)
r.raise_for_status()
data = r.json()
print(data["choices"][0]["message"]["content"])
```

### PHP (Guzzle) — pattern used by Singida TTC

```php
use GuzzleHttp\Client;

$client = new Client([
    'timeout' => 180,
    'connect_timeout' => 25,
    'headers' => [
        'Authorization' => 'Bearer '.env('COPETRA_API_KEY'),
        'x-api-key' => env('COPETRA_API_KEY'),
        'Content-Type' => 'application/json',
        'Accept' => 'application/json',
    ],
]);

$response = $client->post(env('COPETRA_URL'), [
    'json' => [
        'model' => env('COPETRA_MODEL', 'copetra-ai'),
        'messages' => [
            ['role' => 'system', 'content' => 'You are the college AI assistant.'],
            ['role' => 'user', 'content' => $userMessage],
        ],
        'temperature' => 0.4,
        'max_tokens' => (int) env('COPETRA_MAX_TOKENS', 8192),
        'stream' => false,
    ],
]);

$json = json_decode($response->getBody()->getContents(), true);
$text = $json['choices'][0]['message']['content'] ?? ($json['response'] ?? '');
```

---

## 5. Environment variables (client apps)

```env
COPETRA_API_KEY=cpk_xxxxxxxx
COPETRA_URL=https://miraculous-forgiveness-production-10d4.up.railway.app/api/v1/chat/completions
COPETRA_MODEL=copetra-ai
COPETRA_TIMEOUT=180
COPETRA_MAX_TOKENS=8192
```

Never commit real API keys. Store them in server-side env only.

---

## 6. Async webhook mode (optional)

If you send `callback_url` (or `webhook_url`) **without** `stream: true`, the API returns `202 Accepted` and later POSTs the result to your URL:

```json
{
  "event": "copetra.chat.completion",
  "status": "success",
  "developer_id": "u-…",
  "project": "My App",
  "key_id": "…",
  "messages": [ … ],
  "response": "…",
  "timestamp": "2026-08-14T…"
}
```

Useful for long jobs where you do not want to hold an HTTP connection open.

---

## 7. Error reference

| HTTP | Code | Meaning |
|------|------|---------|
| 401 | `missing_api_key` | No Bearer / x-api-key |
| 403 | `invalid_api_key` | Key not found |
| 403 | `key_revoked` | Key disabled |
| 403 | `developer_not_granted` | Admin has not granted API access |
| 400 | `empty_payload` | No messages / prompt |
| 429 | `rate_limited` | Upstream provider rate limit |
| 502 | `provider_auth_failed` | Server GROQ key misconfigured |
| 503 | `provider_not_configured` | No upstream provider on server |
| 504 | `upstream_timeout` | Upstream timed out — retry with `stream: true` |

Error body shape:

```json
{
  "error": {
    "message": "Human readable message",
    "type": "api_error",
    "code": "upstream_timeout"
  }
}
```

### Reliability tips

1. Prefer **`stream: true`** for interactive chat.  
2. Retry once or twice on `502` / `503` / `504` (cold start).  
3. Keep client timeout ≥ **120–180 seconds**.  
4. Ensure your Copetra user has **Grant API** enabled.  
5. Use a valid `cpk_` key (not an empty or revoked key).

---

## 8. End-to-end integration checklist

1. [ ] Admin grants Developer API for your user  
2. [ ] Create API key in Settings → Developer  
3. [ ] Store `COPETRA_API_KEY` + `COPETRA_URL` in env  
4. [ ] Call `POST /api/v1/chat/completions` with Bearer auth  
5. [ ] Parse `choices[0].message.content`  
6. [ ] For chat UI: enable streaming SSE  
7. [ ] Handle 401/403/429/504 with user-friendly messages  
8. [ ] Confirm unlimited tokens if you are a granted developer  

---

## 9. Related endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/chat/completions` | OpenAI-compatible chat |
| `POST /api/gateway` | Same gateway (alias) |
| `GET/POST /api/developer/keys` | Manage your project keys (session auth) |

In-app docs and a live tester are also available under **Settings → Developer** in the Copetra web app.

---

## 10. Support

- Confirm your account has **API: Granted** in the Copetra Admin dashboard.  
- Confirm Railway / production service is awake (first request after sleep can be slower).  
- Check server env `GROQ_API_KEY` is set on the Copetra deployment if all clients get `provider_*` errors.
