---
title: JPEG、PNG、WebP 还是 AVIF？9 种图片格式实测对比，一张表看懂怎么选
date: 2026-06-05
lang: zh
translationKey: format-conversion-guide
description: 用实测数据对比 JPEG、PNG、WebP、AVIF 等 9 种图片格式，告诉你不同场景该选哪个格式，附 TinyJPG 格式转换实操推荐。
tags: [图片格式, 性能优化, 使用指南, 实测对比]
---

选错图片格式是网页性能优化中最常见、也最容易修复的问题之一。正确的格式可以在肉眼无感的前提下让页面体积减半。

我用 TinyJPG 实测了一张 2.4MB 的照片在各格式下的表现。

## 各格式实测数据对比

| 格式 | 体积 | 压缩率 | 肉眼画质 | 最适合 |
|------|------|--------|---------|--------|
| 原图 | 2.4 MB | — | 100% | — |
| JPEG (Q85) | 380 KB | 减 84% | 优秀 | 照片，通用兼容 |
| PNG-24 | 1.8 MB | 减 25% | 无损 | 截图、图标、透明背景 |
| **WebP** | **260 KB** | **减 89%** | **优秀** | **网页使用 — 最均衡选择** |
| **AVIF** | **190 KB** | **减 92%** | **优秀** | **前沿场景，极致压缩** |
| GIF | 4.1 MB | 大 70% | 差（照片） | 仅限简单动图 |

**核心结论**：WebP 是当前网页场景的最优解。AVIF 压缩率更高但兼容性仍在扩展。JPEG 作为兜底格式依然可靠。

👉 [下载 TinyJPG，实测你的图片该用哪个格式](/download/)

## 按场景选格式

### Web 前端
```
照片 → WebP（JPEG 作为 fallback）
图标 → PNG 32-64px（能用 SVG 更好）
首屏大图 → AVIF（WebP 作为 fallback）
截图 → PNG 或 WebP 无损
Favicon → ICO（TinyJPG 支持输出）
```

### 电商
```
商品主图 → JPEG Q80-85
商品缩略图 → WebP
Banner → WebP
透明 overlay → PNG
```

### 打印与出版
```
印刷 → TIFF 或高质量 JPEG
归档 → PNG 无损或 TIFF
文档 → PDF（TinyJPG 支持图片转 PDF）
```

## 01. WebP — 当前最优选择

相比 JPEG，WebP 在同等画质下体积小 25-35%。Chrome、Firefox、Edge、Safari 均已支持，覆盖约 96% 的浏览器。

如果你现在默认全部用 JPEG，换成 WebP 是最划算的优化——改一个设置，省 30% 带宽。

## 02. AVIF — 压缩率天花板

AVIF 使用 AV1 编码，压缩率远超 WebP。代价是浏览器支持稍低（Safari 仍在完善中）。

建议用于首屏大图和大幅 Banner，配合 WebP 或 JPEG fallback。

## 03. JPEG — 还没过时

JPEG 的兼容性无人能及，对照片类内容的压缩效率依然优秀。作为兜底格式是最稳妥的选择。

参数建议：JPEG Q80-85 是画质和体积的最佳平衡点。

## 04. PNG — 需要透明时用

PNG 适合截图、图标和带文字的图形。无损、支持透明通道，但照片类文件明显偏大。

网页场景：照片用 WebP，仅在需要透明或像素级精确时用 PNG。

## 05. 特殊格式：ICO、PDF、TIFF、BMP、GIF

| 格式 | 主要用途 | 说明 |
|------|---------|------|
| **ICO** | Windows 图标、Favicon | 本地 Pillow 处理，256x256 RGBA |
| **PDF** | 文档、演示材料 | 本地处理，150 DPI RGB |
| **TIFF** | 印刷出版、归档 | 高质量大文件 |
| **BMP** | 旧版兼容 | 不要用于网页，TinyJPG 自动转 PNG |
| **GIF** | 简单动图 | 照片效果差，动图建议用 WebP/AVIF |

## 重要提示

- AVIF 和 WebP 需要为旧浏览器准备 fallback
- 有损压缩不可逆，原始文件务必保留归档
- 格式转换只能维持或降低画质，无法提升画质
- TinyJPG 转格式保留原尺寸，需要改尺寸请同时启用缩放
- BMP 文件会自动转为 PNG 再压缩

## 常见问题

**01. 网页照片用哪个格式最好？**
WebP。96%+ 浏览器支持，比 JPEG 小 25-35%，配合 JPEG fallback 覆盖所有用户。

**02. AVIF 能用于生产环境吗？**
可以，但必须配合 fallback。Chrome 和 Firefox 完美支持，Safari 正在追赶。建议 AVIF + WebP 双层 fallback。

**03. 格式转换会改变图片尺寸吗？**
不会。TinyJPG 在格式转换时保持原尺寸。需要改尺寸的话单独开启缩放功能。

**04. 能一次批量转成不同格式吗？**
一个任务只输出一种格式。需要不同格式请分多次执行。

**05. TinyJPG 支持哪些输入输出格式？**
输入：JPG、PNG、WebP、AVIF、BMP、GIF、TIFF
输出：JPEG、PNG、WebP、GIF、TIFF、BMP、AVIF、ICO、PDF

## 总结

没有最好的格式，只有最适合场景的格式。Web 用 WebP，追求极致用 AVIF，兼容兜底用 JPEG，需要透明用 PNG。

下载 [TinyJPG 压缩助手](/download/)，拿你自己的图片实测对比一下。
