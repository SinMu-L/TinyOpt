import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const blogCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    date: z.date(),
    lang: z.enum(['zh', 'en']),
    description: z.string(),
    tags: z.array(z.string()).optional(),
    image: z.string().optional(),
    translationKey: z.string().optional(),
    draft: z.boolean().optional().default(false),
  }),
});

const casesCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/cases' }),
  schema: z.object({
    title: z.string(),
    date: z.date(),
    lang: z.enum(['zh', 'en']),
    description: z.string(),
    image: z.string().optional(),
    translationKey: z.string().optional(),
    draft: z.boolean().optional().default(false),
  }),
});

export const collections = {
  blog: blogCollection,
  cases: casesCollection,
};
