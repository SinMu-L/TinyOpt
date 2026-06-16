---
title: Google PageSpeed Score Under 60? Complete Guide to Image Lazy Loading (Plus 300-Product Batch Optimization)
date: 2026-06-08
lang: en
translationKey: pagespeed-lazy-loading-guide
description: Tackle the most common PageSpeed pain point for e-commerce sites — from lazy loading principles to batch image optimization, cut LCP from 8 seconds to 2.
tags: [PageSpeed, performance optimization, lazy loading, e-commerce, batch processing]
---

You know that feeling when you run Google PageSpeed Insights on your e-commerce site and see a red score in the 40s? I know it all too well.

Last month, a fashion e-commerce client came to me. The homepage LCP (Largest Contentful Paint) was 8.2 seconds. PageSpeed mobile score: 31. Google had already reduced crawl frequency for the low-scoring site, and organic traffic had dropped 40% in six months.

After investigation, three image issues accounted for 70% of the penalties: uncompressed images, no modern format, and first-screen images not lazy-loaded. The client had 320 product photos — manual processing was impossible.

But this problem can be solved in an afternoon.

## First, Understand What PageSpeed Is Penalizing

Google PageSpeed's scoring revolves around Core Web Vitals. Three metrics are directly image-related:

| Metric | Meaning | How Images Affect It | Threshold |
|--------|---------|---------------------|-----------|
| **LCP** | Largest Contentful Paint | Large hero image loading slowly | > 2.5s poor |
| **FID/INP** | First Input Delay | Image decoding blocking main thread | > 100ms poor |
| **CLS** | Cumulative Layout Shift | Images without width/height attributes | > 0.1 poor |

Of these three, **LCP is the most common offender for e-commerce sites**. Simple reason: the homepage hero banner is usually a high-res image, uncompressed and not lazy-loaded — one request dragging down the entire score.

## 01. What Is Image Lazy Loading

Lazy loading means: **only load images visible in the current viewport; load the rest as the user scrolls near them**. The traditional approach loads every image on page open, regardless of visibility.

A typical e-commerce product listing page has 40 thumbnails at 200KB each — that's 8MB total. The user might only see 6 images on first screen. Lazy loading means:

- On page open, only load 6 first-screen images (~1.2MB)
- Load the remaining 34 as the user scrolls
- First-screen load speed improves by **3-5×**

Google itself has been pushing lazy loading — native `loading="lazy"` has been supported since Chrome 76, no JavaScript library needed.

```html
<!-- One line for native lazy loading -->
<img src="product.webp" loading="lazy" alt="Product photo" width="600" height="600">
```

If your site is built on WordPress + WooCommerce, most modern themes enable lazy loading by default. But for custom-built sites or older themes, check whether your `<img>` tags include this attribute.

## 02. Lazy Loading Alone Isn't Enough — Images Must Be Compressed First

Lazy loading solves "when to load," but if each image is 500KB+, lazy loading won't save you.

Here's test data showing the impact of different image treatments on LCP:

| Treatment | Image Size | First Request Time (4G) | LCP |
|-----------|-----------|----------------------|-----|
| Original, no lazy loading | 820 KB | 3.8 sec | 7.2 sec |
| Compressed JPEG Q85 | 310 KB | 1.6 sec | 4.1 sec |
| Compressed + WebP + lazy loading | 105 KB | 0.4 sec | **1.8 sec** |

The combined effect is multiplicative, not additive. Lazy loading alone might bring LCP from 7.2s to 5s, but to reach the green zone under 2.5s, **compression + format conversion + lazy loading** is essential.

## 03. Your E-Commerce Site Might Not Be Using Lazy Loading at All

How to check? Open Chrome DevTools, F12 → Network tab → refresh the page. If 30-40 image requests fire immediately, lazy loading is off.

With proper lazy loading, only 5-10 image requests should fire on page open, with more loading as you scroll.

Common pitfalls:

