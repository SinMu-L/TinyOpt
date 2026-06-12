import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import preact from '@astrojs/preact';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  site: 'https://seojeck.com',
  trailingSlash: 'always',
  output: 'server',
  adapter: vercel(),
  integrations: [
    tailwind(),
    preact(),
  ],
});
