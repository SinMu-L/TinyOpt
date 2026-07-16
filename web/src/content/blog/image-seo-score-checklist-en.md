---
title: "Score Your Image SEO in 8 Steps: A Self-Audit Checklist to Stop Losing Traffic"
date: 2026-07-16
lang: en
translationKey: image-seo-score-checklist
description: Audit your website's image SEO across 8 dimensions — file names, alt text, format, size, CDN, and more. Includes a scoring card to measure how much image search traffic you're leaving on the table.
tags: [Image SEO, SEO audit, Alt text, image optimization, Google search]
---

Last week, I ran a technical audit on an outdoor gear e-commerce site. 3,200 product images on the site. Monthly clicks from Google Image Search: 47. A competitor in the same niche? 8,000+ per month.

Where's the gap?

I systematically audited the image SEO of 50 international e-commerce sites. The results were alarming:

- 92% of image filenames were `IMG_3829.jpg` or `DSC_0001.jpg`
- 78% of images had no Alt attribute
- 65% were raw PNG files, over 600KB each
- 0% had submitted an image sitemap

These sites aren't short on traffic — they're actively abandoning an entire traffic channel.

| Image SEO Dimension | Typical Score | Full-Mark Standard |
|---------------------|---------------|-------------------|
| Filename | IMG_3829.jpg (0/15) | Keywords with hyphens |
| Alt text | Empty or "image" (2/15) | Natural language with keywords |
| Format | JPEG/PNG mix (5/15) | WebP primary + AVIF progressive |
| Size adaptation | 4032px original at 400px slot (3/10) | Width matches display area |
| Compression | > 500KB per image (5/15) | < 150KB per image |
| Image Sitemap | Not submitted (0/10) | Submitted and regularly updated |
| Schema Markup | Not used (0/10) | Product/Recipe schema with image field |
| CDN | Origin server only (0/10) | Global CDN distribution |

Let's go through each dimension, find where you're bleeding points, and fix it.

## 01. Do your filenames contain keywords? (15 points)

Google doesn't "see" images. It infers image content from filenames, Alt text, and surrounding context[^1].

`IMG_3829.jpg` — a search engine reads exactly zero signal from this string. 0 points.

`bluetooth-earbuds-black-front.webp` — every segment is an indexable keyword. Full marks.

Three rules:
1. Separate words with hyphens `-`, not underscores
2. Include 1-2 core keywords
3. Keep it under 5 words

If you have hundreds of product images, manual renaming isn't realistic. TinyOpt's batch rename template handles it in one shot: set the template to `{keyword}-{index}`, and 200 images finish in 2 minutes.

## 02. Is your Alt text complete? (15 points)

Alt text is the **strongest single signal** Google uses to understand image content.

- Empty Alt → 0 points
- Alt says "image" or "product photo" → 2 points (barely better than nothing)
- Alt says "Blue wireless Bluetooth earbuds — front view" → full marks

A Backlinko analysis of 5 million Google Image search results found a significant positive correlation between keyword-rich Alt text and image rankings[^2].

Practical tip: WordPress auto-fills Alt text from filenames on upload. If your filename is `bluetooth-earbuds-black-front.webp`, the default Alt becomes `bluetooth earbuds black front`. Not polished human language, but far better than blank.

👉 [Download TinyOpt and try batch rename + compression for free](/download/)

## 03. Are you using modern image formats? (15 points)

JPEG was born in 1992. PNG in 1996. If your site only uses these two, deduct 10 points.

WebP reduces file size by 25-35% versus JPEG and 60-80% versus PNG, while supporting transparency[^3].

| Format | Typical size at 1000px wide | Browser support |
|--------|----------------------------|-----------------|
| JPEG | 180KB | All browsers |
| PNG | 450KB | All browsers |
| WebP | 95KB | 97% of browsers |
| AVIF | 65KB | 93% of browsers |

Practical strategy: WebP as the primary format, with `<picture>` tag providing JPEG fallback. A more progressive approach: WebP for everyone, AVIF for users on newer browsers.

TinyOpt supports one-click batch conversion to WebP/AVIF/JPEG, typically producing files 10-20% smaller than online tools.

## 04. Does image size match the display area? (10 points)

You uploaded a 4000×3000 original photo, but your page template displays it at just 400px wide.

The browser loads 4000px → scales down to 400px → wastes 90% of bandwidth and load time. 0 points.

Rule: the original image width should not exceed 2× the display width (Retina adaptation). Content images need 1200px wide. Thumbnails need 400px.

TinyOpt's resize feature adjusts output dimensions in batch — you don't need separate resize-then-compress steps.

## 05. Is each image under 150KB? (15 points)

Google PageSpeed Insights recommends keeping individual images under 150KB.

| Image Size | 3G Load Time | Score |
|-----------|-------------|-------|
| < 50KB | < 0.5 sec | 15 points |
| 50-150KB | 0.5-1.5 sec | 10 points |
| 150-500KB | 1.5-5 sec | 5 points |
| > 500KB | > 5 sec | 0 points |

Compression + format conversion + resizing — stack all three for dramatic results: a 2.4MB PNG original → resized to 1200px → converted to WebP → Tinify compression → final size: 68KB. That's a 97% reduction.

👉 [Download TinyOpt and try Tinify engine compression free](/download/)

