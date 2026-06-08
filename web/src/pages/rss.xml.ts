import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export const GET = async () => {
  const posts = (await getCollection('blog'))
    .filter((p) => p.data.lang === 'zh' && !p.data.draft && p.data.date <= new Date())
    .sort((a, b) => b.data.date.getTime() - a.data.date.getTime());

  return rss({
    title: 'TinyJPG 批量压缩助手 - 新闻动态',
    description: '了解 TinyJPG 批量压缩助手的最新版本动态、使用技巧与行业资讯',
    site: 'https://seojeck.com',
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.date,
      description: post.data.description,
      link: `/blog/${post.slug}/`,
    })),
  });
};
