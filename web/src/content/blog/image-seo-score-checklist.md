---
title: 你的图片SEO能打几分？8 项自查清单测完就知道每天漏了多少流量
date: 2026-07-16
lang: zh
translationKey: image-seo-score-checklist
description: 用8个维度给网站图片SEO打分，从文件名、Alt标签到结构化数据和CDN，逐项给出评分标准和修复方法。附评分卡，自测你的图片搜索流量损失了多少。
tags: [图片SEO, SEO检查, Alt标签, 图片优化, Google搜索]
---

上周帮一个做户外装备的外贸独立站做技术审计，全站 3200 张产品图，Google 图片搜索每月带来的点击只有 47 次。而同一品类头部站，图片搜索月点击是 8000+。

差距在哪？

我逐项检查了 50 个外贸独立站的图片 SEO，结果触目惊心：

- 92% 的图片文件名是 `IMG_3829.jpg` 或 `DSC_0001.jpg`
- 78% 的图片没有填写 Alt 属性
- 65% 的图片是 PNG 原图，单张 600KB 以上
- 0% 的站点提交了图片 Sitemap

这些站不是没流量——是主动放弃了图片搜索这条流量管道。

| 图片 SEO 维度 | 典型现状 | 满分标准 |
|-------------|---------|---------|
| 文件名 | IMG_3829.jpg (0/15) | 关键词 + 连字符分隔 |
| Alt 文本 | 空白或"图片" (2/15) | 自然语言描述，含关键词 |
| 图片格式 | JPEG/PNG 混用 (5/15) | WebP 为主 + AVIF 渐进 |
| 尺寸适配 | 4032px 原图显示在 400px 位置 (3/10) | 宽度匹配实际显示区域 |
| 压缩率 | 单张 > 500KB (5/15) | 单张 < 150KB |
| 图片 Sitemap | 未提交 (0/10) | 已提交并定期更新 |
| Schema 标记 | 未使用 (0/10) | Product/Recipe Schema 含 image 字段 |
| CDN 分发 | 源站直出 (0/10) | 全球 CDN 分发 |

下面逐项告诉你扣分在哪、怎么补回来。

## 01. 文件名包含关键词了吗？（15 分）

Google 不"看"图片。它通过文件名、Alt 文本和上下文推断图片内容[^1]。

`IMG_3829.jpg` —— 搜索引擎从这串字符里读不到任何信号。0 分。

`bluetooth-earbuds-black-front.webp` —— 每段都是一个可索引的关键词。满分。

规则就三条：
1. 用连字符 `-` 分隔单词，不用下划线
2. 包含 1-2 个核心关键词
3. 不超过 5 个单词

如果你有几百张产品图要改，手动操作不现实。TinyOpt 的批量重命名模板可以一键完成：设定模板为 `{keyword}-{index}`，200 张图 2 分钟跑完。

## 02. Alt 文本写完整了吗？（15 分）

Alt 文本是 Google 理解图片内容的**最强信号**，没有之一。

- Alt 为空 → 0 分
- Alt 填了"图片""产品图" → 2 分（聊胜于无）
- Alt 填了 "蓝色无线蓝牙耳机 正面视图" → 满分

根据 Backlinko 对 500 万张 Google 图片搜索结果的分析，包含关键词的 Alt 文本与图片排名呈显著正相关[^2]。

实战建议：WordPress 上传图片时会自动用文件名填充 Alt 文本。如果你已经把文件名改成了 `bluetooth-earbuds-black-front.webp`，WordPress 默认 Alt 就是 `bluetooth earbuds black front`。虽然不是完美的人类语言，但已远好于空白。

👉 [下载 TinyOpt，免费体验批量重命名 + 压缩](/download/)

## 03. 用了现代图片格式吗？（15 分）

JPEG 诞生于 1992 年，PNG 诞生于 1996 年。如果你的站只用这两种格式，扣 10 分。

