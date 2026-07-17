---
title: "Technical SEO: Crawl, Index & Core Web Vitals"
date: 2026-06-22
lang: en
translationKey: seo-technical-crawl-index-cwv
description: Master technical SEO from crawling and indexing to Core Web Vitals. Covers Sitemap, robots.txt, canonical tags, and structured data with configuration tips.
tags: [Technical SEO, Core Web Vitals, Sitemap, Structured Data, Crawl & Index]
---

In 2018 I took over a puzzling project: "Our site has been live for two months, and Google hasn't indexed a single page." Everything checked out — WordPress wasn't set to discourage indexing, the server returned 200 status codes, content was complete.

After an hour, I found the culprit in the root directory. The `robots.txt` contained one line:

```
Disallow: /
```

The hosting provider had pre-loaded this default file, and no one had modified it after installing WordPress. One character, sixty days of zero indexing.

Technical SEO isn't as glamorous as content marketing, but when it breaks, it breaks catastrophically — **if search engines can't access your site, no amount of great content matters**.

## 01. Crawl and Index — How Google Discovers Your Pages

Google's process has two stages:

**Crawl** — Googlebot follows links from page to page, downloading content.

**Index** — Google analyzes the downloaded content and stores it in its search database. When users search, Google matches queries against this index.

A widely cited study found that the average crawl depth (clicks from the homepage) directly correlates with how quickly and how often Google discovers a page [^1].

### Crawl Budget

Google allocates a limited daily crawl quota per site, known as the Crawl Budget [^2]. If you have 10,000 pages but only 200 daily crawl requests, Google will prioritize pages it deems most important.

### Factors Affecting Crawl Budget

| Factor | Positive Impact | Negative Impact |
|--------|----------------|-----------------|
| Site authority | High-authority sites get more crawl requests | New sites crawl less frequently |
| Update frequency | Frequently updated pages are crawled more | Static pages see reduced crawl frequency |
| Server response | Fast servers encourage more crawling | 500 errors reduce crawl rate |
| Broken link ratio | — | Many 404s waste crawl budget |

### How to Check Your Index Status

In Google Search Console, open the "Pages" report. Focus on:

- **Valid pages** — successfully indexed count
- **Excluded pages** — pages not indexed, with reasons (common: Page with redirect, Crawled but not indexed, Not found 404)

**Warning**: A page being publicly accessible does NOT mean it's indexed. Always verify in Search Console.

## 02. Sitemap.xml — Your Indexing Roadmap

A Sitemap is an XML file listing all URLs you want indexed, along with their last modification dates. It's not a ranking factor, but it significantly accelerates new page discovery [^3].

### Configuration Essentials

- Use Rank Math or Yoast SEO to auto-generate (WordPress)
- Include only index-worthy URLs (exclude tag pages, author archives, search results)
- Submit via Google Search Console's Sitemaps section
- Keep the Sitemap updated as content changes

### Common Errors

| Error | Consequence |
|-------|-------------|
| Sitemap contains 404 URLs | Google loses trust in your Sitemap |
| Sitemap includes noindex pages | Conflicting instructions; Google follows noindex |
| Includes pagination/filter URLs | Massive duplicate content generation |
| Sitemap submitted once and never updated | New pages go undiscovered |

## 03. Core Web Vitals — Google's UX Scorecard

Core Web Vitals are three metrics measuring real-world user experience. They became a ranking signal with the June 2021 Page Experience update [^4].

In March 2024, Google replaced FID (First Input Delay) with INP (Interaction to Next Paint), providing a more comprehensive measure of interactivity [^5].

### Metrics and Thresholds

| Metric | What It Measures | Good | Poor | Source |
|--------|-----------------|------|------|--------|
| LCP (Largest Contentful Paint) | Loading speed | ≤2.5s | >4.0s | 75th percentile |
| INP (Interaction to Next Paint) | Responsiveness | ≤200ms | >500ms | 75th percentile |
| CLS (Cumulative Layout Shift) | Visual stability | ≤0.1 | >0.25 | 75th percentile |

### How to Diagnose and Optimize

**Step 1: Check the Core Web Vitals Report in Search Console**

This groups URLs by mobile and desktop performance using **field data** (real Chrome users over a 28-day window) — not Lighthouse lab data. These are fundamentally different: lab data simulates an environment, field data measures actual user experiences.

**Step 2: Prioritize Fixes**

