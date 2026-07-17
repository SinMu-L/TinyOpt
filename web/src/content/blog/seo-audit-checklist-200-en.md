---
title: "SEO Audit Checklist: 200 Points in 10 Categories"
date: 2026-07-19
lang: en
translationKey: seo-audit-checklist-200
description: A complete SEO self-audit checklist with 200 checkpoints in 10 categories, covering crawling, indexing, on-page, images, structured data, and backlinks.
tags: [SEO audit, SEO checklist, independent site, technical SEO, on-page SEO]
---

Last month I asked 30 independent site owners in an export community: "When was your last full-site SEO audit?" Twenty-seven said "never" or "once at launch."

SEO isn't a one-time thing. Google updates its algorithm over 5,000 times per year[^1] — ranking #1 today doesn't mean you'll hold that spot next month. A site that has never been audited is leaking rankings without knowing it.

👉 [Download TinyOpt and eliminate 20% of SEO penalties through image compression first](/download/)

## 01. The 10 Categories and 200 Checkpoints

Categories are ordered by impact weight — **the earlier the category, the more fatal its problems**.

| # | Category | Items | Auto-checkable | Primary Tool |
|---|----------|-------|----------------|-------------|
| 1 | Crawl & Index | 25 | 20 | Screaming Frog, GSC |
| 2 | Technical Infrastructure | 25 | 18 | Screaming Frog, Lighthouse |
| 3 | On-Page Optimization | 25 | 15 | Screaming Frog |
| 4 | Content Quality | 25 | 5 (manual) | Manual review |
| 5 | Image SEO | 20 | 10 | TinyOpt, Screaming Frog |
| 6 | Structured Data | 15 | 10 | Schema Validator, GSC |
| 7 | Internal Links | 20 | 15 | Screaming Frog |
| 8 | Backlink Health | 15 | 10 (via GSC) | GSC, Ahrefs |
| 9 | Mobile Adaptation | 15 | 10 | Lighthouse, GSC |
| 10 | Analytics & Tools | 15 | 8 | GSC, GA4 |

Below are the most overlooked, highest-consequence items.

## 02. Critical #01: robots.txt Blocking the Entire Site

This is a real case from our previous technical SEO article[^2]: a site went live for two months, and Google indexed exactly zero pages. After checking every possible cause, we found one line in the root directory:

```
Disallow: /
```

The hosting provider's default robots.txt was never updated. A one-character error blocked the entire site for 60 days.

**How to check**: Open `https://yourdomain.com/robots.txt` and confirm the following aren't present:

| Dangerous Directive | Consequence |
|--------------------|-------------|
| `Disallow: /` | Entire site blocked from crawling |
| `Disallow: /wp-admin/` with default template | Common leftover, not fatal but a red flag |
| `Sitemap: http://example.com/sitemap.xml` | Sitemap pointing to a demo domain |

If your robots.txt contains `Disallow: /`, Google has never seen your site.

## 03. Critical #02: Mixed Content — HTTPS Page Loading HTTP Resources

HTTPS certificate installed ≠ site is fully secure. If a single image or script on any page loads over `http://`, the browser shows a "Not Secure" warning.

Google has treated HTTPS as a ranking signal since 2014[^3]. As of 2024, Chrome blocks all HTTP resources by default. Mixed content equals an automatic penalty.

| Resource Type | Risk |
|--------------|------|
| Images (`<img>`) | Browser flags the entire page as "Not Secure" |
| JS/CSS | Browser blocks loading outright — page breaks |
| Embedded video/fonts | Content won't render |

**One-click detection**: Screaming Frog → Security → Mixed Content report. Results in seconds.

## 04. Critical #03: Title Tags Duplicated Across Pages

Last year I audited a B2B site with $20M annual revenue. Four hundred pages. Seven Title templates. Fifty product pages shared one identical Title: "Products — Company Name."

Google can't differentiate those pages. It randomly picks a few to rank and ignores the rest.

**How to check**: Screaming Frog → Page Titles → Duplicate column. A healthy site should be under 5%.

**Fix principles**:

| Page Type | Title Format |
|-----------|-------------|
| Homepage | Core keyword + Brand name |
| Product page | Product name + 1 key feature + "\| Brand" |
| Category page | Category term + "Best \| Top \| Wholesale" + "\| Brand" |
| Blog post | Post title (with target keyword) + "\| Brand" |

