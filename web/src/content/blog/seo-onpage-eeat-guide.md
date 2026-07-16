---
title: 站内优化完全指南：从 Title 标签到 E-E-A-T，Google 如何评估你的页面质量
date: 2026-06-22
lang: zh
translationKey: seo-onpage-eeat-guide
description: 页面SEO是独立站获取搜索流量的基本功。本文从Title、Meta Description、标题层级到E-E-A-T框架，结合实战案例和Google官方指南，拆解每个优化要素的具体做法和常见错误。
tags: [页面SEO, E-E-A-T, Title标签, 标题层级, 内容优化]
---

去年我审计了一个年营收 2000 万美金的外贸 B2B 站点。技术上没有大问题，服务器响应快、HTTPS 已启用、移动端适配良好。然而 Google 收录了 400 多个页面，有排名的关键词不到 30 个。

逐个页面翻下去，原因一目了然：**全站 80% 的页面 Title 是自动生成的，H1 和页面标题完全重复，400 个页面的 Meta Description 只有 3 种模板**。

这是典型的 "重技术，轻页面" 的 SEO 失衡。页面 SEO（On-Page SEO）是搜索引擎评估页面相关性的最直接信号，也是最容易被系统化修复的优化环节。

## 01. Title 标签——搜索结果的第一印象

Title（标题标签）是搜索引擎结果页（SERP）中显示的可点击蓝色标题，也是页面 SEO 中权重最高的元素之一。

根据 Google 搜索中心的官方指南，Title 应该准确描述页面内容，且每个页面必须独立设置[^1]。

### 最佳实践

- **核心靠前**：主要关键词放在 Title 的前 60 个字符以内。Google 搜索结果通常显示 50-60 个字符（约 580-600px 宽度），超出的部分会被截断
- **每个页面唯一**：不存在两个页面共用同一个 Title
- **不堆砌关键词**：Google 明确表示关键词堆砌（Keyword Stuffing）违反其垃圾政策[^2]
- **加入品牌名**：建议在 Title 末尾加入品牌名，用竖线分隔，如 "MCCB 630A 3-Pole | ABC Electric"

### 反面案例

| 错误做法 | 问题 |
|---------|------|
| `<title>Home</title>` | 无关键词，不与业务相关 |
| `<title>MCCB | MCCB Supplier | MCCB Price | Best MCCB</title>` | 关键词堆砌 |
| 全站统一 `<title>ABC Electric Company</title>` | 所有页面无区分，搜索引擎无法判断相关性 |

### 实战案例

我们为一个做包装机械的客户重构 Title 策略。原来所有产品页的 Title 都是 "Product - Brand Name" 的统一格式。改后每个产品页独立设置，格式为 "产品型号 + 核心卖点 | Brand Name"。6 周后，产品页的点击率（CTR）从平均 2.1% 提升到 4.8%，直接带来询盘增长。

## 02. Meta Description——CTR 的隐形推手

Meta Description（元描述）虽然**不是直接的排名因素**，但它影响用户是否点击你的结果。Google 在 2024 年的更新中进一步强调了描述内容与搜索查询的匹配程度对 CTR 的影响[^3]。

### 写法建议

- 限制在 150-160 个字符
- 包含目标关键词（搜索结果中会加粗显示）
- 描述页面的独特价值，而非堆砌关键词
- 加入行动号召（CTA），如 "Get a quote in 24 hours"

### 一个改写的实际对比

写之前：`We supply high quality industrial valves. Our factory has 20 years of experience. Contact us for more information.`

改之后：`Looking for industrial gate valves for chemical plants? Our API 600 certified valves deliver zero-leak performance with 20 years of field-proven reliability. Request a quote.`

修改后 CTR 从 1.8% 提升到了 3.5%。

## 03. 标题层级 H1/H2/H3——给搜索引擎搭结构

标题标签（Heading Tags）是为页面内容搭建结构的基本工具，帮助搜索引擎理解页面各部分之间的主题关系[^4]。

### 三条绝对不能违反的规则

1. **每个页面有且只有一个 H1**
2. **标题层级不可跳跃**（H1 后直接 H3 是不合理的）
3. **H1 应与页面目标关键词一致**

