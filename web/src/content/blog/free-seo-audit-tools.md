---
title: 免费 SEO 审计：GSC、SF 和 Lighthouse 全流程
date: 2026-07-21
lang: zh
translationKey: free-seo-audit-tools
description: 无需 Semrush 或 Ahrefs 也能完成专业 SEO 审计。Google Search Console、Screaming Frog 和 Lighthouse 三件免费工具，带你走完从全站扫描、索引检查到页面诊断的完整流程，附审计报告模板。
tags: [SEO审计, 免费工具, Google Search Console, Screaming Frog, Lighthouse]
---

**Semrush** 月费 **$139**，**Ahrefs** 月费 **$129**。对个人站长和自由职业者来说，这不是小数目——一年下来将近 **$1,700**，相当于一个中小站一年的服务器成本。

但好消息是：三件免费工具就能覆盖 **80%** 的专业 SEO 审计需求。省下的 $139 可以用来买链接、投广告，或者什么都不做。

这三件工具是：**Google Search Console**、**Screaming Frog SEO Spider**、**Lighthouse**。

## 工具对比

| 工具 | 覆盖范围 | 免费限制 | 核心用途 |
|------|---------|---------|---------|
| **Google Search Console** | 索引状态、搜索表现、Core Web Vitals | 无限制 | 宏观健康检查 |
| **Screaming Frog** | 全站爬取，200+ 指标 | 500 个 URL 免费 | 微观问题扫描 |
| **Lighthouse** | 页面级性能/SEO/无障碍 | 无限制 | 单页深度诊断 |

三件工具互补：GSC 看趋势，Screaming Frog 抓漏洞，Lighthouse 做深度。缺一不可。

## 01. GSC — 宏观健康检查（30 分钟）

GSC 是唯一能告诉你 Google 怎么看你网站的工具。它是你的 SEO 体检中心。

### 1.1 Pages 报告

在 GSC 左侧菜单打开 "Pages" 报告，看两个数字：

- **有效页面数**：趋势上升还是下降？连续两个月下降 = 有问题。
- **已排除页面数**：重点是 "已抓取但未收录" 的数量。

如果排除率 > **20%**，属于严重信号。意味着 Google 爬了你的页面但不认为值得收录——通常是内容质量问题。

### 1.2 Performance 报告

设置筛选：最近 **3 个月**，按排名排序。找出排名 **4-10 位**的关键词——这些是 SEO 中的"低垂果实"。

排名 4-10 的关键词只需微调（优化标题、补充内容、加内链）就有机会冲进前 3。排名 11-20 的词难度高一档，不建议优先处理。

导出 CSV，新增一列 "优化优先级"，按如下规则标注：
- 排名 4-7 → 高优先级
- 排名 8-10 → 中优先级
- 展示量 > 100 且排名 > 10 → 列为观察对象

### 1.3 Core Web Vitals 报告

切换到"移动"标签。看两个指标：

- **"Poor" 状态的 URL 数量**
- 按问题类型分组：LCP > 2.5s 的问题占比最高

常见根因：**未优化的图片**。一张 2MB 的 PNG 直接让 LCP 飙升到 4 秒以上。

👉 [TinyOpt 批量压缩图片，解决 60% 的 LCP 问题](/download/)

### 1.4 Sitemaps 板块

提交的 Sitemap 状态是否为"成功"？查看 "已提交 URL" 和 "已收录 URL" 的比值。

比值 < **50%** = 爬取预算或内容质量问题。需要回头去 Screaming Frog 分析哪些页面没被收录。

> GSC 不能做的事：检查全站 404、重复标题、缺失 H1、超大图片。这些要靠下线工具。

## 02. Screaming Frog — 微观问题扫描（1 小时）

**Screaming Frog SEO Spider** 免费版支持 **500 个 URL**。对大多数个人站和中小企业站，这个额度够用。

### 2.1 爬取配置

进入工具后做三步配置：

