import { defineConfig } from 'astro/config';
import rehypeMermaid from 'rehype-mermaid';

import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  markdown: {
    rehypePlugins: [
      [rehypeMermaid, { strategy: 'img-svg' }]
    ],
  },

  vite: {
    plugins: [tailwindcss()],
  },
});