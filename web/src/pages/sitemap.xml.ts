import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

const SITE = 'https://seojeck.com';

export const GET: APIRoute = async () => {
  const now = new Date();
  const blogPosts = (await getCollection('blog'))
    .filter((p) => !p.data.draft && !p.data.noindex && p.data.date <= now);
  const casePosts = (await getCollection('cases'))
    .filter((p) => !p.data.draft && !p.data.noindex && p.data.date <= now);

  const staticPages = [
    { url: '/', changefreq: 'weekly', priority: '1.0' },
    { url: '/about/', changefreq: 'monthly', priority: '0.7' },
    { url: '/download/', changefreq: 'weekly', priority: '0.9' },
    { url: '/cases/', changefreq: 'monthly', priority: '0.6' },
    { url: '/contact/', changefreq: 'monthly', priority: '0.5' },
    { url: '/privacy/', changefreq: 'yearly', priority: '0.3' },
    { url: '/terms/', changefreq: 'yearly', priority: '0.3' },
    { url: '/zh/', changefreq: 'weekly', priority: '0.9' },
    { url: '/zh/about/', changefreq: 'monthly', priority: '0.6' },
    { url: '/zh/download/', changefreq: 'weekly', priority: '0.8' },
    { url: '/zh/cases/', changefreq: 'monthly', priority: '0.5' },
    { url: '/zh/contact/', changefreq: 'monthly', priority: '0.4' },
    { url: '/zh/privacy/', changefreq: 'yearly', priority: '0.2' },
    { url: '/zh/terms/', changefreq: 'yearly', priority: '0.2' },
    { url: '/zh/blog/', changefreq: 'weekly', priority: '0.7' },
  ];

  const allPages = [
    ...staticPages,
    ...blogPosts.map((p) => ({
      url: `/${p.data.lang === 'en' ? '' : 'zh/'}blog/${p.id}/`,
      changefreq: 'monthly' as const,
      priority: '0.6' as const,
      lastmod: p.data.date.toISOString().split('T')[0],
    })),
    ...casePosts.map((p) => ({
      url: `/${p.data.lang === 'en' ? '' : 'zh/'}cases/${p.id}/`,
      changefreq: 'monthly' as const,
      priority: '0.6' as const,
      lastmod: p.data.date.toISOString().split('T')[0],
    })),
  ];

  const urlset = allPages
    .map(
      (p) => `  <url>
    <loc>${SITE}${p.url}</loc>
    <changefreq>${p.changefreq}</changefreq>
    <priority>${p.priority}</priority>
    ${p.lastmod ? `<lastmod>${p.lastmod}</lastmod>` : ''}
  </url>`
    )
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlset}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
