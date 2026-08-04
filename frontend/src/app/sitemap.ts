import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://miraculous-forgiveness-production-10d4.up.railway.app'
  const lastMod = new Date()

  return [
    {
      url: `${baseUrl}`,
      lastModified: lastMod,
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: `${baseUrl}/chat`,
      lastModified: lastMod,
      changeFrequency: 'always',
      priority: 0.95,
    },
    {
      url: `${baseUrl}/landing`,
      lastModified: lastMod,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
    {
      url: `${baseUrl}/dashboard`,
      lastModified: lastMod,
      changeFrequency: 'daily',
      priority: 0.85,
    },
    {
      url: `${baseUrl}/api/gateway`,
      lastModified: lastMod,
      changeFrequency: 'monthly',
      priority: 0.5,
    },
  ]
}
