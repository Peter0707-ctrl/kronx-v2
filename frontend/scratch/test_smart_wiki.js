function extractKeywords(query) {
  // Remove filler question words, typos, and stop words
  const stopWords = /\b(what|is|the|importance|of|in|and|their|dis|advantages|tell|me|about|explain|define|can|you|how|why|does|do)\b/gi
  let cleaned = query.replace(stopWords, ' ').replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()

  // Fix common typos
  cleaned = cleaned.replace(/matterial/gi, 'matter')
                   .replace(/invironment/gi, 'environment')
                   .replace(/tanzanai/gi, 'tanzania')

  return cleaned || query
}

async function testSmartWiki(query) {
  const keywords = extractKeywords(query)
  console.log('Original Query:', query)
  console.log('Extracted Keywords:', keywords)

  try {
    const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(keywords)}&format=json`
    const searchRes = await fetch(searchUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' } })
    const searchData = await searchRes.json()

    if (searchData.query?.search?.length > 0) {
      const topTitle = searchData.query.search[0].title
      console.log('Matched Article:', topTitle)

      const summaryUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`
      const summaryRes = await fetch(summaryUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' } })
      const summaryData = await summaryRes.json()

      console.log('Extract:', summaryData.extract)
    }
  } catch (e) {
    console.error(e)
  }
}

testSmartWiki("WHAT THE IMPORTANCE OF ORGANIC MATTERIAL IN INVIRONMENT AND THEIR DIS ADVANTAGES")
