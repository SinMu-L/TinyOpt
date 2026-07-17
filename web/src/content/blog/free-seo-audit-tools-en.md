---
title: "Free SEO Audit: GSC, Screaming Frog & Lighthouse"
date: 2026-07-21
lang: en
translationKey: free-seo-audit-tools
description: "Ditch Semrush and Ahrefs: run a complete SEO audit with GSC, Screaming Frog, and Lighthouse. Full workflow from site crawl to page diagnostics included."
tags: [SEO audit, free tools, Google Search Console, Screaming Frog, Lighthouse]
---

**Semrush** costs **$139/month**. **Ahrefs** costs **$129/month**. For solo site owners and freelancers, that's serious money — nearly **$1,700/year**, equivalent to hosting costs for a mid-size site.

The good news: three free tools cover **80%** of a professional SEO audit. That $139/month you save can go toward links, ads, or just staying profitable.

The tools: **Google Search Console**, **Screaming Frog SEO Spider**, and **Lighthouse**.

## Tool Comparison

| Tool | Coverage | Free Limit | Key Use |
|------|----------|-----------|---------|
| **Google Search Console** | Index status, search performance, CWV | Unlimited | Macro health check |
| **Screaming Frog** | Full-site crawl, 200+ metrics | 500 URLs free | Micro issue scan |
| **Lighthouse** | Page-level performance/SEO/a11y | Unlimited | Deep page diagnostics |

These three complement each other: GSC shows trends, Screaming Frog finds bugs, Lighthouse diagnoses depth. You need all three.

## 01. GSC — Macro Health Check (30 min)

GSC is the only tool that tells you how Google sees your site. It's your SEO health screening center.

### 1.1 Pages Report

Open the "Pages" report in the left sidebar. Watch two numbers:

- **Valid pages**: Is the count growing or shrinking? Two consecutive months of decline = a problem.
- **Excluded pages**: Focus on "Crawled but not indexed" count.

If the exclusion ratio exceeds **20%**, you have a serious issue. Google crawled your pages but decided they weren't worth indexing — usually a content quality problem.

### 1.2 Performance Report

Set filters: last **3 months**, sort by position. Find keywords at positions **4-10** — the "low-hanging fruit" of SEO.

Keywords at positions 4-10 only need minor tweaks (title optimization, content expansion, internal links) to break into the top 3. Keywords at positions 11-20 are a tier harder. Don't start with them.

Export CSV, add a "Priority" column using these rules:
- Position 4-7 → High priority
- Position 8-10 → Medium priority
- Impressions > 100 and position > 10 → Monitor

### 1.3 Core Web Vitals Report

Switch to the "Mobile" tab. Check two things:

- Number of URLs in "Poor" status
- Break down by issue type: LCP > 2.5s is the most common

Root cause in most cases: **unoptimized images**. A single 2MB PNG can drive LCP past 4 seconds.

👉 [TinyOpt batch-compresses images, solving 60% of LCP issues instantly](/download/)

### 1.4 Sitemaps Section

Is the submitted sitemap status "Success"? Compare "Submitted URLs" vs. "Indexed URLs" ratio.

Ratio < **50%** = crawl budget or content quality issue. Go back to Screaming Frog to analyze which pages aren't getting indexed.

> What GSC can't do: find 404s, detect duplicate titles, identify missing H1s, or surface oversized images. That's what offline tools are for.

## 02. Screaming Frog — Micro Issue Scan (1 hour)

**Screaming Frog SEO Spider** free version handles **500 URLs**. For most personal sites and SMBs, that's enough.

### 2.1 Crawl Setup

Three steps before you start:

1. Enter site URL, click "Start"
2. Configuration → Spider → Check "Crawl Images", "Crawl CSS", "Crawl JavaScript"
3. Configuration → User-Agent → Select "Googlebot (Smartphone)"

Using Googlebot's User-Agent shows you what Google sees — not what users see. Some JS rendering issues only surface from the crawler's perspective.

Crawl time: ~**5-10 minutes** for 500 URLs.

### 2.2 Key Columns to Export

After crawling, export CSV. Focus on these columns:

| Column | What to Check | Severity |
|--------|--------------|----------|
| Status Code | All 404, 301, 302, 500 | High |
| Title 1 | Duplicate titles (sort alphabetically to spot patterns) | High |
| H1-1 | Missing or duplicate H1s | Medium |
| Meta Description 1 | Missing, too short (< 70 chars), too long (> 160 chars) | Medium |
| Canonical Link Element 1 | Missing canonical tag | High |
| Image Size | Sort descending, find anything > **500KB** | High |
| Internal Links | Pages with **0** internal links (orphan pages) | High |
| Click Depth | Depth > **4** (hard for Google to find) | Medium |

### 2.3 Image-Specific Audit

Filter "Images" under the Internal tab. Three checks:

- **File size > 500KB**: These images directly bloat LCP. An 800KB product photo isn't worth it.
- **Dimensions > 2000px wide**: Display width is usually 800px — you're wasting **60%** of bandwidth.
- **No Alt text**: SEO blind spot. Google Image Search uses Alt text to understand image content.

👉 [TinyOpt batch-compresses + converts format, shrinking >500KB images to <150KB](/download/)

### 2.4 Hreflang Audit

If your site is multilingual, check hreflang tags:
- Do any hreflang links point to 404 pages?
- Are any language versions missing?
- Is x-default correctly configured?