1. 输入网站 URL，点击 "Start"
2. Configuration → Spider → 勾选 "Crawl Images"、"Crawl CSS"、"Crawl JavaScript"
3. Configuration → User-Agent → 选择 "Googlebot (Smartphone)"

选择 Googlebot User-Agent 的原因是：你会看到 Google 看到的渲染结果，而不是用户看到的。某些 JS 渲染问题只在爬虫视角下暴露。

爬取时间：500 个 URL 约 **5-10 分钟**。

### 2.2 导出核心列

爬取完成后，导出 CSV。重点检查以下列：

| 列名 | 检查内容 | 严重度 |
|------|---------|-------|
| Status Code | 所有 404、301、302、500 | 高 |
| Title 1 | 重复标题（按字母排序找规律） | 高 |
| H1-1 | 缺失或重复的 H1 | 中 |
| Meta Description 1 | 缺失、过短（< 70 字符）、过长（> 160 字符） | 中 |
| Canonical Link Element 1 | 缺失 canonical 标签 | 高 |
| Image Size | 按大小降序，找出 > **500KB** 的图片 | 高 |
| Internal Links | 内链数为 **0** 的页面（孤立页面） | 高 |
| Click Depth | 深度 > **4** 的页面（Google 难发现） | 中 |

### 2.3 图片专项审计

在 Internal 标签下筛选 "Images"，做三项检查：

- **文件大小 > 500KB**：这些图片在直接拖慢 LCP。一张 800KB 的产品图不值得。
- **尺寸 > 2000px 宽**：显示宽度通常只有 800px，浪费了 **60%** 带宽。
- **无 Alt 文本**：SEO 盲区。Google Image Search 靠 Alt 理解图片内容。

👉 [TinyOpt 批量压缩 + 格式转换，把 > 500KB 的图片压到 < 150KB](/download/)

### 2.4 hreflang 审计

如果你的网站是多语言，检查 hreflang 标签：
- hreflang 是否指向 404 页面
- 是否遗漏了某些语言版本
- x-default 是否正确设置

hreflang 配错 = Google 可能向法文用户显示英文页面。

## 03. Lighthouse — 页面级诊断（30 分钟）

Lighthouse 嵌入在 Chrome DevTools 中，完全免费，无限制使用。

### 3.1 运行方法

打开 Chrome DevTools（F12）→ Lighthouse 标签 → 选择 Desktop + Mobile 各跑一次。

建议跑的页面：首页 + 3 个核心落地页 + 1 个博客页。这 5 个页面代表了站点的典型表现。

### 3.2 Performance 深度剖析

Performance 分数 < **50** = 有严重性能问题。看两个关键位置：

**LCP element**：页面上最大的可见元素是什么？如果是 `<img>`，检查三项：
- 是否已压缩？（原图 > 500KB = 不合格）
- 格式是 WebP/AVIF 还是 JPEG/PNG？
- 是否设置了 `loading="lazy"` 和显式宽高？

**Opportunities** 栏目的 "Serve images in next-gen formats"：这是 Lighthouse 最常给出的图片优化建议。换成 WebP/AVIF 直接解决。

👉 [TinyOpt 一键转 WebP/AVIF，直接消除 Lighthouse 的图片警告](/download/)

### 3.3 SEO 检查

Lighthouse 的 SEO 评分覆盖了 15+ 项基础检查：

- `Document has a <title> element`：基础但容易被忽略（尤其在 SPA 应用中）
- `Links have descriptive text`："点击这里" 和 "了解更多" 对 SEO 无价值
- `robots.txt is valid`：一个错误字符就能屏蔽全站
- Structured data validation：Lighthouse 会标记 Schema 的语法错误

每一项都值得通过。SEO 分 < **90** 建议逐项修复。

## 审计报告模板

每次审计结束，用以下三页模板整理结果：

**第 1 页：执行摘要**
- 发现的最严重 **3 个问题**
- 每个问题的预估修复时间
- 预期 SEO 影响（排名 / 收录 / 速度）