Every page unique. No exceptions. This is the first law of on-page SEO.

## 05. Critical #04: Core Pages Missing Canonical Tags

Canonical tags tell Google: "This is the official version of this page." Without them, Google might choose the wrong version to index — or think you're publishing duplicate content.

Google's official guidance: **every page should have a self-referencing canonical tag**[^4].

```html
<link rel="canonical" href="https://yoursite.com/current-page-url/" />
```

Common mistakes:

| Error | Consequence |
|-------|------------|
| All pages missing canonicals | Google decides which version to index — may choose wrong |
| Canonical pointing to homepage `href="/"` | All pages treated as duplicates of homepage |
| Canonical pointing to a 404 | You're telling Google your page is dead |
| Paginated pages canonical → page 1 | Pages 2-N will never be indexed |

Screaming Frog → Directives → Canonicals. Check the missing and error ratios.

## 06. Critical #05: Image Sitemap Never Submitted

Many sites submit a page sitemap but never an image sitemap. Consequence: Google never actively crawls your images. Image search traffic: zero.

For e-commerce and image-heavy sites, image search can drive 10-25% of organic traffic[^5].

| Checkpoint | How to Verify |
|-----------|---------------|
| Image sitemap generated? | WordPress: Rank Math / Yoast auto-generate. Others: requires plugin or manual creation |
| Submitted to GSC? | GSC → Sitemaps → check image sitemap submission status |
| All image URLs HTTPS and accessible? | Spot-check 5-10 image URLs from the sitemap |

👉 [TinyOpt compresses images in bulk without changing filenames or paths — your existing image sitemap stays valid](/download/)

## 07. High Risk #06: Broken Internal Links (404) Wasting Crawl Budget

Google allocates a limited crawl budget to each site daily. If Google spends 30% of that quota hitting 404 pages, 30% of your valid pages don't get crawled in time.

**How to check**: Screaming Frog → Response Codes → Client Error (4XX).

| Source of Broken Links | Fix |
|-----------------------|-----|
| Deleted product page, still linked from category | 301 redirect to related category or alternative |
| Old URL structure changed, no redirects | Batch 301 to new URLs |
| External links in articles now dead | Update link or remove |

Ideally, internal 404 count should be zero. If a page must be removed, give it a 301 destination.

## 08. High Risk #07: Thin Content Pages (<300 Words)

Google's Helpful Content System specifically targets "low-quality, non-unique" pages[^6]. If your site hosts many sub-300-word pages with no unique value, they drag down the entire site's quality score.

**How to check**: Export all page URLs. Manually review word counts. Focus on:

- Product pages (many sites have images only, no text)
- Tag/archive pages (identical across the site)
- Author archive pages (minimal content)

Fix strategy:

| Situation | Action |
|-----------|--------|
| Page has potential but lacks depth | Expand to 500+ words with unique information |
| Page has zero value (e.g., tag archives) | Add `noindex` tag |
| Page duplicates another page's content | Merge content, 301 old URL to new |

## 09. High Risk #08: Mobile Usability Issues

Google has used mobile-first indexing for all sites since 2023[^7]. Your desktop version being perfect means nothing if mobile fails.

**GSC → Mobile Usability report**. Three most common issues:

| Issue | Trigger | Quickest Fix |
|-------|---------|-------------|
| Text too small to read | Font size <12px | Set `font-size: 16px` as baseline |
| Clickable elements too close | Button spacing <8mm | Increase padding/margin, touch targets ≥48px |
| Content wider than screen | Non-responsive images or tables | Add `max-width: 100%` |

Every mobile usability error is telling Google: "I don't care about mobile users."

## 10. 30-Minute Quick Audit: 20 Must-Check Items

If you only have 30 minutes, follow this sequence:

**GSC (5 minutes, 5 items)**:

1. Pages report → check "Not indexed" count and reasons
2. Sitemaps → confirm submission status is "Success"
3. Core Web Vitals → check mobile and desktop LCP/INP/CLS groupings
4. Mobile Usability → confirm zero errors
5. Security Issues → confirm no issues

**Screaming Frog quick scan (10 minutes, 5 items)**:

6. Response Codes → check 404 and 500 error counts
7. Page Titles → duplicate Title percentage
8. Meta Description → missing or duplicate percentage
9. Canonicals → missing percentage
10. H1 → pages with missing or duplicate H1