### 正确结构示例

```html
H1: Industrial Gate Valve Selection Guide 2025
├── H2: What Is a Gate Valve?
│   └── H3: Gate Valve vs Ball Valve
├── H2: Key Specifications to Consider
│   └── H3: Pressure Rating and Temperature Limits
├── H2: Top 5 Gate Valve Manufacturers Compared
└── H2: Frequently Asked Questions
```

Google 在 2024 年 3 月的核心更新中进一步强化了 Helpful Content 系统（HCS）与搜索排名算法的融合，优质的结构化内容成为排名的重要参考[^5]。

## 04. E-E-A-T：Google 如何评估内容质量

E-E-A-T 是 Google 搜索质量评估指南中最重要的概念，代表 Experience（经验）、Expertise（专业）、Authoritativeness（权威）、Trustworthiness（可信）[^6]。

Google 在 2022 年 12 月从原来的 E-A-T 扩展到 E-E-A-T，新增的 "经验" 维度强调：**一手经验对内容质量的提升作用**。这不是一个直接的算法排名因素，而是指导人工评估员的框架，但它反映在 Google 的核心排名系统中[^7]。

### 四要素拆解与实操

| 要素 | Google 的期待 | 独立站怎么做 |
|------|-------------|-----------|
| Experience 经验 | 内容是否有真实使用经验？ | 提供产品实测数据、客户案例、工厂实拍 |
| Expertise 专业 | 内容创作者是否有该领域的知识？ | 署名专业人员，提供作者背景，引述行业标准 |
| Authoritativeness 权威 | 行业是否认可你为可靠来源？ | 获取外部链接、媒体报道、行业协会认证 |
| Trustworthiness 可信 | 内容和网站是否值得信任？ | HTTPS、联系方式透明、引用来源、信息准确 |

Google 官方明确指出："在这些要素中，可信是最重要的。其他要素服务于可信，但内容不需要展示所有要素"[^1]。

### B2B 独立站的 EEAT 增强策略

我们给一个做液压系统的客户制定了一套 EEAT 增强方案，核心改动只有三点：

1. **每篇技术文章都加 "作者 + 审阅人" 栏**，列明工程师姓名和从业年限
2. **技术参数标明来源**（引用 ISO 标准号、测试报告编号）
3. **每个产品页放一张工厂或产线实拍图**，而非只有渲染图

三个月后的变化：Google Search Console 中 "页面已收录但未索引" 的比例从 34% 降至 7%。

## 05. 五个可以立刻执行的优化项

1. **检查全站的 Title 唯一性**：用 Screaming Frog 或 Sitebulb 扫描，找出 Title 重复或缺失的页面
2. **建立 H1 审核机制**：新页面发布前确认是否满足 "一词一 H1"
3. **重写 Meta Description**：每个落地页补充独立的、包含 CTA 的描述
4. **增加作者信息**：技术文章和产品介绍页面需要署名
5. **检查事实准确性**：技术参数、行业引用是否准确，有没有过时的数据

页面 SEO 不需要大刀阔斧的改版，但需要系统性地、持续地执行。80% 的效果来自 20% 的基础工作——把 Title、H1、Description 这三件事做到位，排名不会太差。

---

[^1]: Google Search Central, "Creating Helpful, Reliable, People-First Content", https://developers.google.com/search/docs/fundamentals/creating-helpful-content

[^2]: Google Search Central, "Irrelevant Keywords", Google Search Essentials, https://developers.google.com/search/docs/essentials

[^3]: Google Search Central, "Control your snippets", https://developers.google.com/search/docs/appearance/snippet

[^4]: Google Search Central, "How Search Works – Organizing Information", https://www.google.com/search/howsearchworks/how-search-works/

[^5]: Google Search Central Blog, "March 2024 Core Update & Helpful Content Update", https://developers.google.com/search/updates

[^6]: Moz, "What is Google E-E-A-T? Guidelines and SEO Benefits", 2025, https://moz.com/learn/seo/google-eat

[^7]: Mateusz Makosiewicz & Joshua Hardwick, "E-E-A-T: How to Build Trust and Boost Web Visibility", Ahrefs Blog, 2023, https://ahrefs.com/blog/eeat-seo/