**第 2 页：优先级列表**

| 优先级 | 问题 | 影响页面数 | 修复难度 | 预估时间 |
|--------|------|-----------|---------|---------|
| P0 | 修复所有 404 | 12 | 低 | 30 分钟 |
| P1 | 压缩超过 500KB 的图片 | 34 | 低 | 20 分钟 |
| P2 | 补充缺失的 H1 | 8 | 低 | 15 分钟 |
| P3 | 调整重复标题 | 15 | 中 | 1 小时 |

按"影响 × 修复难度"排序。影响大 + 修复简单 = 优先做。

**第 3 页：修复追踪表**

| 周次 | 计划修复 | 已完成 | 备注 |
|------|---------|-------|------|
| 第 1 周 | 404 + 图片压缩 | ✓ | 一次性解决 |
| 第 2 周 | 标题 + H1 优化 | ✓ | 逐个页面改 |
| 第 3 周 | Canonical + Schema | 待完成 | 需要开发配合 |

## 模式总结

收费 SEO 工具增加的是**便利性**，不是**能力**。本文的三件免费工具能给你同等的诊断力。

收费工具唯一增加的价值是：
1. **规模**：超过 500 个 URL 的全站审计
2. **趋势追踪**：自动化周期性对比
3. **竞品分析**：查看对手的关键词策略

建议路径：先用免费工具，站点超过 500 页时再考虑付费工具。在此之前，省下来的 $139/月可以投入内容创作或外链建设。

## FAQ

**Q1：Screaming Frog 能爬大站吗？**

免费版上限 **500 个 URL**，超过需要购买 License（**￡199/年**，约 **$260**）。500 个 URL 对大部分个人站和中小站已经够用。

**Q2：Lighthouse 分数等于真实用户体验吗？**

不完全等于。Lighthouse 是**实验室数据**（模拟环境），GSC 的 Core Web Vitals 是**实地数据**（真实用户）。两者可能存在差异。以 GSC 数据为准，Lighthouse 用作发现问题的入口。

**Q3：有 GSC 了还需要 Screaming Frog 吗？**

需要。GSC 不会告诉你哪些页面有重复标题、哪些图片超过 500KB、哪些页面是孤立页面。GSC 看宏观，Screaming Frog 抓微观，两者互补。

**Q4：发现 50 个图片问题怎么批量修？**

一张张手动改不现实。用 **TinyOpt** 批量导入，一次性完成压缩 + 格式转换 + 尺寸缩放，50 张图几分钟搞定。

👉 [TinyOpt 批量处理，一行命令解决所有图片优化问题](/download/)

**Q5：审计频率应该是多久？**

**每月一次**。花 **2 小时**，够发现大部分问题。如果有新内容大量上线或改版，额外加一次。

## 总结

2 小时，3 件免费工具，覆盖 80% 的专业 SEO 审计需求。

这是你每个月花在 SEO 上最值的 2 小时。比追热点写文章、比研究最新的算法更新、比任何其他 SEO 投入都更确定——因为它直接告诉你问题在哪、怎么修、修完有什么效果。

操作流程记住三句话：
- **GSC** 看 Google 眼中的你
- **Screaming Frog** 看你自己不知道的漏洞
- **Lighthouse** 看每个页面的具体病症

今天下午打开 GSC，按本文 Step 1 走一遍。30 分钟后，你会看到一个你之前没注意到的问题。

👉 [下载 TinyOpt，先把 Lighthouse 报告的图片问题一次性解决](/download/)

---

[^1]: Google Search Central, "Google Search Console Help", https://support.google.com/webmasters/answer/9128668

[^2]: Screaming Frog, "SEO Spider Tool", https://www.screamingfrog.co.uk/seo-spider/

[^3]: Google Chrome Developers, "Lighthouse", https://developer.chrome.com/docs/lighthouse/

[^4]: Google Search Central, "Understand Core Web Vitals and Google Search Results", https://developers.google.com/search/docs/appearance/core-web-vitals
