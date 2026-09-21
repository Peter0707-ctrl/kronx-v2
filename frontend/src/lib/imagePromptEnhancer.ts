/**
 * Copetra Neural Canvas - Image Prompt Expansion Engine
 * Expands concise user prompts (e.g. 'horse', 'farasi', 'sports car') into
 * rich, photorealistic, cinematic prompt descriptions matching ChatGPT / DALL-E 3 visual fidelity.
 * Strictly zero emojis.
 */

const SWAHILI_DICTIONARY: Record<string, string> = {
  farasi: 'stallion horse',
  simba: 'majestic male lion',
  chui: 'leopard',
  duma: 'cheetah',
  ndovu: 'african elephant',
  tembo: 'african elephant',
  twiga: 'tall giraffe',
  pundamilia: 'zebra',
  kifaru: 'rhinoceros',
  kiboko: 'hippopotamus',
  mamba: 'crocodile',
  tai: 'golden eagle',
  ndege: 'bird',
  paka: 'graceful domestic cat',
  mbwa: 'loyal dog',
  'mbwa mwitu': 'african wild dog',
  ngiri: 'warthog',
  nyati: 'cape buffalo',
  swala: 'gazelle impala',
  nyoka: 'serpent snake',
  kobe: 'giant tortoise',
  nyangumi: 'majestic blue whale',
  papa: 'great white shark',
  samaki: 'vibrant tropical fish',
  gari: 'sleek modern luxury sports car',
  'gari la kifahari': 'luxury supercar',
  pikipiki: 'modern sleek sports motorcycle',
  baiskeli: 'modern road bicycle',
  meli: 'luxury cruise ocean liner',
  'ndege ya abiria': 'modern passenger airplane in flight',
  helikopta: 'modern helicopter in flight',
  'chombo cha anga': 'futuristic advanced spacecraft in deep space',

  nyumba: 'modern luxury architectural villa with glass walls',
  jiji: 'futuristic skyline metropolis city at twilight',
  pwani: 'pristine tropical beach paradise with turquoise water and palm trees',
  bahari: 'deep azure ocean with rolling waves',
  msitu: 'lush vibrant tropical rainforest with sunlight filtering through canopy',
  milima: 'majestic snow-capped mountain peaks rising into dramatic clouds',
  kilimanjaro: 'mount kilimanjaro with snowy peak rising above acacia plains',
  maporomoko: 'spectacular rushing waterfall cascades into a crystal clear pool',
  ua: 'exquisite blooming flower with dew drops',
  bustani: 'blooming vibrant botanical garden with stone pathways',
  machweo: 'breathtaking dramatic sunset sky with golden and magenta hues',
  macheo: 'serene golden sunrise horizon over gentle hills',
  mwanamke: 'stunning beautiful African woman portrait with radiant skin',
  mwanamume: 'handsome distinguished African man portrait with confident expression',
  mtoto: 'joyful smiling child portrait with bright expressive eyes',
  shujaa: 'regal African warrior in ornate ceremonial attire',
  roboti: 'futuristic humanoid cybernetic robot with glowing accents',
  kahawa: 'steaming cup of artisanal espresso coffee with intricate latte art',
  chakula: 'gourmet feast beautifully plated on rustic wooden table'
}

export interface EnhancedImageResult {
  expandedPrompt: string
  userCaption: string
  imageUrl: string
  markdown: string
}

