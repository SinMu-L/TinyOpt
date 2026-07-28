import sys
import os
import json
import ssl
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp", ".gif", ".tiff", ".tif"}

FORMATS = {
    "":       {"label": "原格式（不转换）", "mime": "",            "ext": "",     "pil_only": False},
    "jpeg":   {"label": "JPEG (.jpg)",      "mime": "image/jpeg",  "ext": ".jpg", "pil_only": False},
    "png":    {"label": "PNG (.png)",       "mime": "image/png",   "ext": ".png", "pil_only": False},
    "webp":   {"label": "WebP (.webp)",     "mime": "image/webp",  "ext": ".webp","pil_only": False},
    "gif":    {"label": "GIF (.gif)",       "mime": "image/gif",   "ext": ".gif", "pil_only": False},
    "tiff":   {"label": "TIFF (.tiff)",     "mime": "image/tiff",  "ext": ".tiff","pil_only": False},
    "bmp":    {"label": "BMP (.bmp)",       "mime": "image/bmp",   "ext": ".bmp", "pil_only": False},
    "avif":   {"label": "AVIF (.avif)",     "mime": "image/avif",  "ext": ".avif","pil_only": False},
    "ico":    {"label": "ICO (.ico)",       "mime": "image/x-icon","ext": ".ico", "pil_only": True},
    "pdf":    {"label": "PDF (.pdf)",       "mime": "application/pdf","ext": ".pdf","pil_only": True},
}
DEFAULT_FORMAT = ""

DEFAULT_KEYS = [
    {"key": "Rrrj15K5mlVfRHxhcjCDNWDX8zlKz9Wd", "remark": "Key-1"},
    {"key": "lljYDckvHXz4ZbL2w6csfMnGqjgG6dxN", "remark": "Key-2"},
    {"key": "wB5GkcFGBzpxCGgckbjn66sCddRnCwFv", "remark": "Key-3"},
    {"key": "v0MKkFyq6VmNPQtc7rFz5Ly2ZdV9lb8M", "remark": "Key-4"},
    {"key": "hzWSy3mgjvVQH97cdBqcScCJDNp31R9Z", "remark": "Key-5"},
    {"key": "TbwrFS17vq0PWy37rHGbDLfxKKdTCP9Q", "remark": "Key-6"},
]

RESIZE_METHODS = {
    "fit":   "适应 (fit) — 保持比例，在限定框内",
    "scale": "缩放 (scale) — 百分比缩放",
    "cover": "裁剪 (cover) — 保持比例，裁剪溢出",
    "thumb": "缩略图 (thumb) — 固定尺寸居中裁剪",
}
DEFAULT_RESIZE_METHOD = "fit"

WATERMARK_POSITIONS = {
    "top_left": "左上角",
    "top_center": "中上",
    "top_right": "右上角",
    "center_left": "左中",
    "center": "居中",
    "center_right": "右中",
    "bottom_left": "左下角",
    "bottom_center": "中下",
    "bottom_right": "右下角",
    "tile": "平铺",
}

WATERMARK_TYPES = {
    "image": "图片水印",
    "text": "文字水印",
    "both": "图片+文字",
}

RATIO_PRESETS = {
    "1:1":    (1, 1),
    "4:3":    (4, 3),
    "3:2":    (3, 2),
    "16:9":   (16, 9),
    "21:9":   (21, 9),
    "9:16":   (9, 16),
    "4:5":    (4, 5),
    "2:3":    (2, 3),
}
DEFAULT_RATIO = "1:1"

RATIO_MODES = {
    "crop":    "裁剪",
    "pad":     "填充",
    "stretch": "拉伸",
}
DEFAULT_RATIO_MODE = "crop"

RATIO_ANCHORS = {
    "center":        "居中",
    "top_left":      "左上",
    "top_center":    "中上",
    "top_right":     "右上",
    "center_left":   "左中",
    "center_right":  "右中",
    "bottom_left":   "左下",
    "bottom_center": "中下",
    "bottom_right":  "右下",
}
DEFAULT_RATIO_ANCHOR = "center"

RATIO_FILL_COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}

RENAME_VARIABLE_HINTS = {
    "{name}": "原文件名（不含后缀）",
    "{index}": "自动序号",
    "{date}": "当前日期（YYYYMMDD）",
}

LOCAL_JPEG_QUALITY = 85

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / ".tinypng_compressor_config.json"
MAX_FREE_SIZE = 5 * 1024 * 1024


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "api_key" in data and data["api_key"]:
                if "api_keys" not in data:
                    data["api_keys"] = []
                if not any(k["key"] == data["api_key"] for k in data["api_keys"]):
                    data["api_keys"].append({
                        "key": data["api_key"],
                        "remark": "",
                        "monthly_usage": 0,
                        "monthly_limit": 500,
                        "enabled": True,
                    })
                del data["api_key"]
            if "api_keys" not in data:
                data["api_keys"] = []
            if "history" not in data:
                data["history"] = []
            return data
        except:
            pass
    config = {"api_keys": [], "output_dir": "", "history": []}
    for dk in DEFAULT_KEYS:
        config["api_keys"].append({
            "key": dk["key"],
            "remark": dk["remark"],
            "monthly_usage": 0,
            "monthly_limit": 500,
            "enabled": True,
        })
    return config


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except:
        pass