Wrong hreflang = Google might serve English pages to French users.

## 03. Lighthouse — Page-Level Diagnostics (30 min)

Lighthouse is built into Chrome DevTools. Completely free, unlimited use.

### 3.1 How to Run

Open Chrome DevTools (F12) → Lighthouse tab → Run Desktop + Mobile separately.

Recommended pages: homepage + 3 core landing pages + 1 blog post. These 5 pages represent your site's typical performance.

### 3.2 Performance Deep Dive

Performance score < **50** = serious issues. Check two key areas:

**LCP element**: What's the largest visible element? If it's an `<img>`, verify three things:
- Is it compressed? (Original > 500KB = fail)
- Is the format WebP/AVIF or JPEG/PNG?
- Does it have `loading="lazy"` and explicit dimensions?

**Opportunities** → "Serve images in next-gen formats": This is Lighthouse's #1 image-related suggestion. Switch to WebP/AVIF to resolve it instantly.

👉 [TinyOpt converts to WebP/AVIF in one click, eliminating Lighthouse image warnings](/download/)

### 3.3 SEO Checks

Lighthouse's SEO audit covers 15+ basic checks:

- `Document has a <title> element`: Basic but often missed (especially in SPAs)
- `Links have descriptive text`: "Click here" and "Learn more" are SEO dead weight
- `robots.txt is valid`: One wrong character can block your entire site
- Structured data validation: Lighthouse flags Schema syntax errors

Pass every single one. SEO score < **90** means fix them item by item.

## Audit Report Template

After each audit, organize findings into three pages:

**Page 1: Executive Summary**
- Top **3 most critical issues**
- Estimated fix time for each
- Expected SEO impact (ranking / indexing / speed)

**Page 2: Priority List**

| Priority | Issue | Pages Affected | Fix Difficulty | Est. Time |
|----------|-------|---------------|---------------|-----------|
| P0 | Fix all 404s | 12 | Low | 30 min |
| P1 | Compress images >500KB | 34 | Low | 20 min |
| P2 | Add missing H1s | 8 | Low | 15 min |
| P3 | Fix duplicate titles | 15 | Medium | 1 hour |

Sort by impact × fix difficulty. High impact + easy fix = do first.

**Page 3: Progress Tracker**

| Week | Planned Fixes | Completed | Notes |
|------|--------------|-----------|-------|
| Week 1 | 404s + image compression | ✓ | One-time fixes |
| Week 2 | Titles + H1s | ✓ | Page by page |
| Week 3 | Canonical + Schema | Pending | Needs dev help |

## Pattern Summary

Paid SEO tools add **convenience**, not **capability**. The three free tools in this guide give you the same diagnostic power.

Paid tools only add value in three areas:
1. **Scale**: Full-site audits beyond 500 URLs
2. **Trend tracking**: Automated period-over-period comparisons
3. **Competitor analysis**: Insight into competitors' keyword strategies

Recommended path: start with free tools. Only upgrade when your site exceeds 500 pages. Until then, that $139/month is better spent on content creation or link building.

## FAQ

**Q1: Can Screaming Frog crawl large sites?**

Free version caps at **500 URLs**. Beyond that, you need a license (**￡199/year**, ~**$260**). For most personal sites and SMBs, 500 URLs is sufficient.

**Q2: Are Lighthouse scores the same as real-user experience?**

Not exactly. Lighthouse is **lab data** (simulated environment); GSC Core Web Vitals are **field data** (real users). Discrepancies can occur. Trust GSC data as the source of truth, use Lighthouse as an issue discovery tool.

**Q3: Do I need Screaming Frog if I already use GSC?**

Yes. GSC won't tell you which pages have duplicate titles, which images exceed 500KB, or which pages are orphans. GSC is macro, Screaming Frog is micro — you need both.

**Q4: What if I find 50 image issues — how do I batch-fix them?**

Manual fixes are impractical. Use **TinyOpt** for batch import — compress, convert format, and resize all at once. 50 images fixed in minutes.

👉 [TinyOpt batch processing — one click solves all your image optimization issues](/download/)

**Q5: How often should I run this audit?**

**Monthly**. **2 hours** each time catches most problems. Run an extra one after major content pushes or site redesigns.

## Summary

2 hours. 3 free tools. 80% coverage of a professional SEO audit.

This is the best 2 hours you'll spend on SEO each month. Better than chasing trends, better than fretting over algorithm updates, better than any other SEO investment — because it tells you exactly what's wrong, how to fix it, and what will happen when you do.

Remember the workflow:
- **GSC** shows you how Google sees your site
- **Screaming Frog** reveals the problems you don't know about
- **Lighthouse** diagnoses each page's specific symptoms

Open GSC this afternoon. Follow Step 1 from this guide. In 30 minutes, you'll spot an issue you hadn't noticed before.

👉 [Download TinyOpt — fix every image issue Lighthouse flagged, all at once](/download/)

---

[^1]: Google Search Central, "Google Search Console Help", https://support.google.com/webmasters/answer/9128668

[^2]: Screaming Frog, "SEO Spider Tool", https://www.screamingfrog.co.uk/seo-spider/

[^3]: Google Chrome Developers, "Lighthouse", https://developer.chrome.com/docs/lighthouse/

[^4]: Google Search Central, "Understand Core Web Vitals and Google Search Results", https://developers.google.com/search/docs/appearance/core-web-vitals
