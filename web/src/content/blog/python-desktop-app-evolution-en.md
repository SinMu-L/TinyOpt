---
title: "Python Desktop App Refactoring: 200 to 3000 Lines"
date: 2026-06-16
lang: en
translationKey: python-desktop-app-evolution
description: "Refactoring journey: 200-line script to 3000-line PyQt5 desktop app. Watermarking, batch rename, multi-key concurrency, i18n, and 5 key lessons learned."
tags: [Python, PyQt5, architecture, desktop-app, refactoring]
noindex: true
---

Six months ago I wrote a Python script: call the TinyPNG API, compress images, done. Roughly 200 lines. It worked.

Then users started asking —"Can you add watermarking?" "Batch rename?" "Support multiple API keys?"

Each request looked small on its own. But stacked together, that 200-line script became unmanageable. Fix one feature, break another. Global variables everywhere. No module boundaries, no state management.

So I started refactoring. Six months later, it's a 3000-line PyQt5 desktop application with 3 independent modules, bilingual i18n, and automated CI/CD builds.

This isn't a tutorial —it's a real refactoring postmortem. What I chose, why I chose it, and what it cost.

## 01. Phase One: Single Script, Just Ship It

The original architecture was minimal:

| Component | Implementation |
|-----------|---------------|
| GUI | None (command-line only) |
| Compression | One function: `compress(file_path, api_key)` |
| API Key | Hardcoded in the script |
| State | None |
| Error handling | Basic try/except |

It used `requests` to call the TinyPNG API —read file, upload, download compressed result, save.

**Biggest problem**: compressing a different directory meant editing the script.

That was fine when I was the only user. When I shared it with friends, they couldn't —and shouldn't need to —edit Python scripts.

## 02. Phase Two: Added GUI, Did Not Add Architecture

I slapped a PyQt5 GUI on top. Classic mistake: **logic and UI fused together**.

The compress button callback contained the full API logic inline:

```python
def on_compress_clicked(self):
    for file in self.file_list:
        response = requests.post("https://api.tinypng.com/shrink",
                                 auth=(self.api_key, ""),
                                 data=open(file, "rb"))
        # 50 lines of processing...
        # error handling...
        # result display...
        # UI updates...
```

One function doing 5 things. Adding a progress bar felt dangerous.

Worse, PyQt's GUI thread can't block. QThread was necessary —but every feature built its own threading mechanism. State sync relied on signals. Debugging meant guessing which Worker misbehaved.

| Problem | Symptom |
|---------|---------|
| Mixed responsibilities | API calls, file I/O, error reporting all in UI code |
| Uncontrolled threading | Each feature rolled its own QThread |
| Scattered state | API Key read from 3 different locations |
| Hard to extend | Every new feature bloated MainWindow |

Three months in, MainWindow hit ~800 lines. Nobody wanted to touch it.

## 03. Phase Three: Modular Refactoring

The core idea: **separate by responsibility, decouple threads with the Worker pattern**.

### 3.1 Unified Worker Pattern

Each expensive operation became a dedicated QThread Worker:

| Worker | Responsibility | Signals |
|--------|---------------|---------|
| `CompressWorker` | TinyPNG API, format conversion, resize | `progress`, `file_done`, `all_done` |
| `WatermarkWorker` | Image loading, watermark compositing, output | `progress`, `file_done`, `all_done` |
| `RenameWorker` | Template substitution, conflict detection, rename | `progress`, `file_done`, `all_done` |

They share the same base pattern with identical signal interfaces. MainWindow connects signals —no need to understand internal logic.

### 3.2 KeyManager as Central State

API keys were scattered everywhere. `KeyManager` centralized them:

```python
class KeyManager:
    def __init__(self):
        self.keys = []
        self.lock = Lock()
        self.index = 0

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

This abstraction made concurrent compression simple: Workers get keys from the pool, return them when done. KeyManager handles round-robin distribution, quota tracking, and automatic disable of exhausted keys.

### 3.3 i18n System

When users asked for an English version, I didn't want to write two UIs. A simple `Translator` class solved it:

- JSON-based translation storage with dot-notation lookup
- `{variable}` substitution
- Language switch triggers callbacks —UI refreshes in place

```python
class Translator:
    def __init__(self, lang="en"):
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

Windows register callbacks on init. After a language switch, all labels, buttons, and table headers update automatically —no restart needed.

## 04. Phase Four: CI/CD and Automated Releases

After modularization, releases became the bottleneck —manual PyInstaller builds, uploading to cloud storage, notifying users.

GitHub Actions fixed it:

```
git tag v1.5.0
git push --tags
```

The pipeline automatically:
1. Reads the tag version, injects it into the .spec file
2. pip installs dependencies
3. Runs PyInstaller to build the .exe
4. Uploads to GitHub Releases

| Metric | Manual Release | CI/CD Automated |
|--------|---------------|-----------------|
| Time per release | ~15 min | ~3 min |
| Release frequency | Wanted to, but too tedious | Ship after every bugfix |
| Version tag mistakes | Occasionally | Never |
| Rollback | Find old file | Git tag checkout |

## 05. 5 Lessons I Learned

If I could start over, I'd tell myself this:

**—Small tools still need architecture**
A 200-line script doesn't need modules. But before adding a GUI, spend a day designing boundaries. It saves two months of refactoring.

**—Worker pattern is PyQt best practice**
QThread isn't scary —what's scary is every feature reinventing it. One base Worker class with clear signal interfaces solves all threading problems in one place.

**—Global variables are evil**
An API Key read in 3 places, state modified in 5 places —this coupling makes changes impossible. Centralize state in a single manager class. Minimal cost, maximum gain.

**—Add i18n early**
My app was Chinese-only. When users asked for English, it took 3 days to extract all hardcoded strings. If I'd used JSON from day one, it would have taken 3 hours.

**—CI/CD isn't just for big teams**
After 3 manual releases, humans make mistakes —wrong version, forgotten deps, missed uploads. Half a day to set up GitHub Actions, then every release is one button.

## 06. Current Architecture Overview

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| UI | MainWindow + 5 Tabs | User interaction, drag-drop, config |
| Worker | Compress / Watermark / Rename | Background tasks, progress reporting |
| Core | KeyManager / Translator | API key scheduling, internationalization |
| Data | JSON config file | Persistent config and history |
| Build | PyInstaller + GitHub Actions | Packaging, releases, distribution |

3000 lines, 5 modules. Each module does one thing.

馃憠 **Building a desktop app?** [Download TinyOpt](/) and see the result. Or browse the source —the architecture isn't perfect, but every refactoring decision had a reason. And those reasons are worth more than the code itself.
