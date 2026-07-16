---
title: 独立站 SEO 自检清单：10 大类 200 项检查点，漏一项排名就在漏流量
date: 2026-07-19
lang: zh
translationKey: seo-audit-checklist-200
description: 一份完整的SEO自检清单，覆盖爬虫抓取、技术基础、On-Page优化、内容质量、图片SEO、结构化数据、内链、外链、移动端适配、数据分析共10大类。如果你只有30分钟，先查高危20项。附带自动化工具检查方案。
tags: [SEO检查, SEO审计, 清单, 独立站, 技术SEO]
---

我上个月在一个外贸独立站群里做了个调查："你上一次做全站 SEO 体检是什么时候？" 30 个人回复，27 个说"没做过"或者"上线时查过一次"。

SEO 不是一次性工程。Google 每年更新算法超过 5000 次[^1]——你今天排名第一，不代表下个月还在那个位置。从没做过全站审计的网站，等于在漏排名而不自知。

👉 [下载 TinyOpt，先通过图片压缩消灭 20% 的扣分项](/download/)

## 01. 全站 SEO 审计的 10 大类，200 项检查点

以下分类按影响权重排序——**越靠前的分类，出了问题是致命的**。

| # | 类别 | 检查项数 | 可自动化项数 | 主要工具 |
|---|------|---------|------------|---------|
| 1 | 抓取与索引 | 25 | 20 | Screaming Frog, GSC |
| 2 | 技术基础设施 | 25 | 18 | Screaming Frog, Lighthouse |
| 3 | On-Page 优化 | 25 | 15 | Screaming Frog |
| 4 | 内容质量 | 25 | 5（需人工） | 人工审查 |
| 5 | 图片 SEO | 20 | 10 | TinyOpt, Screaming Frog |
| 6 | 结构化数据 | 15 | 10 | Schema Validator, GSC |
| 7 | 内链结构 | 20 | 15 | Screaming Frog |
| 8 | 外链健康度 | 15 | 10（GSC） | GSC, Ahrefs |
| 9 | 移动端适配 | 15 | 10 | Lighthouse, GSC |
| 10 | 数据分析与工具 | 15 | 8 | GSC, GA4 |

下面逐个展开最容易忽略、后果最严重的高危项。

## 02. 致命项 01：robots.txt 封了全站？

这是我们之前一篇技术 SEO 文章里写过的真实案例[^2]：一个站点上线两个月，Google 一个页面都没收录。排查了所有可能，最终在根目录发现了一行代码：

```
Disallow: /
```

托管商预置的默认 robots.txt 没有更新。一个字面意思上的"封站"，持续了 60 天。

**自查方式**：打开 `https://你的域名/robots.txt`，确认没有以下内容：

| 危险指令 | 后果 |
|---------|------|
| `Disallow: /` | 全站禁止抓取 |
| `Disallow: /wp-admin/` + 模板没改 | 虽不致命但常见的默认值未清理 |
| `Sitemap: http://example.com/sitemap.xml` | Sitemap 指向了演示域名 |

如果 robots.txt 里写的是 `Disallow: /`，恭喜，Google 从来没有见过你。

## 03. 致命项 02：HTTPS 页面加载了 HTTP 资源（Mixed Content）

HTTPS 证书安装成功 ≠ 全站安全。只要一个页面上混入了一张 `http://` 协议的图片或脚本，浏览器地址栏会显示 "不安全" 警告。

Google 在 2014 年就将 HTTPS 作为排名信号[^3]。2024 年 Chrome 已将所有 HTTP 资源默认阻止加载。Mixed Content 直接等于扣分。

| 资源类型 | 风险 |
|---------|------|
| 图片 (`<img>`) | 浏览器标记页面为"不安全" |
| JS/CSS | 浏览器直接阻止加载，页面显示异常 |
| 内嵌视频/字体 | 内容无法渲染 |

**一键检测**：Screaming Frog → Security 报告 → Mixed Content，秒出结果。

## 04. 致命项 03：Title 标签大面积重复

去年审计一个 2000 万美金营收的 B2B 站，全站 400 个页面，Title 只有 7 种模板。400 个产品页，50 个共用同一个 Title："Products - Company Name"。

Google 无法区分这些页面，只能随机挑几个来排名——其他的直接不展示。

**自查方式**：Screaming Frog → Page Titles → Duplicate 一栏，查看重复率。健康网站应该 <5%。

**修复原则**：

| 页面类型 | Title 格式建议 |
|---------|--------------|
| 首页 | 核心词 + 品牌名 |
| 产品页 | 产品名 + 核心卖点（1个） + "\| 品牌" |
| 分类页 | 分类词 + "Best \| Top \| Wholesale" + "\| 品牌" |
| 文章页 | 文章标题（含目标关键词）+ "\| 品牌" |

每页独立，绝不重复。这是 On-Page SEO 的第一条铁律。

