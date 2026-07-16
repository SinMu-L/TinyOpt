---
title: 图还没加载完按钮就飞了？CLS 布局偏移 5 大元凶和 3 步修复法
date: 2026-07-17
lang: zh
translationKey: cls-layout-shift-fix
description: 图片没设宽高、第三方广告、动态注入内容都是 CLS 布局偏移的常见原因。本文逐一拆解 5 个罪魁祸首，给出 3 步修复流程，附带修复前后 CLS 实测数据对比。
tags: [CLS, Core Web Vitals, 布局偏移, 性能优化, PageSpeed]
---

你压缩了图片，换了 WebP，上了 CDN。打开 PageSpeed，分数还是黄的。点开 CLS 一看：0.38（不通过）。

问题不在图片大小，在布局偏移。

这才是最让人崩溃的部分——你已经做了所有"据说有效"的优化，但指标就是不动。因为你修的是体积，而 CLS 扣分的是页面跳动。

## CLS 到底有多普遍？先看一组数据

Google 在 2023 年 Core Web Vitals 报告中指出，CLS 是桌面端通过率最低的指标之一[^1]。HTTP Archive 的统计显示，全 Web 站点中 CLS 达到"良好"（< 0.1）的比例不到 60%。

以下是 5 个常见场景的实测 CLS 数据：

| 场景 | CLS 值 | 根本原因 |
|------|--------|---------|
| Banner 没设宽高 | 0.45 | 图片加载后撑开页面 |
| 第三方广告 | 0.32 | 动态 DOM 注入 |
| Web 字体替换 | 0.18 | 字体加载后文本回流 |
| Cookie 弹窗注入 | 0.22 | 新元素插入推下全部内容 |
| 嵌入 iframe | 0.28 | 没有预置尺寸 |

别急，一个一个修。

## 01. 图片没设宽高——最常见的 CLS 元凶

```html
<!-- 问题代码：浏览器完全不知道要预留多少空间 -->
<img src="banner.webp" alt="活动横幅">

<!-- 修复后的代码：浏览器提前知道尺寸，预分配空间 -->
<img src="banner.webp" alt="活动横幅" width="1200" height="600">
```

当你只写 `src` 不写 `width` 和 `height`，浏览器在做布局计算时，会先给图片分配 0px 高度。然后图片加载完成，瞬间撑开 600px。下面所有内容被往下推——这就是那 0.45 分的 CLS 来源。

修复方法只有两个属性：`width` 和 `height`。加上之后，浏览器按宽高比提前预留空间，图片加载不会产生任何位移。Chrome 90 以后自动计算 `aspect-ratio`，即使 CSS 设置了 `max-width: 100%`，只要宽高属性齐全，浏览器就能正确预分配。

除了给 `<img>` 加属性，CSS 的后备方案也很重要：

```css
img {
  aspect-ratio: attr(width) / attr(height);
  max-width: 100%;
  height: auto;
}
```

这些工作里，有一件事容易被忽略：你自己得先知道图片的真实尺寸。如果原图尺寸不统一——有些供应商给的图 2000px 宽，有些只有 600px——那即使写了宽高，页面也会因为不同图片尺寸差异产生二次偏移。

TinyOpt 的缩放功能可以在批量压缩时统一指定最大宽度，保持原始比例的同时让所有输出图片尺寸一致。这样你写入模板的 `width` 和 `height` 就是准的，不会出现比例不对导致图片变形的尴尬。

## 02. 第三方广告脚本——你控制不了它，但可以控制它的容器

Google AdSense 的加载逻辑是这样的：异步请求 → 返回广告内容 → 动态创建 iframe → 插入 DOM。这个过程里，广告脚本不知道你的页面布局，你想给广告预留多大空间它也不知道。

结果就是：广告返回前，那个位置是 0px 高；广告加载后，突然出现一个 280px 的广告卡片。一下把下面的产品列表推出一个屏幕。

解决思路：不是控制广告脚本，而是控制它的容器。

```html
<div class="ad-container">
  <!-- 广告脚本注入的位置 -->
  <ins class="adsbygoogle"
       data-ad-client="xxx"
       data-ad-slot="xxx"></ins>
</div>
```