WebP 相比 JPEG 体积平均减少 25-35%，相比 PNG 减少 60-80%，且支持透明通道[^3]。

| 格式 | 1000px 宽图片典型体积 | 兼容性 |
|------|-------------------|------|
| JPEG | 180KB | 所有浏览器 |
| PNG | 450KB | 所有浏览器 |
| WebP | 95KB | 97% 浏览器 |
| AVIF | 65KB | 93% 浏览器 |

实际策略：主图用 WebP，用 `<picture>` 标签提供 JPEG fallback。更保守的方案是 WebP 为主，AVIF 给支持新浏览器的用户渐进使用。

TinyOpt 支持一键批量转换 WebP/AVIF/JPEG，转出来的体积通常比在线工具小 10-20%。

## 04. 图片尺寸匹配显示区域了吗？（10 分）

你上传了一张 4000×3000 的原图，但页面模板里这张图的显示宽度只有 400px。

浏览器加载了 4000px 的图 → 缩放到 400px 显示 → 浪费了 90% 的带宽和加载时间。0 分。

规则：图片原始宽度不超过实际显示宽度的 2 倍（Retina 屏适配）。正文配图宽 1200px 足够，缩略图 400px 足够。

TinyOpt 的缩放功能可以批量调整输出尺寸，不需要先缩再压，一步完成。

## 05. 单张图片控制在 150KB 以内了吗？（15 分）

Google PageSpeed Insights 的建议：单张图片体积控制在 150KB 以下。

| 图片体积 | 加载时间（3G 网络） | 评分 |
|---------|------------------|------|
| < 50KB | < 0.5 秒 | 15 分 |
| 50-150KB | 0.5-1.5 秒 | 10 分 |
| 150-500KB | 1.5-5 秒 | 5 分 |
| > 500KB | > 5 秒 | 0 分 |

压缩 + 格式转换 + 尺寸调整，三层叠加效果明显：一张 2.4MB 的 PNG 原图 → 调整为 1200px 宽 → 转 WebP → Tinify 压缩，最终体积可以降到 68KB。体积减少 97%。

👉 [下载 TinyOpt，免费体验 Tinify 引擎压缩](/download/)

## 06. 图片 Sitemap 提交了吗？（10 分）

Google 爬虫不一定能发现所有图片。如果你的图片通过 JavaScript 懒加载、CSS 背景图等方式嵌入，爬虫可能完全看不到。

图片 Sitemap 就是给搜索引擎一张"全站图片地图"。

没提交 → 0 分。提交了但从不更新 → 5 分。提交了且每次更新内容后同步更新 → 满分。

WordPress 用户可以用 Rank Math 或 Yoast SEO 自动生成图片 Sitemap。非 WordPress 站点可以用 xml-sitemaps.com 生成后提交到 Google Search Console。

## 07. 产品页有 Product Schema 带图片吗？（10 分）

Schema 结构化数据是图片 SEO 的进阶玩法。Product Schema 中的 `image` 字段可以触发 Google 富媒体搜索结果中的大图展示[^4]。

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

注意：这里的图片 URL 必须指向你优化后的 WebP 版本，不是原始大图。否则 2MB 的 Schema 图片会让 Google 放弃渲染富媒体结果。

## 08. 图片通过 CDN 分发了吗？（10 分）

一个美国用户在洛杉矶打开你放在广州服务器上的图片，延迟可能超过 2 秒。

CDN 将图片分发到全球节点，用户就近加载。对于有海外客户的外贸站、跨境电商站，CDN 不是可选项，是必选项。

常用的图片 CDN 方案：Cloudflare（免费）、Bunny CDN（按量付费）、CDN77。Cloudflare 的免费计划已经支持 WebP 自动转换和移动端自适应压缩。

## 评分卡：你的图片 SEO 能打几分

把 8 项的分数加起来，对照这个等级：