## 05. 致命项 04：核心页面缺少 Canonical 标签

Canonical（规范链接）告诉 Google："这个页面的官方版本是 xxx"。没有它，Google 可能选错收录版本——或者以为你在重复发布内容。

Google 官方指南明确建议：**每个页面都应该有自引用的 Canonical 标签**[^4]。

```html
<link rel="canonical" href="https://yoursite.com/current-page-url/" />
```

常见错误：

| 错误 | 后果 |
|------|------|
| 全站缺失 Canonical | Google 自行判断收录版本，可能选错 |
| 指向首页 `href="/"` | 所有页面被认为与首页重复 |
| Canonical 指向 404 | 告诉 Google 你的页面已死 |
| 分页页面 Canonical 指向第 1 页 | 第 2-N 页永远不会被索引 |

Screaming Frog → Directives → Canonicals，查看缺失和错误比例。

## 06. 致命项 05：图片 Sitemap 从未提交

很多网站提交了页面 Sitemap，但从来没有提交过图片 Sitemap。后果是：Google 不会主动爬取你的图片，图片搜索流量为 0。

对于电商站和图片密集型站点，图片搜索可以贡献 10-25% 的自然流量[^5]。

| 自检项 | 检查方式 |
|-------|---------|
| 图片 Sitemap 已生成？ | Wordpress：Rank Math / Yoast 自动生成。其他：需插件或手动生成 |
| 已提交到 GSC？ | GSC → Sitemaps → 检查图片 Sitemap 的提交状态 |
| 图片 URL 均为可访问的 HTTPS 链接？ | 随机抽检 5-10 个 Sitemap 中的图片 URL |

👉 [TinyOpt 批量压缩图片后，文件名和路径不变，不影响已有的图片 Sitemap](/download/)

## 07. 高危项 06：站内死链（404）在浪费抓取预算

Google 每天分配给你网站的爬取次数是有限的（Crawl Budget）。如果 Google 花了 30% 的抓取配额在 404 页面上，意味着 30% 的有效页面没有被及时发现。

**自查方式**：Screaming Frog → Response Codes → Client Error (4XX)。

| 死链来源 | 修复方式 |
|---------|---------|
| 删除了产品页但分类页还在链接 | 301 重定向到相关分类或替代产品 |
| 旧版 URL 结构变更后未处理 | 批量 301 到新 URL |
| 文章引用外部链接已失效 | 更新链接或删除 |

理想状态下，站内 404 数量应为 0。如果一个页面必须删除，给它一个 301 去处。

## 08. 高危项 07：薄内容页面（<300 字）

Google 的 Helpful Content System 专门针对"低质、无独特性"的页面[^6]。如果你的网站上存在大量 <300 字的页面且没有独特价值，它们在拖累整站的质量评分。

**自查方式**：导出全站页面列表，人工筛查每个页面的字数。重点关注：

- 产品页（大量站的产品页只有图片没有文字）
- 标签/tag 归档页（全站相同）
- 作者存档页（内容极少）

修复方案：

| 情况 | 措施 |
|------|------|
| 页面有潜在价值但内容不足 | 扩充到 500+ 字，补充独特信息 |
| 页面本身无价值（如 tag 归档页） | 添加 `noindex` 标签 |
| 页面与另一页面内容高度重复 | 合并内容，原 URL 301 到新页面 |

## 09. 高危项 08：移动端可用性问题

Google 自 2023 年起全面推行移动优先索引（Mobile-First Indexing）[^7]。你的桌面版再完美，移动端有问题就等于零。

**GSC → Mobile Usability 报告**，最常见的三个问题：

| 问题 | 触发条件 | 最快修复 |
|------|---------|---------|
| 文字太小，难以阅读 | 字号 <12px 的文本 | 设置 `font-size: 16px` 作为基准 |
| 可点击元素太近 | 按钮间距 <8mm | 增加 `padding` 或 `margin`，触摸目标 ≥48px |
| 内容宽度超出屏幕 | 图片或表格未响应式 | 添加 `max-width: 100%` 

每一个移动端可用性错误，都是在告诉 Google："我不关心手机用户"。

## 10. 30 分钟快速审计：20 项必查

如果你只有 30 分钟，按以下顺序执行：

**GSC（5 分钟，5 项）**：

1. Pages 报告 → 查看 "Not indexed" 页面数量和原因
2. Sitemaps → 确认 Sitemap 提交状态为 "Success"
3. Core Web Vitals → 查看移动端和桌面端的 LCP/INP/CLS 分组状态
4. Mobile Usability → 确认无错误页面
5. Security Issues → 确认无安全问题

**Screaming Frog 快速扫描（10 分钟，5 项）**：

6. Response Codes → 检查 404 和 500 错误数量
7. Page Titles → 重复 Title 比例
8. Meta Description → 缺失或重复比例
9. Canonicals → 缺失比例
10. H1 → 缺失或重复 H1 的页面数