```css
.ad-container {
  min-height: 280px;  /* 预分配足够的高度 */
  width: 100%;
  background: #f9f9f9;
}
```

关键是 `min-height`。即使广告加载失败返回空白，容器高度不会变，下面的内容就不会跳动。

同理适用于推荐系统、社交挂件、聊天插件。任何"页面加载后才注入内容"的第三方脚本，都应放在一个预定了 `min-height` 的容器里。

## 03. Web 字体导致文本跳动——font-display 是关键

你访问一个网站，文字先以宋体显示，半秒后突然变成自定义字体。如果两个字体渲染宽度不同，整段文字的换行位置就变了——这就是 CLS。

解决核心是两件事：

**一是设置 `font-display`：**

```css
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;  /* 或者 optional */
}
```

`swap` 的意思是：先用后备字体渲染，等自定义字体加载完后再替换。配合下面这条，能大幅减少 CLS。

**二是用 `size-adjust` 让后备字体和自定义字体宽度接近：**

```css
@font-face {
  font-family: 'CustomFont-fallback';
  src: local('Arial');
  size-adjust: 105%;     /* 微调宽度比 */
  ascent-override: 90%;  /* 微调上沿 */
}
```

这样即使自定义字体还没加载完，Arial 渲染出来的文字宽度和 CustomFont 几乎一样，替换时就不会产生明显的跳动[^2]。

👉 [下载 TinyOpt，先把你网站的图片尺寸统一了](/download/)

## 04. 动态注入内容——Cookie 弹窗、通知栏、促销横幅

Cookie 弹窗的典型实现：页面加载 → JS 检测 cookie → 没找到 → 在 `<body>` 顶部插入一个元素。这一步插入，把整个页面内容往下推了一个弹窗的高度。CLS +0.22。

修复原则一样：**提前分配空间**。

如果弹窗固定在顶部，CSS 这样写：

```css
#cookie-banner {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
}
```

`position: fixed` 将元素从文档流中移除，插入 DOM 时不会推动其他元素。

如果不能 fixed（比如弹窗要占据文档流位置），就用空占位容器：

```html
<div id="cookie-banner-container" style="min-height: 60px;">
  <!-- JS 动态填充弹窗内容 -->
</div>
```

## 05. 嵌入内容没预置尺寸——YouTube、地图、推特卡片

嵌入一个 YouTube 视频，不加任何样式：

```html
<!-- 问题：加载完后才发现是一个 560×315 的播放器 -->
<iframe src="https://www.youtube.com/embed/xxx"></iframe>
```

正确做法：

```html
<iframe
  src="https://www.youtube.com/embed/xxx"
  width="560"
  height="315"
  style="max-width: 100%; height: auto;">
</iframe>
```

或者用 CSS 的 `aspect-ratio` 做响应式：

```css
.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
}
.video-wrapper iframe {
  position: absolute;
  width: 100%;
  height: 100%;
}
```

## CLS 修复三步流程

别一次修全部。按以下流程来，每一步验证结果。

**Step 1：定位偏移元素**

Chrome DevTools → Performance 面板 → 录制页面加载 → 查看 Experience 行。红色矩形就是发生布局偏移的时刻。点击红块，Summary 面板会告诉你偏移分数和移动了哪个元素。

也可以用 Lighthouse 的 "Avoid large layout shifts" 审计，它会直接列出偏移最大的 DOM 元素。

**Step 2：逐个修复，逐个验证**

修一个问题 → 重新录 Performance → 确认该偏移消失 → 下一个。一次性修太多你分不清哪个生效、哪个没生效。

目标：CLS 降到 0.1 以下。对于大部分内容型网站，修完图片宽高、广告容器和字体三样，CLS 从 0.38 降到 0.05 只需 30 分钟。

**Step 3：把 Lighthouse CI 接入 CI 流水线**

修完不是终点。下一次发布新版本，新的 JS 组件可能又引入偏移。把 Lighthouse CI 接入 GitHub Actions 或 Jenkits：

```yaml
# .github/workflows/lighthouse.yml
- name: Run Lighthouse CI
  uses: treosh/lighthouse-ci-action@v12
  with:
    urls: |
      https://your-site.com/
    budgetPath: .github/lighthouse/budget.json
```