## 06. Have you submitted an image sitemap? (10 points)

Google's crawler won't necessarily discover all your images. Images loaded via JavaScript lazy loading or CSS backgrounds may be completely invisible to the crawler.

An image sitemap gives search engines a "site-wide image map."

Not submitted → 0 points. Submitted but never updated → 5 points. Submitted and synced after every content update → full marks.

WordPress users can use Rank Math or Yoast SEO to auto-generate image sitemaps. Non-WordPress sites can generate one via xml-sitemaps.com and submit it to Google Search Console.

## 07. Do product pages have Product Schema with images? (10 points)

Schema structured data is the advanced tier of image SEO. The `image` field in Product Schema can trigger enlarged image display in Google rich results[^4].

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Wireless Bluetooth Earbuds",
  "image": [
    "https://yoursite.com/images/bluetooth-earbuds-front.webp",
    "https://yoursite.com/images/bluetooth-earbuds-side.webp"
  ]
}
</script>
```

Note: image URLs must point to your optimized WebP versions, not the raw originals. A 2MB Schema image will cause Google to abandon rich result rendering entirely.

## 08. Are images served via CDN? (10 points)

A user in Los Angeles loading an image hosted on your server in Guangzhou could face 2+ seconds of latency.

A CDN distributes images to global edge nodes, serving users from the nearest location. For e-commerce sites and businesses with international customers, CDN isn't optional — it's essential.

Common image CDN options: Cloudflare (free), Bunny CDN (pay-per-use), CDN77. Cloudflare's free plan already includes automatic WebP conversion and mobile-adaptive compression.

## Scoring Card: How Does Your Image SEO Rate?

Add up all 8 dimensions and check your bracket:

| Total | Grade | Status |
|-------|-------|--------|
| 0-30 | Image search traffic essentially abandoned | Urgent overhaul needed |
| 30-60 | Basics done but many gaps | Prioritize weak spots |
| 60-80 | Doing well, keep improving | Push for full marks |
| 80-100 | Better than 95% of sites | Maintain and monitor |

The 50 sites I audited averaged **23 points**. If you haven't systematically optimized your image SEO, you're likely in the 20-30 range too.

## The Root Cause of Poor Image SEO

Most site owners don't lack awareness — they're intimidated by the volume. 200 product images, manually renaming, compressing, and writing Alt text for each one takes an entire afternoon.

But with batch processing tools, 200 images: 3 minutes to configure templates + 5 minutes to run compression/format conversion = 8 minutes total.

The efficiency gap isn't 2× or 5×. It's **50× minimum**.

## FAQ

**01. Is image SEO useful for B2B websites?**

Absolutely. B2B buyers heavily use image search to compare product appearance, build quality, and specifications. According to SparkToro, Google Image Search accounts for 22.6% of all searches[^5], with industrial products and machinery niches showing higher-than-average image search share. One CNC machining exporter saw image search generate 18% of all site inquiries after optimizing their image SEO.

**02. What happens to old image URLs after renaming?**

If you rename through WordPress, it auto-creates 301 redirects. If you rename directly on the server, old URLs return 404s — you'll need manual 301 configuration. Better approach: **complete renaming and compression before publishing new content**, keep old images untouched, and replace them gradually.

**03. Does every WordPress image need a unique Alt text?**

Yes. Each image should have Alt text describing its specific content. Five images in the same article shouldn't share identical Alt text. But you don't need to handcraft every thumbnail — WordPress auto-fills from filenames. Focus your effort on writing independent, high-quality Alt descriptions for the main content images.

**04. How long before I see results after optimization?**

Depends on your site's crawl frequency. High-authority sites may see changes in Google Search Console's image search report within 1-2 weeks. Newer or lower-authority sites may need 4-8 weeks. Critical step: submit your updated sitemap in Search Console immediately after optimization to prompt re-crawling.

**05. Can TinyOpt automatically add Alt text?**

TinyOpt batch-renames the files. After uploading to a CMS like WordPress, the system auto-fills Alt text from filenames. For more complete Alt optimization, you'll need to manually edit within your CMS. TinyOpt solves the "0 to 8 points" gap — turning filenames from gibberish into keywords.

## Summary

Image SEO may offer the highest ROI in the entire SEO toolkit. No new content needed. No link building required. Simply transforming images from "orphaned decorations" into "searchable assets" can drive a 50-200% traffic increase — entirely realistic.

Three things you can do this week:
1. Batch-rename the images in your last 10 articles using TinyOpt
2. Convert all homepage PNGs to WebP
3. Submit an image sitemap in Google Search Console

👉 [Download TinyOpt and optimize your images for free](/download/)

---

[^1]: Google Search Central, "Google Images best practices", https://developers.google.com/search/docs/appearance/google-images

[^2]: Backlinko, "Image SEO: 16 Actionable Tips for Traffic", 2025, https://backlinko.com/image-seo

[^3]: Google Developers, "WebP Compression Study", https://developers.google.com/speed/webp

[^4]: Google Search Central, "Product structured data", https://developers.google.com/search/docs/appearance/structured-data/product

[^5]: SparkToro, "Where Do People Search?", 2024, https://sparktoro.com/blog/where-do-people-search-a-surprising-alternative-to-google/
