import type { APIRoute } from 'astro';

const SITE = 'https://tinyjpg-compressor.com';

interface PageEntry {
  url: string;
  changefreq?: string;
  priority?: string;
  lastmod?: string;
}

const pages: PageEntry[] = [
  { url: '/', changefreq: 'weekly', priority: '1.0' },
  { url: '/about/', changefreq: 'monthly', priority: '0.7' },
  { url: '/download/', changefreq: 'weekly', priority: '0.9' },
  { url: '/cases/', changefreq: 'monthly', priority: '0.6' },
  { url: '/contact/', changefreq: 'monthly', priority: '0.5' },
  { url: '/privacy/', changefreq: 'yearly', priority: '0.3' },
  { url: '/en/', changefreq: 'weekly', priority: '1.0' },
  { url: '/en/about/', changefreq: 'monthly', priority: '0.7' },
  { url: '/en/download/', changefreq: 'weekly', priority: '0.9' },
  { url: '/en/cases/', changefreq: 'monthly', priority: '0.6' },
  { url: '/en/contact/', changefreq: 'monthly', priority: '0.5' },
  { url: '/en/privacy/', changefreq: 'yearly', priority: '0.3' },
  { url: '/blog/', changefreq: 'weekly', priority: '0.8' },
  { url: '/en/blog/', changefreq: 'weekly', priority: '0.8' },
];

export const GET: APIRoute = async () => {
  const urlset = pages
    .map(
      (p) => `  <url>
    <loc>${SITE}${p.url}</loc>
    <changefreq>${p.changefreq}</changefreq>
    <priority>${p.priority}</priority>
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