设置 CLS 阈值 0.1，超过就阻断合并。这样就再也不会半夜被 CLS 回归搞醒了。

👉 [下载 TinyOpt，图片尺寸一步到位](/download/)

## 模式总结：所有 CLS 共享同一个根因

回头看这 5 个场景，你会发现它们不是 5 个独立的问题，而是同一个问题换了 5 副面具。

**根因：浏览器不知道内容加载完之前要预留多大空间。**

图片没宽高 → 浏览器不知道预留多大面积 → 加载后撑开。

广告没容器 → 浏览器不知道广告会有多高 → 加载后推开。

字体不 match → 浏览器不知道后备字体渲染宽度 → 替换后回流。

Cookie 弹窗 → 浏览器不知道有元素要插进来 → 插入后下推。

iframe 没尺寸 → 浏览器不知道嵌入内容有多大 → 加载后显形。

**修复逻辑永远是一样的：提前告诉浏览器，这里要占多大位置。**

所以 CLS 不是什么深奥的优化技术。它只是一个信息差问题——你知道页面最终长什么样，但浏览器不知道。你要做的就是把这个信息提前传递过去。

## 常见问题

**01. 给图片加了 width/height 后，图片被拉伸变形了？**

因为你的 CSS 里设了 `height: 100%` 或固定像素高度，覆盖了原图的宽高比。检查并删除这些全局样式，改用 `height: auto` 配合 `max-width: 100%`。或者直接用 `aspect-ratio` 属性显式声明比例。

**02. CLS 从 0.4 修到 0.1，PageSpeed 能涨多少分？我指 SEO 层面。**

不直接涨分，但间接影响很大。CLS 是 Core Web Vitals 三大指标之一，直接影响 Google 的页面体验排名信号。从 0.4（需要改进）到 0.1（良好），至少把一个红色扣分项变成绿色加分项。有数据显示 Core Web Vitals 全部达标，移动端自然流量平均提升 8%[^3]。

**03. 延迟加载（loading="lazy"）会不会引入 CLS？**

会，而且很常见。延迟加载的图片如果不设 `width` 和 `height`，它们在滚动到视口附近才开始加载，加载完成后撑开页面——延迟加载把 CLS 的发生时间从"页面打开时"推迟到了"滚动时"。解决方法和普通图片完全一样：加上宽高属性。

**04. 动态内容（实时通知、聊天弹窗）的 CLS 怎么彻底解决？**

三种路径：① `position: fixed` 把元素脱离文档流；② 提前插入一个空容器占位，`min-height` 等于预期高度；③ 用 CSS transform/opacity 做出现动画而非直接插入 DOM。三种可以组合使用。

**05. 存量几百张图片没设宽高，怎么批量补上？**

有三种方法：

- **服务器端**：用脚本（Python PIL、Node sharp）批量读取图片尺寸，自动生成带 `width`/`height` 的 `<img>` 标签。
- **模板层**：如果用了 SSG（Astro、Next.js），构建时自动读取图片 metadata 填入标签。
- **先统一处理**：用 TinyOpt 批量缩放+压缩所有图片到一致尺寸，然后在模板中写一个统一的宽高值就行——因为所有输出图片尺寸已知且一致。

👉 [下载 TinyOpt，批量处理你的图片](/download/)

## 今天就能做的三件事

一、打开 Chrome DevTools Performance 面板，看看你的 CLS 到底是多少。

二、全站搜索 `<img`，检查有多少个 `<img>` 标签没有 `width`/`height` 属性，全局补上。

三、把你所有第三方脚本的容器加上 `min-height`。

这三件事做完，CLS 大概率从红变绿。

---

[^1]: Google. "The state of Core Web Vitals." web.dev, February 2023. https://web.dev/top-cwv-2023/
[^2]: Google Chrome Developers. "Optimize Cumulative Layout Shift." web.dev, 2024. https://web.dev/optimize-cls/
[^3]: Sistrix. "Core Web Vitals as a ranking factor — data study." sistrix.com, July 2021. https://www.sistrix.com/blog/core-web-vitals-ranking-factor-data/
