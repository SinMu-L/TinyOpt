import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
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
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.date(),
    lang: z.enum(['zh', 'en']),
    description: z.string(),
    image: z.string().optional(),
    draft: z.boolean().optional().default(false),
  }),
});

export const collections = {
  blog: blogCollection,
  cases: casesCollection,
};
