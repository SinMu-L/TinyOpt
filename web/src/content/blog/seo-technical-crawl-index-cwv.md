---
title: 技术 SEO 实战：从 Google 爬虫抓取到 Core Web Vitals，让你的网站被正确收录
date: 2026-06-22
lang: zh
translationKey: seo-technical-crawl-index-cwv
description: 技术SEO决定了搜索引擎能否发现和理解你的内容。本文从抓取与索引、Sitemap、robots.txt、Canonical、Core Web Vitals到结构化数据，逐个拆解配置方法和常见陷阱。
tags: [技术SEO, Core Web Vitals, Sitemap, 结构化数据, 爬虫抓取]
---

2018 年我接手了一个奇怪的项目：客户说 "网站上线两个月了，Google 一个页面都没收录"。检查了所有配置——WordPress 后台没有勾选 "建议搜索引擎不收录"，服务器返回 200 状态码，页面内容完整。

花了一个小时，最终在网站根目录发现了一个 robots.txt 文件，内容只有一行：

```
Disallow: /
```

这是该站点托管商预置的默认文件，安装 WordPress 后忘记修改。一个字符的错误，导致全站被搜索引擎屏蔽了两个月。

技术 SEO 不像内容 SEO 那样需要持续输出，但它出的问题往往是致命的——**搜索引擎根本找不到你的网站，再好的内容也没有意义**。

## 01. 抓取（Crawl）与索引（Index）——理解 Google 的工作流程

Google 发现和收录页面分为两个阶段：

**抓取（Crawl）**：Googlebot（谷歌爬虫）沿着链接从一个页面跳到另一个页面，下载页面内容。

**索引（Index）**：Google 分析抓取到的页面内容，存入搜索数据库。用户搜索时，Google 从索引库中匹配相关页面。

一篇被广泛引用的研究指出，平均每个页面的抓取深度（从首页出发需要点击的次数）决定了 Google 能否以及多久访问到这个页面[^1]。

### 关键概念：Crawl Budget

Google 对每个网站每天分配的爬取次数是有限的，这个额度叫 Crawl Budget（抓取预算）[^2]。如果你的网站有 10,000 个页面，每天只有 200 次抓取机会，Google 会优先抓取它认为重要的页面。

### 影响 Crawl Budget 的因素

| 因素 | 正面影响 | 负面影响 |
|------|---------|---------|
| 网站权威性 | 高权威网站获得更多抓取 | 新站抓取频率较低 |
| 页面更新频率 | 频繁更新的页面被更频繁抓取 | 长期不更新的页面降低抓取频率 |
| 服务器响应速度 | 快速响应的服务器抓取更多 | 500 错误会减少抓取 |
| 死链比例 | - | 大量 404 页面浪费抓取预算 |

### 如何查看你的索引状态

在 Google Search Console 中打开 "Pages" 报告，核心关注两个指标：

- **Valid pages**：已被正常索引的页面数量
- **Excluded pages**：未被索引的页面及原因（常见原因：Page with redirect、Crawled but not indexed、Not found 404）

**⚠️ 一个常见误区**：页面可以正常访问，不代表已被 Google 索引。索引必须通过 Search Console 确认。

## 02. Sitemap.xml——给 Google 的收录地图

Sitemap（网站地图）是一个 XML 文件，列出你希望搜索引擎收录的所有页面及其最后更新时间。它不是排名因素，但能显著加快新页面的收录速度[^3]。

### 配置要点

- 使用 Rank Math 或 Yoast SEO 插件自动生成（WordPress 环境）
- 只包含需要被索引的 URL（排除标签页、作者归档页、搜索结果页）
- 提交到 Google Search Console 的 Sitemaps 栏目
- 更新内容后 Sitemap 应同步更新

### 常见配置错误

| 错误 | 后果 |
|------|------|
| Sitemap 包含 404 页面 | Google 收到大量无效 URL，降低信任 |
| 包含 noindex 页面 | 指令冲突，Google 以 noindex 为准 |
| 包含分页和筛选参数 URL | 造成大量重复内容 |
| Sitemap 一次性提交后从不更新 | 新页面无法被及时发现 |

## 03. Core Web Vitals——Google 的用户体验评分卡

Core Web Vitals 是 Google 衡量真实用户体验的三项核心指标，自 2021 年 6 月的 Page Experience 更新起正式成为排名信号[^4]。

2024 年 3 月，Google 用 INP 替换了原来的 FID（First Input Delay），使交互响应度的衡量更加全面[^5]。

### 三项指标及阈值

| 指标 | 衡量对象 | 良好阈值 | 较差阈值 | 数据来源 |
|------|---------|---------|---------|---------|
| LCP（最大内容绘制） | 加载速度 | ≤2.5 秒 | >4.0 秒 | 第 75 百分位 |
| INP（交互响应） | 交互响应度 | ≤200 毫秒 | >500 毫秒 | 第 75 百分位 |
| CLS（累计布局偏移） | 视觉稳定性 | ≤0.1 | >0.25 | 第 75 百分位 |

