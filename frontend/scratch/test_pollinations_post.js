async function testPollinationsPOST() {
  const url = 'https://text.pollinations.ai/'
  const body = {
    messages: [
      { role: 'user', content: 'Explain the importance of organic material in the environment.' }
    ],
    model: 'openai'
  }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    console.log('Status:', res.status)
    const text = await res.text()
    console.log('Output length:', text.length)
    console.log('First 400 chars:', text.substring(0, 400))
  } catch (e) {
    console.error('Error:', e)
  }
}

testPollinationsPOST()