**Manual check (10 minutes, 5 items)**:

11. `yoursite.com/robots.txt` → confirm no `Disallow: /`
12. Type your domain in browser → confirm HTTPS auto-redirect, no security warning
13. Open homepage on phone → check load speed and horizontal scrolling
14. Spot-check 3 core product pages → confirm each has unique Title / H1 / Description
15. Google search `site:yoursite.com` → compare indexed count to your total page count

**Lighthouse (5 minutes, 5 items)**:

16. Performance score ≥70 (mobile)
17. Accessibility score ≥85
18. Best Practices score ≥90
19. SEO score ≥90
20. Check Opportunities → what's the single biggest improvement?

## 11. Automation Approach

With the right tools, you can cover ~160 items automatically. The remaining ~40 require human judgment.

| Tool | Items Covered | Cost | Core Capability |
|------|-------------|------|----------------|
| Screaming Frog | ~120 items | Free (500 URLs) / Paid | Full site crawl |
| Google Search Console | ~40 items | Free | Index status, performance data |
| Lighthouse | ~30 items | Free | Performance and PWA audit |
| Schema Validator | ~15 items | Free | Structured data validation |
| TinyOpt | ~10 image/CSS items | Free | Bulk image compression |

Must involve human review: content quality assessment, E-E-A-T signal evaluation, keyword strategy review, backlink quality analysis.

## 12. The Pattern: Audit for Impact, Not Volume

After a full-site audit, you might find 50-200 issues. The number doesn't matter. The priority does.

The 80/20 rule applies: **20% of issues cause 80% of ranking loss**.

Priority logic:

```
If Google can't find your pages → clear all crawl and index issues first
If pages are found but not clicked → optimize Title and Description
If clicked but users bounce → check content quality and page speed
If content is good but won't rank → check E-E-A-T signals and backlinks
```

Start from category 1. If the foundation is broken, nothing else matters.

## 13. FAQ

**Q1: How often should I do an SEO audit?**

Full deep audit: quarterly. Light checkup (GSC + spot-check core pages): monthly. Immediately after any technical change (domain migration, redesign, theme switch).

**Q2: Can I audit without a technical background?**

Yes. At minimum, complete the "Manual check 5 items" and "GSC 5 items" from Section 10 — no technical background needed. Technical sections can be handed off to a developer.

**Q3: I found 100 issues. Which do I fix first?**

Fix "blocker-class" issues first: robots.txt errors, site-wide noindex, expired HTTPS certificate, Sitemap submission failure. These make every other fix irrelevant.

**Q4: Do I need paid tools for an audit?**

No. Screaming Frog's free version scans 500 URLs — enough for small sites (<100 pages). GSC and Lighthouse are entirely free. Paid tools improve efficiency but don't change your ability to find core problems.

**Q5: How do I convince a client or boss to invest in SEO fixes?**

Don't use SEO jargon. Use their language: **"When people search for [your core product term], Google isn't showing your site. Your competitor occupies that spot. Fix this, and expect to see traffic changes within X weeks."**

## 14. Summary

Start with Category 1 — Crawl & Index. A page Google can't see doesn't exist.

You don't need to check all 200 items in one sitting. Round one: clear the 8 critical items. Then rotate through categories monthly, covering all 10 within a quarter.

An SEO audit isn't a test with a passing score. It's a map — showing you where rankings are leaking and which hole to plug first.

👉 [Download TinyOpt and eliminate 20% of SEO penalties through image compression first](/download/)

---

[^1]: Moz, "Google Algorithm Update History", 2025, https://moz.com/google-algorithm-change

[^2]: Google Search Central, "Robots.txt Introduction", https://developers.google.com/search/docs/crawling-indexing/robots/intro

[^3]: Google Security Blog, "HTTPS as a Ranking Signal", 2014, https://developers.google.com/search/blog/2014/08/https-as-ranking-signal

[^4]: Google Search Central, "Canonical URLs", https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

[^5]: Google Search Central, "Image Sitemaps", https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps

[^6]: Google Search Central, "Creating Helpful, Reliable, People-First Content", https://developers.google.com/search/docs/fundamentals/creating-helpful-content

[^7]: Google Search Central, "Mobile-First Indexing", https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-first-indexing
