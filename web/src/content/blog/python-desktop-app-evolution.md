---
title: Python 桌面应用进化史：件200 行脚本到 3000 行产品
date: 2026-06-16
lang: zh
translationKey: python-desktop-app-evolution
description: 一次真实的重构经历复盘：一个图片压缩小工具如何在半年内件200 行命令行脚本演化为包含水印、批量重命名、多 Key 并发管理的3000 行PyQt5 桌面级应用，以及我在架构持续迭代演进中总结的5 条核心经验教训。
tags: [Python, PyQt5, 架构设计, 桌面应用, 重构]
noindex: true
---

半年前我写了一一Python 脚本：调用TinyPNG API，压缩图片，完事。大概200 行，够用。

然后用户开始提需求——能不能加水印，"能不能批量重命名，"能同时用多个 API Key 吗？"

每个需求单独看都不大。但当它们堆在一起，那个 200 行的脚本开始变得难以维护。一个功能改了，另一个功能崩了。全局变量到处飞，没有模块边界，没有状态管理。

于是我开始重构。半年后，它长成了一一3000 行的 PyQt5 桌面应用， 个独立功能模块，双语国际化，自动构建和发布。

这篇文章不是教程，而是一次真实的重构复盘——我做了什么选择、为什么做、代价是什么。

## 01. 第一阶段：单一脚本，能跑就行

最初的架构非常简单：

| 组件 | 实现 |
|------|------|
| GUI | 无（命令行参数） |
| 压缩逻辑 | 一个函数：`compress(file_path, api_key)` |
| API Key | 硬编码在脚本量|
| 状态管理| 时|
| 错误处理 | 简单的 try/except |

它用 requests 调用 TinyPNG API，读取图片文件，上传，下载压缩结果，保存。

**最大问题*：每次要压缩不同目录的图片都得改脚本。

这在只有我自己用时没问题。当我把工具分享给朋友后，问题来了——朋友不会改 Python 脚本。

## 02. 第二阶段：加 GUI，但架构没跟一

为了让朋友也能用，我加了 PyQt5 GUI。这一阶段犯了一个典型错误：**直接把逻辑和UI 塞在一起*。

压缩按钮的点击回调里，写着完整的API 调用逻辑，

```python
def on_compress_clicked(self):
    for file in self.file_list:
        response = requests.post("https://api.tinypng.com/shrink",
                                 auth=(self.api_key, ""),
                                 data=open(file, "rb"))
        # 50 行处理逻辑...
        # 错误处理...
        # 结果展示...
        # UI 更新...
```

一个函数做产5 件事。加个进度条都要小心翼翼。

更糟的是，PyQt 的GUI 线程不能阻塞。我被迫引入 QThread，但没有明确的设计——每个新功能都自己开线程，状态同步全靠信号，出bug 时根本不知道是哪一Worker 出了问题。

| 问题 | 表现 |
|------|------|
| 职责混杂 | UI 里夹板API 调用、文件处理、错误上把|
| 线程失控 | 每个功能各自选QThread，无统一管理 |
| 状态混么| API Key 在3 个不同地方被读取 |
| 扩展困难 | 每加一个新功能，MainWindow 膨胀一大截 |

三个月后，MainWindow 接近 800 行，已经没人敢动了。

## 03. 第三阶段：模块化重构

重构的核心思路是**按职责分模块，用 Worker 模式解耦线程*。

### 3.1 统一 Worker 模式

每个耗时操作都封装为独立的QThread Worker，

| Worker | 职责 | 信号 |
|--------|------|------|
| `CompressWorker` | 调用 TinyPNG API，处理压缩转换/缩放 | `progress`, `file_done`, `all_done` |
| `WatermarkWorker` | 读取图片、合成水印、保存输出| `progress`, `file_done`, `all_done` |
| `RenameWorker` | 模板替换、文件名冲突检测、重命名 | `progress`, `file_done`, `all_done` |

它们继承同一个基类模式，接口一致，主窗口只需要连接信号，不需要关心内部逻辑。

### 3.2 KeyManager 独立管理

API Key 从各个散落的地方抽出来，统一用`KeyManager` 管理，