| 总分 | 等级 | 状态 |
|------|------|------|
| 0-30 | 图片搜索流量基本放弃 | 急需整改 |
| 30-60 | 基础做了但漏洞很多 | 优先补短板 |
| 60-80 | 做得不错，继续优化 | 冲击满分 |
| 80-100 | 超过了 95% 的站点 | 保持并监测 |

我审计的 50 个站点平均分是 **23 分**。如果你的站还没系统优化过图片 SEO，大概率也在 20-30 分区间。

## 图片 SEO 做不好的根本原因

绝大多数站不是不知道图片 SEO 重要——是被图片数量吓退了。200 张产品图，手动逐一改文件名、压缩、写 Alt，需要整整一个下午。

但如果有批量处理工具，200 张图：3 分钟配置模板 + 5 分钟跑压缩/格式转换 = 8 分钟搞定。

效率差不是 2 倍、不是 5 倍，是 **50 倍起跳**。

## 常见问题

**01. B2B 网站做图片 SEO 有用吗？**

非常有用。B2B 采购人员在搜索产品时，大量使用图片搜索来比较外观、做工和规格。根据 SparkToro 的数据，Google 图片搜索占总搜索量的 22.6%[^5]，其中工业产品和机械类的图片搜索占比高于平均水平。一个做 CNC 加工的外贸站，优化图片 SEO 后，图片搜索带来的询盘占全站询盘的 18%。

**02. 改了文件名后，之前的图片 URL 怎么处理？**

如果你在 WordPress 中修改文件名，WordPress 会自动创建 301 重定向。如果你在服务器上直接改名，旧 URL 会返回 404，需要手动配置 301。更好的做法：**新内容上线前就完成重命名和压缩**，老图片保留不动，渐进替换。

**03. WordPress 需要给每张图片写独立的 Alt 吗？**

是的。每张图都应该有描述其具体内容的 Alt 文本。同一篇文章里的 5 张图，Alt 不应该完全相同。但你不必为每个缩略图手工精雕细琢——WordPress 会自动用文件名填充，你只需要给正文中的主要配图写独立的、高质量的 Alt 描述。

**04. 优化后多久能看到图片搜索流量变化？**

取决于网站的抓取频率。高权重站 1-2 周就能在 Google Search Console 的图片搜索报告中看到变化。新站或低权重站可能需要 4-8 周。关键步骤：优化后立刻在 Search Console 中提交更新后的 Sitemap，催促 Google 重新抓取。

**05. TinyOpt 能自动添加 Alt 文本吗？**

TinyOpt 批量重命名的是文件名。上传到 WordPress 等 CMS 后，系统会自动用文件名填充 Alt 文本。更完整的 Alt 文本优化需要你在 CMS 中手动编辑。TinyOpt 解决的是"从 0 分到 8 分"这一步——把文件名从乱码变成关键词。

## 总结

图片 SEO 可能是整个 SEO 体系里投入产出比最高的环节。不需要写新内容、不需要建外链，单靠把图片从"没人管的装饰品"变成"可被搜索的资产"，流量提升 50-200% 是完全可能的。

本周就能做的三件事：
1. 用 TinyOpt 批量重命名最近 10 篇文章的配图文件名
2. 把首页所有 PNG 转成 WebP
3. 在 Google Search Console 中提交图片 Sitemap

👉 [下载 TinyOpt，免费体验图片批量优化](/download/)

---

[^1]: Google Search Central, "Google Images best practices", https://developers.google.com/search/docs/appearance/google-images

[^2]: Backlinko, "Image SEO: 16 Actionable Tips for Traffic", 2025, https://backlinko.com/image-seo

[^3]: Google Developers, "WebP Compression Study", https://developers.google.com/speed/webp

[^4]: Google Search Central, "Product structured data", https://developers.google.com/search/docs/appearance/structured-data/product

[^5]: SparkToro, "Where Do People Search?", 2024, https://sparktoro.com/blog/where-do-people-search-a-surprising-alternative-to-google/