- **Slider/Carousel components**: Many slider plugins preload all slide images. If your homepage carousel has 5 banners at 800KB each, that's 4MB wasted on first screen.
- **Product grid pages**: Shopify or WooCommerce default product listings often don't lazy load. 50 products × 1 image = 50 simultaneous requests.
- **Footer logos and social icons**: These start loading before the user ever scrolls down.

## 04. How to Batch-Process 300 Product Images

This is the most painful part for e-commerce sellers. Your site might have hundreds of SKUs, each with multiple photos (main, detail, lifestyle) — totaling in the thousands.

Manual processing time estimate:

```
1 image: Open PS → compress → export WebP → save (~40 sec)
300 images: 300 × 40 sec = 3.3 hours
1000 images: 1000 × 40 sec = 11 hours
```

With a batch tool, the workflow becomes:

**Step 1: Organize images by product folder**

Place each SKU's images in its own folder (most sites already store images this way).

**Step 2: Drag into TinyOpt for batch processing**

Drag all product folders into TinyOpt at once, enable recursive subfolder scanning:

- Format conversion: unified output as WebP
- Compression: Tinify engine auto-compression
- Resize: set max width to 1200px if product images are too large
- Preserve directory structure: output directly overrides originals in place

**Step 3: Add lazy loading to theme templates**

Add `loading="lazy"` and explicit `width`/`height` (solves CLS) to `<img>` tags in your theme. Most e-commerce themes only need changes in one template file.

👉 [Download TinyOpt, free processing for first 50 images](/download/)

## 05. Advanced: Using `<picture>` for Multi-Format Compatibility

If your e-commerce site serves a global audience with diverse browsers, use the `<picture>` tag for multi-format fallback:

```html
<picture>
  <source srcset="product.avif" type="image/avif">
  <source srcset="product.webp" type="image/webp">
  <img src="product.jpg" loading="lazy" width="600" height="600" alt="Product photo">
</picture>
```

TinyOpt can output both WebP and AVIF versions of the same batch (run two separate tasks to different directories), then reference the appropriate paths in your template.

## The Core Problem

Low PageSpeed scores aren't about technical inability — it's that images are treated as "content" rather than "performance assets." Most e-commerce workflows look like:

```
Shoot/get images from supplier → upload directly → wait for site to slow down → then think about optimization
```

The correct workflow:

```
Shoot/get images from supplier → batch compress + convert to WebP → set loading strategy → upload
```

Move optimization before upload, not as a post-mortem. Once this habit is formed, "image-related" red warnings on PageSpeed will disappear.

## FAQ

**01. Does lazy loading affect SEO?**

No. Googlebot renders pages with JavaScript and simulates scrolling — it can properly crawl lazy-loaded images. Google officially supports native `loading="lazy"`. However, don't lazy-load critical first-screen images (like hero banners), as that actually hurts LCP.

**02. I added loading="lazy" but PageSpeed didn't change?**

Because your images are still too large. Lazy loading solves "when to load," not "how much to load." Compress images to a reasonable size (under 150KB each) first, then add lazy loading. Only the combination shows significant improvement.

**03. What's the ideal size for e-commerce product images?**

For web: main images at 1200px wide, thumbnails at 400px wide. Wider images waste bandwidth on 99% of screens. TinyOpt's resize feature lets you batch-scale to any max width during compression.

**04. AVIF or WebP — which one to choose?**

For e-commerce sites with a global audience, stick with WebP as your primary format (96%+ browser support). For hero images, consider providing an AVIF version as progressive enhancement.

**05. How long does it take to batch-process hundreds of images?**

300 images with TinyOpt and multi-key parallel processing typically completes in 3-5 minutes. A single key has a 500-image monthly limit; batch tasks automatically rotate between keys to break the limit.

## Summary

E-commerce image optimization was never a technical problem — it's an efficiency problem. Three core steps:

1. **Batch compress + convert to WebP** — solve file size
2. **Add loading="lazy"** — solve load timing
3. **Set width/height** — solve layout shifts

Get all three right, and your PageSpeed mobile score will likely jump from 40 to 75+.

Download [TinyOpt Compressor](/download/), compress 10 product images to start. If you're happy with 10, the same operation handles 300.
