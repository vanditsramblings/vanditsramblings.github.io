# Vandit's Ramblings

## About Me
**Lead Architect.**

I specialize in designing highly scalable, distributed systems. My focus is on structural integrity, reducing accidental complexity, and fostering engineering cultures that value deliberate decision-making without compromising on reactive coding.

## Core Ideals

* **Simple Complexity:** 
* **Boring for Old Dumb For New:** 

---

## Developer Guide

### How to use this
This repository contains the source code for my personal blog and portfolio, built using [Astro](https://astro.build/).
To run the project locally:
1. Clone the repository.
2. Install dependencies with `npm install`.
3. Start the development server with `npm run dev`.
4. Open `localhost:4321` in your browser.

### How to update pages
* **Main Pages**: The main pages of the site (like the home page or this about page) are located in `src/pages/`. They are `.astro` files.
* **Components**: Shared UI components are in `src/components/`.
* **Styling**: Global styles and design tokens are in `src/styles/global.css`.

### How to add new blogs
1. Navigate to the `src/content/blog/` directory.
2. Create a new markdown (`.md`) file. The file name should preferably follow the `YYYY-MM-DD-slug.md` format.
3. Add the frontmatter at the top of the file:
   ```markdown
   ---
   title: "Your Blog Post Title"
   description: "A brief summary of the post"
   pubDate: 2026-04-29
   ---
   ```
4. Write your blog content below the frontmatter using standard Markdown.
5. The blog will automatically be available on the site under the `/blog` route.