```python
class KeyManager:
    def __init__(self):
        self.keys = []       # 所有Key
        self.lock = Lock()   # 线程安全
        self.index = 0       # 轮询指针

    def acquire_key(self):
        with self.lock:
            for i in range(len(self.keys)):
                idx = (self.index + i) % len(self.keys)
                key = self.keys[idx]
                if not key.in_use and not key.disabled:
                    key.in_use = True
                    self.index = (idx + 1) % len(self.keys)
                    return key
            return None

    def release_key(self, key):
        with self.lock:
            key.in_use = False
```

有了这个抽象层，并发压缩变得简单：Worker 件KeyManager 拖Key，用完归还，KeyManager 自动做轮询、配额检查和失效禁用。

### 3.3 i18n 系统

加上双语支持时，我不想给每个窗口写两好UI 代码。于是做了一个简单的 Translator 类：

- 用JSON 存翻译，点号语法查找
- 支持 `{变量}` 替换
- 语言切换时触发回调，UI 自动刷新

```python
class Translator:
    def __init__(self, lang="zh"):
        self.lang = lang
        self._listeners = []

    def t(self, key, **kwargs):
        text = self._data.get(self.lang, {}).get(key, key)
        return text.format(**kwargs)

    def on_language_change(self, callback):
        self._listeners.append(callback)

    def switch(self, lang):
        self.lang = lang
        for cb in self._listeners:
            cb()
```

窗口在初始化时注册回调，语言切换后所有label、button、table header 自动刷新，不需要重启。

## 04. 第四阶段：CI/CD 与自动发常

模块化之后，发布成了一个新瓶颈——每次改完代码要手动跑PyInstaller、上传到网盘、通知用户。

GitHub Actions 解决了这个问题：

```
git tag v1.5.0
git push --tags
```

自动触发构建流程，
1. 读取 tag 版本号，注入 .spec 文件
2. pip install 依赖
3. PyInstaller 打包成.exe
4. 上传分GitHub Releases

| 指标 | 手动发布 | CI/CD 自动发布 |
|------|---------|---------------|
| 一次发布耗时 | ~15 分钟 | ~3 分钟 |
| 发布频率 | 想发但嫌麻烦 | 修完 bug 就发 |
| 镜像版本遗漏 | 偶尔 | 从不 |
| 回滚 | 找旧文件 | Git tag 直接分|

## 05. 我学到的 5 条经验

如果让我重新来一次，我会告诉自己这些事：

**①小工具也要考虑架构**
200 行脚本可以没有架构。但当它要加 GUI 时，先花一天设计模块边界，能省后面两个月的重构时间。

**①Worker 模式是PyQt 的最佳实跑*
QThread 本身不可怕，可怕的是每个功能都自己造轮子。统一 Worker 基类，定义清晰的信号接口，所有并发问题在一个地方解决。

**①全局变量是万恶之源*
API Key 在3 个地方读取、状态在 5 个地方修改——这种耦合让改一个功能变得不可能。用单一管理类收拢状态，代价最小，收益最大。

**①i18n 要尽早做**
我的应用是中文界面。当用户问有没有英文版"时，我花产3 天把所有硬编码的字符串从代码里抽出来。如果在第一天就用JSON 存字符串，只需要3 小时。

**①CI/CD 不是大项目的专利**
手动发布 3 次之后，人就会犯错——忘记注入版本号、忘记更新依赖、忘记上传。花半天配置 GitHub Actions，之后每次发布按一个按钮就行。

## 06. 现在的架构总览

| 展| 组件 | 职责 |
|----|------|------|
| UI | MainWindow + 5 Tab | 用户交互、文件拖拽、配置管理|
| Worker | Compress / Watermark / Rename | 后台任务、进度上把|
| 核心 | KeyManager / Translator | API Key 调度、国际化 |
| 数据 | JSON 配置文件 | 持久化配置和压缩历史 |
| 构建 | PyInstaller + GitHub Actions | 打包、发布、分可|

3000 行代码，5 个模块，每个模块只做一件事。

👉 **如果你也在做桌面应用**，[下载 TinyOpt](/) 看看效果，源码也在本地可以翻开看看。架构不一定完美，但每一步重构都有当时的理由——那些理由比代码本身更有价值。