### 如何诊断和优化

**步骤 1：在 Search Console 中查看 Core Web Vitals 报告**

该报告按 URL 分组展示桌面端和移动端的表现。Google 使用 28 天窗口的 **实际用户数据（Field Data）**，而非 Lighthouse 的实验室数据。两者有本质区别：实验室数据基于模拟环境，实际数据来自 Chrome 用户的真实体验。

**步骤 2：按优先级优化**

优化的顺序建议：LCP → CLS → INP。原因如下：

- LCP 问题最常见，图片未优化是最大成因
- CLS 修复成本低，只需为图片和广告位预留尺寸空间
- INP 通常涉及 JavaScript 优化，技术门槛最高

**步骤 3：针对具体指标**

| 指标 | 最常见成因 | 最快修复方式 |
|------|----------|------------|
| LCP 慢 | 未压缩的大图 | 压缩图片 + WebP 格式 + 适当尺寸 |
| CLS 高 | 图片未设宽高 | 所有图片 `width` 和 `height` 属性必须存在 |
| INP 长 | 第三方脚本堵塞主线程 | 延迟加载非关键 JS，移除多余脚本 |

关于 Core Web Vitals 在排名中的权重，Google 明确说明：这是排名信号之一，但权重有限。内容相关性远胜于分数优化。一个 Core Web Vitals 满分的差内容不会获得高排名，反之一个有权威性的好内容即使 Core Web Vitals 略差仍可能排名靠前[^4]。

## 04. 结构化数据（Schema）——让搜索结果更显眼

结构化数据是使用标准格式告诉搜索引擎你页面内容类型的代码。它不会影响排名，但能让你在搜索结果中获得富媒体展示（如星级评分、价格、FAQ 展开），从而显著提升点击率[^6]。

### 独立站最常用的三种 Schema

**Product Schema（产品结构化数据）**
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

**FAQ Schema（常见问题）**
B2B 站点中 FAQ 页面或每个产品页的 FAQ 片段使用 FAQ Schema 后，Google 搜索中可以直接展开答案，大幅提升可见度。

**BreadcrumbList Schema（面包屑导航）**
帮助 Google 理解页面在站点层级中的位置，搜索结果中会显示面包屑路径，提升 CTR。

### 测试工具

Google Rich Results Test（https://search.google.com/test/rich-results）和 Schema Markup Validator 是免费的结构化数据验证工具。发布前务必验证一次。

## 05. 多语言站点 SEO（Hreflang）——防止内容重复惩罚

如果你的独立站有多个语言版本（如中、英、西语），需要正确使用 `hreflang` 标签告诉 Google 各语言页面的对应关系[^7]。

### 常见错误

- **不同语言内容混在同一页面**：每个语言版本应该有独立 URL
- **没有设置 hreflang**：Google 可能只索引其中一个版本
- **hreflang 指向错误或不存在页面**：配置后必须验证

### 正确配置方式

以 `/product/mccb`（英语）、`/zh/product/mccb`（中文）、`/es/product/mccb`（西班牙语）三版本为例：

```html
<link rel="alternate" hreflang="en" href="https://example.com/product/mccb" />
<link rel="alternate" hreflang="zh" href="https://example.com/zh/product/mccb" />
<link rel="alternate" hreflang="es" href="https://example.com/es/product/mccb" />
<link rel="alternate" hreflang="x-default" href="https://example.com/product/mccb" />
```

Rank Math 和 Yoast SEO 都支持在插件内直接配置 hreflang。

## 06. 技术 SEO 月度检查清单

建议每个月初花 30 分钟执行以下检查：

1. **Search Console → Pages 报告**：验证索引页面数量没有异常下降
2. **Search Console → Sitemaps**：确认 Sitemap 状态为 "成功"
3. **Sitebulb / Screaming Frog 扫描全站**：检查 404、301 链和重定向链长度
4. **Pagespeed Insights 抽检 3-5 个核心页面**：确认 Core Web Vitals 没有劣化
5. **确认 HTTPS 证书剩余有效期**：低于 30 天时安排更新

技术 SEO 不像撰写文章那样有 "发布一刻" 的满足感，但它为你的所有内容工作提供基础保障。没有它，内容做得再好，搜索引擎也看不到。

---

[^1]: Brian Dean, "We Analyzed 11.8 Million Google Search Results", Backlinko, 2024

[^2]: Google Search Central, "Crawl Budget Management", https://developers.google.com/search/docs/crawling-indexing/large-site-managing-crawl-budget

[^3]: Google Search Central, "Sitemaps", https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview

[^4]: Google Search Central, "Understanding Core Web Vitals and Google Search Results", https://developers.google.com/search/docs/appearance/core-web-vitals

[^5]: web.dev, "Web Vitals", https://web.dev/articles/vitals

[^6]: Google Search Central, "Understand How Structured Data Works", https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data

[^7]: Google Search Central, "Tell Google About Different Language Versions of Your Pages", https://developers.google.com/search/docs/specialty/international/localized-versions
