const DEFAULT_KEY_B64 = 'QVEuQWI4Uk42S1BDRjN6T2E1YjdicG04WDZkZlJaMFhRT2NueEV5S3YyMUNETUROVzhsZnc='
const apiKey = Buffer.from(DEFAULT_KEY_B64, 'base64').toString('utf-8')

async function testGeminiStream() {
  const model = 'gemini-flash-latest'
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:streamGenerateContent?key=${apiKey}&alt=sse`

  const contents = [{ role: 'user', parts: [{ text: "Explain quantum physics in 2 simple sentences" }] }]

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents }),
    })

    console.log('HTTP Status:', res.status, res.statusText)
    if (!res.ok) {
      const errText = await res.text()
      console.log('Error Body:', errText)
      return
    }

    const text = await res.text()
    console.log('Response Length:', text.length)
    console.log('First 300 chars:', text.substring(0, 300))
  } catch (err) {
    console.error('Fetch thrown error:', err)
  }
}

testGeminiStream()