Recommended order: LPC → CLS → INP. Rationale:

- LCP is usually caused by unoptimized images — the most common issue
- CLS is cheap to fix — always set explicit dimensions for images and ad slots
- INP typically involves JavaScript optimization — technically harder

**Step 3: Targeted Solutions**

| Metric | Most Common Cause | Quickest Fix |
|--------|------------------|-------------|
| Poor LCP | Uncompressed large images | Compress + WebP + appropriate dimensions |
| High CLS | Images without dimensions | Set explicit `width` and `height` on all images |
| Slow INP | Third-party scripts blocking the main thread | Lazy-load non-critical JS, remove unnecessary scripts |

Regarding ranking weight, Google states that Core Web Vitals are one signal among many. Content relevance far outweighs perfect scores. Poor content with great Core Web Vitals won't rank; authoritative content with slightly subpar Vitals still can [^6].

## 04. Structured Data (Schema) — Stand Out in Search Results

Structured data tells search engines what type of content your page contains using a standard format. It doesn't affect ranking but enables rich results (star ratings, prices, expandable FAQ) that significantly boost CTR [^7].

### Three Most Useful Schemas for Independent Sites

**Product Schema**
```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "630A Molded Case Circuit Breaker",
  "description": "3-pole 630A MCCB with thermal-magnetic protection",
  "brand": "Brand Name",
  "offers": {
    "@type": "Offer",
    "priceCurrency": "USD",
    "price": "189.00"
  }
}
```

**FAQ Schema** — B2B sites can use this on FAQ pages or product-page FAQ sections to enable expandable answers directly in search results.

**BreadcrumbList Schema** — Helps Google understand page hierarchy and displays breadcrumb paths in SERPs, improving CTR.

### Testing Tools

Google's Rich Results Test (https://search.google.com/test/rich-results) and Schema Markup Validator are free. Always validate before publishing.

## 05. Hreflang for Multi-Language Sites

If your site has multiple language versions (e.g., English, Chinese, Spanish), `hreflang` tags tell Google which pages correspond to which language — preventing duplicate content penalties [^8].

### Common Mistakes

- Mixing languages on the same page — each language version needs its own URL
- Missing hreflang — Google may index only one version
- Pointing hreflang to wrong or non-existent pages — verify after configuration

### Correct Setup

For three versions: `/product/mccb` (en), `/zh/product/mccb` (zh), `/es/product/mccb` (es):

```html
<link rel="alternate" hreflang="en" href="https://example.com/product/mccb" />
<link rel="alternate" hreflang="zh" href="https://example.com/zh/product/mccb" />
<link rel="alternate" hreflang="es" href="https://example.com/es/product/mccb" />
<link rel="alternate" hreflang="x-default" href="https://example.com/product/mccb" />
```

Both Rank Math and Yoast SEO support hreflang configuration directly in their settings.

## 06. Monthly Technical SEO Checklist

Spend 30 minutes on the first of each month:

1. **Search Console → Pages report** — verify no unexpected drop in indexed page count
2. **Search Console → Sitemaps** — confirm status is "Success"
3. **Sitebulb / Screaming Frog full scan** — check for 404s, 301s, and redirect chain length
4. **Pagespeed Insights on 3-5 core pages** — confirm Core Web Vitals haven't degraded
5. **Check HTTPS certificate expiry** — schedule renewal if under 30 days

Technical SEO lacks the dopamine hit of "publish now," but it underlies everything else. Without it, search engines simply can't see your work.

---

[^1]: Brian Dean, "We Analyzed 11.8 Million Google Search Results", Backlinko, 2024

[^2]: Google Search Central, "Crawl Budget Management", https://developers.google.com/search/docs/crawling-indexing/large-site-managing-crawl-budget

[^3]: Google Search Central, "Sitemaps", https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview

[^4]: Google Search Central, "Understanding Core Web Vitals and Google Search Results", https://developers.google.com/search/docs/appearance/core-web-vitals

[^5]: web.dev, "Web Vitals", https://web.dev/articles/vitals

[^6]: Barry Schwartz, "Google Clarifies Page Experience & Core Web Vitals Document", Search Engine Roundtable, 2024

[^7]: Google Search Central, "Understand How Structured Data Works", https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data

[^8]: Google Search Central, "Tell Google About Different Language Versions of Your Pages", https://developers.google.com/search/docs/specialty/international/localized-versions