function cleanInputPrompt(input: string): string {
  let cleaned = (input || '').trim()

  cleaned = cleaned
    .replace(/\[IMAGE:.*?\]/gi, '')
    .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE) DOCUMENT ATTACHED:.*?\][\s\S]*/gi, '')
    .replace(/\[PERSISTENT USER BRAIN MEMORY[\s\S]*/gi, '')
    .replace(/\[FEEDBACK HISTORY[\s\S]*/gi, '')
    .replace(/\[REAL-TIME VERIFIED WEB SEARCH DATA[\s\S]*/gi, '')
    .replace(/\[MEMORIZE:.*?\]/gi, '')
    .replace(/\[VISUAL_SUMMARY:.*?\]/gi, '')
    .trim()

  // Remove common prompt preambles in English and Swahili
  cleaned = cleaned
    .replace(/^(can you|please|kindly|could you)\s+/i, '')
    .replace(
      /^(generate|create|draw|make|design|render|produce|paint|craft|illustrate|tengeneza|chora|leta|niletee)\s+(an?\s+)?(image|picture|photo|illustration|art|drawing|painting|picha|mchoro)\s+(of|for|about|ya|za|kwa ajili ya|showing|depicting)?/i,
      ''
    )
    .replace(/^(tengeneza|chora)\s+picha\s+(ya|za|kwa ajili ya)?/i, '')
    .replace(/^(draw|paint)\s+(an?\s+)?(image|picture|photo|mchoro)/i, '')
    .replace(/^(generate|create|render|make)\s+/i, '')
    .replace(/\s+(picture|image|photo|drawing|mchoro|picha)$/i, '')
    .replace(/^(for|of|about|ya|za)\s+/i, '')
    .trim()

  return cleaned || input.trim()
}

export function expandImagePrompt(rawQuery: string): EnhancedImageResult {
  const cleaned = cleanInputPrompt(rawQuery)
  const lower = cleaned.toLowerCase()

  // Detect Swahili keywords and translate to rich English concepts
  let translatedSubject = cleaned
  let isSwahili = false

  for (const [swKey, enVal] of Object.entries(SWAHILI_DICTIONARY)) {
    const wordPattern = new RegExp(`\\b${swKey}\\b`, 'i')
    if (wordPattern.test(lower)) {
      translatedSubject = translatedSubject.replace(wordPattern, enVal)
      isSwahili = true
    }
  }

  const subjectLower = translatedSubject.toLowerCase()
  let expandedPrompt = ''
  let userCaption = cleaned

  // Category 1: Equine / Horse
  if (/\b(horse|stallion|mare|foal|mustang|colt|farasi)\b/i.test(subjectLower)) {
    expandedPrompt =
      'A majestic brown stallion with a dark flowing mane and tail galloping gracefully across an open lush green meadow, rolling hills and majestic mountain peaks under warm golden hour sunlight, dynamic full-body action shot, hyperrealistic, 8k resolution, cinematic lighting, photorealistic textures.'
    userCaption = isSwahili ? 'Farasi mwenye madaha akikimbia uwandani' : 'A majestic stallion galloping across a meadow'
  }
  // Category 2: Big Cats & African Savanna Wildlife
  else if (/\b(lion|simba|tiger|cheetah|duma|leopard|chui|elephant|tembo|ndovu|giraffe|twiga|zebra|pundamilia|rhino|kifaru|hippo|kiboko)\b/i.test(subjectLower)) {
    expandedPrompt = `A breathtaking, majestic ${translatedSubject} in its natural African savanna habitat during golden hour, sweeping wilderness plains and distant acacia trees under dramatic sky, national geographic wildlife photography, sharp focus on eyes and fur texture, 8k resolution, cinematic composition.`
    userCaption = isSwahili ? `${cleaned} katika mazingira ya asili ya nyika` : `A majestic ${cleaned} in its natural habitat`
  }
  // Category 3: Domestic Pets
  else if (/\b(cat|paka|kitten|dog|mbwa|puppy|husky|golden retriever|pug)\b/i.test(subjectLower)) {
    expandedPrompt = `An adorable, highly detailed ${translatedSubject} with captivating vibrant eyes and soft, lifelike fur textures, sitting in a warm sunlit cozy indoor setting, shallow depth of field, sharp studio focus, 8k resolution, warm ambient lighting.`
    userCaption = isSwahili ? `${cleaned} maridadi mwenye macho maangavu` : `A charming ${cleaned} with expressive eyes`
  }
  // Category 4: Sports Cars & Vehicles
  else if (/\b(car|gari|sports car|supercar|ferrari|lamborghini|porsche|bugatti|bmw|mercedes|motorcycle|pikipiki|concept car)\b/i.test(subjectLower)) {
    expandedPrompt = `A sleek high-performance ${translatedSubject} with aerodynamic curves and glossy metallic paint finish, parked on a scenic coastal highway at sunset, dramatic sky reflections on hood and windshield, ultra-detailed alloy wheels, cinematic commercial automotive photography, 8k resolution, ray-traced lighting.`
    userCaption = isSwahili ? `${cleaned} ya kisasa ya kifahari` : `A luxury high-performance ${cleaned}`
  }
  // Category 5: Landscapes & Nature
  else if (/\b(beach|pwani|ocean|bahari|sea|mountain|milima|kilimanjaro|sunset|machweo|sunrise|macheo|waterfall|maporomoko|forest|msitu|lake|ziwa|island|kisiwa)\b/i.test(subjectLower)) {
    expandedPrompt = `A breathtaking panoramic landscape of ${translatedSubject}, dramatic volumetric clouds catching golden sunlight, crystalline reflections on water surface, rich natural textures and depth of field, award-winning landscape photography, ultra-high resolution 8k, photorealistic.`
    userCaption = isSwahili ? `Mandhari nzuri ya ${cleaned}` : `A scenic panoramic landscape of ${cleaned}`
  }
  // Category 6: Human Portraits & Figures
  else if (/\b(portrait|woman|mwanamke|man|mwanamume|girl|msichana|boy|mvulana|queen|king|warrior|shujaa|person|mtu|model)\b/i.test(subjectLower)) {
    expandedPrompt = `A stunning, hyperrealistic portrait of ${translatedSubject}, authentic detailed skin texture with natural pores, captivating expressive eyes with deep emotional gaze, soft studio and golden ambient lighting, shot on 85mm lens with creamy bokeh background, 8k resolution, masterpiece.`
    userCaption = isSwahili ? `Picha maridadi ya ${cleaned}` : `A portrait of ${cleaned}`
  }
  // Category 7: Modern Architecture & Interiors
  else if (/\b(house|nyumba|mansion|villa|apartment|building|skyscraper|living room|interior|kitchen|city|jiji)\b/i.test(subjectLower)) {
    expandedPrompt = `An exquisite architectural photograph of ${translatedSubject}, modern minimalist luxury design, floor-to-ceiling glass walls, warm ambient interior illumination contrasting with twilight exterior sky, high-end architectural digest photography, 8k resolution.`
    userCaption = isSwahili ? `Muundo wa kisasa wa ${cleaned}` : `Architectural design of ${cleaned}`
  }
  // Category 8: Sci-Fi, Space & Futuristic
  else if (/\b(robot|roboti|cyborg|spaceship|chombo cha anga|space|galaxy|cyberpunk|futuristic|alien|starship|nebula)\b/i.test(subjectLower)) {
    expandedPrompt = `A visionary futuristic sci-fi visual of ${translatedSubject}, intricate mechanical and cybernetic details, glowing neon ambient lighting, deep atmospheric perspective, cinematic concept art, highly detailed textures, 8k resolution, ArtStation trending quality.`
    userCaption = isSwahili ? `Taswira ya kisasa ya ${cleaned}` : `A futuristic vision of ${cleaned}`
  }
  // Category 9: Food & Beverages
  else if (/\b(coffee|kahawa|food|chakula|cake|keki|burger|pizza|fruit|matunda|meal|dish)\b/i.test(subjectLower)) {
    expandedPrompt = `A mouthwatering gourmet presentation of ${translatedSubject}, artisanal culinary styling, fresh vibrant ingredients with subtle rising steam, warm restaurant table ambience, shallow depth of field, macro food photography, 8k resolution.`
    userCaption = isSwahili ? `Muonekano wa kuvutia wa ${cleaned}` : `Gourmet presentation of ${cleaned}`
  }
  // Category 10: General Fallback / Custom Descriptions
  else {
    // If user already wrote a rich detailed prompt (more than 70 chars), respect their exact vision
    if (cleaned.length > 70) {
      expandedPrompt = `${translatedSubject}, hyperrealistic, cinematic lighting, 8k resolution, sharp focus, masterpiece composition, highly detailed textures.`
      userCaption = cleaned
    } else {
      expandedPrompt = `A beautifully composed, highly detailed scene of ${translatedSubject}, vivid cinematic lighting, rich atmospheric environment, sharp focus, hyperrealistic, 8k resolution, photorealistic masterpiece.`
      userCaption = cleaned
    }
  }

  const encoded = encodeURIComponent(expandedPrompt.slice(0, 600))
  const seed = Math.floor(Math.random() * 1000000)
  const imageUrl = `https://image.pollinations.ai/prompt/${encoded}?width=1024&height=1024&model=flux&seed=${seed}&nologo=true&enhance=true`

  // Markdown format: Clean ChatGPT-style presentation without ugly headers
  const markdown = `![${userCaption}](${imageUrl})`

  return {
    expandedPrompt,
    userCaption,
    imageUrl,
    markdown
  }
}
