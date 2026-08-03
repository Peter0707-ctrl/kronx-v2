const DEFAULT_KEY_B64 = 'QVEuQWI4Uk42S1BDRjN6T2E1YjdicG04WDZkZlJaMFhRT2NueEV5S3YyMUNETUROVzhsZnc='
const apiKey = Buffer.from(DEFAULT_KEY_B64, 'base64').toString('utf-8')

async function testGeminiGenerate() {
  const model = 'gemini-flash-latest'
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`

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

    const data = await res.json()
    console.log('Answer:', data.candidates?.[0]?.content?.parts?.[0]?.text)
  } catch (err) {
    console.error('Fetch thrown error:', err)
  }
}

testGeminiGenerate()