**手动检查（10 分钟，5 项）**：

11. `yoursite.com/robots.txt` → 确认没有 Disallow: /
12. 浏览器输入域名 → 确认 HTTPS 自动跳转且无安全警告
13. 用手机打开首页 → 检查加载速度和是否横向滚动
14. 抽检 3 个核心产品页 → 确认每页 Title / H1 / Description 都独立设置
15. 在 Google 搜索 `site:yoursite.com` → 对比收录数量与你的页面总数

**Lighthouse（5 分钟，5 项）**：

16. Performance 分数是否 ≥70（移动端）
17. Accessibility 分数是否 ≥85
18. Best Practices 分数是否 ≥90
19. SEO 分数是否 ≥90
20. 查看 Opportunities → 最大的单项收益是什么

## 11. 自动化检查方案

合理利用工具可以覆盖约 160 项检查，剩下 40 项需要人工判断。

| 工具 | 覆盖项数 | 费用 | 核心能力 |
|------|---------|------|---------|
| Screaming Frog | ~120 项 | 免费（500 URL）/ 付费 | 全站爬虫扫描 |
| Google Search Console | ~40 项 | 免费 | 索引状态、效果数据 |
| Lighthouse | ~30 项 | 免费 | 性能和 PWA 审计 |
| Schema Validator | ~15 项 | 免费 | 结构化数据验证 |
| TinyOpt | 图片 CSS 相关 ~10 项 | 免费 | 批量图片压缩优化 |

人工必须参与的内容：内容质量判断、E-E-A-T 信号评估、关键词策略审查、外链质量分析。

## 12. 规律总结：SEO 审计不是找问题，是找影响排名的问题

做完一次全站审计，你可能会找到 50-200 个问题。关键不是问题数量，而是优先级。

80/20 法则在这里同样适用：**20% 的问题导致 80% 的排名损失**。

优先级排序规则：

```
如果 Google 根本找不到你的页面 → 先把抓取和索引的问题清零
如果页面能被找到但没人点 → 优化 Title 和 Description
如果点了但跳走了 → 检查内容质量和页面速度
如果内容很好但没排名 → 检查 E-E-A-T 信号和外链
```

从第一类开始。底层的砖歪了，顶层的装修再好也没有意义。

## 13. 常见问题

**Q1：SEO 审计多久做一次？**

全站深度审计每季度一次。轻量检查（GSC + 核心页面抽查）每月一次。技术配置变更（域名迁移、改版、换主题）后立即做一次。

**Q2：不懂技术能做 SEO 审计吗？**

能。至少完成第 10 节中的 "手动检查 5 项" 和 "GSC 5 项"，这些不需要技术背景。技术类的部分可以找技术人员配合。

**Q3：查出 100 个问题，先修哪一个？**

先修"阻塞类"：robots.txt 错误、全站 noindex、HTTPS 证书过期、Sitemap 提交失败。这些是"其他问题修好了也没有用"的问题。

**Q4：审计一定要付费工具吗？**

不必要。Screaming Frog 免费版可扫描 500 个 URL，对小站（<100 个页面）足够。GSC 和 Lighthouse 完全免费。付费工具能显著提高效率但不影响你发现核心问题。

**Q5：怎么说服客户/老板投入资源修 SEO 问题？**

不要用 SEO 术语。用他们的语言：**"你的网站在用户搜【核心产品词】时，Google 没有展示。竞争对手的页面占了那个位置。修复这个问题，预计 X 周后开始看到流量变化。"**

## 14. 总结

从第 1 类开始——抓取与索引。Google 看不到的页面，等于不存在。

200 项不必一次查完。第一次：把 8 个致命项扫干净。然后按月轮值检查各类别，用一个季度覆盖全 10 类。

SEO 审计不是考试，不是分数越高越好。它是一张地图——告诉你哪里在漏流量，以及先堵哪个洞。

👉 [下载 TinyOpt，先通过图片压缩消灭 20% 的扣分项](/download/)

---

[^1]: Moz, "Google Algorithm Update History", 2025, https://moz.com/google-algorithm-change

[^2]: Google Search Central, "Robots.txt Introduction", https://developers.google.com/search/docs/crawling-indexing/robots/intro

[^3]: Google Security Blog, "HTTPS as a Ranking Signal", 2014, https://developers.google.com/search/blog/2014/08/https-as-ranking-signal

[^4]: Google Search Central, "Canonical URLs", https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

[^5]: Google Search Central, "Image Sitemaps", https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps

[^6]: Google Search Central, "Creating Helpful, Reliable, People-First Content", https://developers.google.com/search/docs/fundamentals/creating-helpful-content

[^7]: Google Search Central, "Mobile-First Indexing", https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-first-indexing
