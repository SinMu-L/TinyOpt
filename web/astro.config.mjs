import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://tinyjpg-compressor.com',
  integrations: [
    tailwind(),
  ],
});
