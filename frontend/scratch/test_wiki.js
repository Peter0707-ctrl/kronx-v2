async function testWikiSearch(query) {
  try {
    const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&format=json`
    const searchRes = await fetch(searchUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' } })
    const searchData = await searchRes.json()

    console.log('Search Results count:', searchData.query?.search?.length)
    if (searchData.query?.search?.length > 0) {
      const topTitle = searchData.query.search[0].title
      console.log('Top Title:', topTitle)

      const summaryUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`
      const summaryRes = await fetch(summaryUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' } })
      const summaryData = await summaryRes.json()

      console.log('Summary Extract Length:', summaryData.extract?.length)
      console.log('Summary Text:\n', summaryData.extract)
    }
  } catch (e) {
    console.error('Wiki error:', e)
  }
}

testWikiSearch("WHAT THE IMPORTANCE OF ORGANIC MATTERIAL IN INVIRONMENT AND THEIR DIS ADVANTAGES")
