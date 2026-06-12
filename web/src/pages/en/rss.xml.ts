import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export const GET = async () => {
  const posts = (await getCollection('blog'))
    .filter((p) => p.data.lang === 'en' && !p.data.draft && p.data.date <= new Date())
    .sort((a, b) => b.data.date.getTime() - a.data.date.getTime());

  return rss({
    title: 'TinyOpt - Blog',
    description: 'Latest news, tips and updates about TinyOpt batch image compressor',
    site: 'https://seojeck.com/en',
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.date,
      description: post.data.description,
      link: `/en/blog/${post.slug}/`,
    })),
  });
};
