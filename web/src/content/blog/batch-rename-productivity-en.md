---
title: 500 Photos and Still Renaming One by One with F2? 10 Seconds with Template Variables
date: 2026-06-04
lang: en
description: Batch rename thousands of images in seconds using TinyJPG's template variables {name}, {index}, and {date}. Manual renaming takes 30 minutes — templates take 10 seconds.
tags: [batch-rename, productivity, file-management]
---

Camera output: `_DSC0001.jpg`. Screenshot: `screenshot_20260607_143322.jpg`. Downloaded asset: `image-xyz-1200x800.jpg`. These filenames are useless when you need to organize hundreds of images.

Manual renaming: Select → F2 → Type → Confirm. Repeat 500 times.

Last week I had 500 photos that needed to be named "ProjectName_Sequence_Date." With TinyJPG's batch rename feature, it took 10 seconds to configure and one click to execute.

| Comparison | Manual Rename | TinyJPG |
|-----------|--------------|---------|
| 500 files | 20-30 minutes | 10 seconds |
| Workflow | F2 → Type → Confirm × 500 | Configure once, execute all |
| Error rate | High (missed files, wrong sequences) | Zero (programmatic) |
| Complex naming | Not feasible | Template variable combinations |

## 01. Just Three Template Variables

TinyJPG offers three variables that cover 90% of renaming needs:

| Variable | Description | Example Output |
|----------|-------------|---------------|
| `{name}` | Original filename (no extension) | `IMG_001` → `IMG_001` |
| `{index}` | Auto-incrementing sequence (zero-padded) | `001`, `002`, ..., `999` |
| `{date}` | Current date | `20260607` |

**The template I used**:
```
Template: 2026_Portfolio_{index}_{date}
Result: 2026_Portfolio_001_20260607.jpg
     2026_Portfolio_002_20260607.jpg
     ...
```

👉 [Download TinyJPG and rename your files in bulk](/download/)

## 02. Advanced Configuration

Start from any number, not just 1:
```
Starting index: 100 → 101, 102, 103...
```

Custom date formats:
```
%Y%m%d → 20260607 (default)
%Y-%m-%d → 2026-06-07
%d-%m-%Y → 07-06-2026
```

A preview list is generated before execution so you can verify every new filename before committing.

## 03. Industry Naming Conventions

```
E-commerce: SKU_{color}_{index}.jpg
Photography: {date}_{project}_{index}.jpg
Design: {project}_{version}_{sequence}.png
Marketing: {platform}_{type}_{date}.jpg
```

General principles:
- **Machine-readable**: Avoid spaces and special characters
- **Human-readable**: Filename should describe content
- **Sortable**: Date or sequence prefixes enable natural ordering
- **Unique**: Prevent accidental overwrites

## 04. Safety Notes

- Renaming modifies original files — back up before large operations
- Existing filenames are automatically skipped (no overwrites)
- Windows `Ctrl+Z` can undo renaming
- Combine with compression and format conversion in one workflow

## FAQ

**01. Can I use EXIF capture date instead of current date?**
Currently uses file modification time or current date. EXIF capture date is not yet supported.

**02. Can I change the zero-padding width?**
Yes. Default is 3 digits (001). Change to 2 (01) or 4 (0001) in settings.

**03. Are original files preserved after renaming?**
Renaming modifies the original file directly. The old name is replaced. Back up if needed.

**04. Does it support files in subdirectories?**
Currently only processes the flat list of files you drag in. No recursive subdirectory scanning.

**05. Can I rename and compress at the same time?**
Yes. Enable the rename option in the compression task, and all operations complete in one pass.

## Summary

Batch renaming isn't high-tech, but it saves more time in daily work than most features. Three template variables, configure once, automate forever.

Download now: [TinyJPG Compressor](/download/)
