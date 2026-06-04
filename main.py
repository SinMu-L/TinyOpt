import sys
import os
import json
import ssl
import time
import threading
from datetime import datetime
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ssl._create_default_https_context = ssl._create_unverified_context

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QLineEdit, QCheckBox,
    QGroupBox, QSplitter, QAbstractItemView, QDialog, QFormLayout,
    QSpinBox, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QStackedWidget, QSlider,
    QFontDialog, QColorDialog, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QRect
from PyQt5.QtGui import (
    QDragEnterEvent, QDropEvent, QFont, QColor, QBrush, QIcon,
    QPixmap, QPainter, QPen
)

import requests
from PIL import Image, ImageDraw, ImageFont


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

RENAME_VARIABLE_HINTS = {
    "{name}": "原文件名（不含后缀）",
    "{index}": "自动序号",
    "{date}": "当前日期（YYYYMMDD）",
}

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
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


def format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024*1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes // 1024} KB"
    return f"{size_bytes} B"


def find_font_path(family_name):
    """Find font file path on Windows by family name."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                if name.split('&')[0].strip().lower() == family_name.lower():
                    winreg.CloseKey(key)
                    fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
                    return os.path.join(fonts_dir, value)
            except OSError:
                break
            i += 1
        winreg.CloseKey(key)
    except:
        pass
    fallback_map = {
        "微软雅黑": "msyh.ttc",
        "宋体": "simsun.ttc",
        "黑体": "simhei.ttf",
        "楷体": "simkai.ttf",
        "Arial": "arial.ttf",
        "Tahoma": "tahoma.ttf",
        "Verdana": "verdana.ttf",
        "Times New Roman": "times.ttf",
        "Courier New": "cour.ttf",
    }
    if family_name in fallback_map:
        fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        path = os.path.join(fonts_dir, fallback_map[family_name])
        if os.path.exists(path):
            return path
    return None


def calc_watermark_position(img_w, img_h, wm_w, wm_h, x_ratio, y_ratio, margin_x=20, margin_y=20):
    """Calculate watermark position from ratio (0-1) with margin clamping."""
    avail_w = max(1, img_w - wm_w)
    avail_h = max(1, img_h - wm_h)
    x = int(margin_x + (avail_w - 2 * margin_x) * x_ratio)
    y = int(margin_y + (avail_h - 2 * margin_y) * y_ratio)
    x = max(margin_x, min(img_w - wm_w - margin_x, x))
    y = max(margin_y, min(img_h - wm_h - margin_y, y))
    return (x, y)


def render_text_watermark(text, font_path, font_size, font_color):
    """Render text as RGBA PIL Image with anti-aliasing."""
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    dummy = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0] + 20
    th = bbox[3] - bbox[1] + 20
    wm = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wm)
    draw.text((-bbox[0] + 10, -bbox[1] + 10), text, font=font,
              fill=(*font_color[:3], 255))
    return wm


def apply_watermark_to_image(image, watermark_type, watermark_img=None,
                              watermark_text="", font_path=None, font_size=48,
                              font_color=(255, 255, 255), x_ratio=0.85, y_ratio=0.85,
                              opacity=80, scale=15, margin_x=20, margin_y=20):
    """Apply watermark to a PIL Image, return watermarked Image."""
    if watermark_type not in ("image", "text", "both"):
        return image
    img = image.convert('RGBA') if image.mode != 'RGBA' else image.copy()
    img_w, img_h = img.size

    wm = None
    if watermark_type == "image" and watermark_img is not None:
        wm = watermark_img.copy()
        if wm.mode != 'RGBA':
            wm = wm.convert('RGBA')
        wm_w = max(1, int(img_w * scale / 100))
        wm_h = max(1, int(wm.height * wm_w / wm.width))
        wm = wm.resize((wm_w, wm_h), Image.LANCZOS)

    elif watermark_type == "text" and watermark_text:
        wm = render_text_watermark(watermark_text, font_path, font_size, font_color)

    elif watermark_type == "both" and watermark_img is not None and watermark_text:
        wm_img = watermark_img.copy()
        if wm_img.mode != 'RGBA':
            wm_img = wm_img.convert('RGBA')
        wm_w = max(1, int(img_w * scale / 100))
        wm_h = max(1, int(wm_img.height * wm_w / wm_img.width))
        wm_img = wm_img.resize((wm_w, wm_h), Image.LANCZOS)
        wm_txt = render_text_watermark(watermark_text, font_path, font_size, font_color)
        combined_w = max(wm_img.width, wm_txt.width)
        combined_h = wm_img.height + 5 + wm_txt.height
        wm = Image.new('RGBA', (combined_w, combined_h), (0, 0, 0, 0))
        wm.paste(wm_img, ((combined_w - wm_img.width) // 2, 0), wm_img)
        wm.paste(wm_txt, ((combined_w - wm_txt.width) // 2, wm_img.height + 5), wm_txt)

    if wm is None:
        return image

    if opacity < 100 and wm.mode == 'RGBA':
        r, g, b, a = wm.split()
        a = a.point(lambda x: int(x * opacity / 100))
        wm = Image.merge('RGBA', (r, g, b, a))

    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0))

    pos = calc_watermark_position(img_w, img_h, wm.width, wm.height,
                                   x_ratio, y_ratio, margin_x, margin_y)
    result.paste(wm, pos, wm)

    if image.mode != 'RGBA':
        result = result.convert(image.mode)
    return result


def generate_rename_preview(file_paths, pattern, start_index=1, pad_digits=3, date_format="%Y%m%d"):
    """Generate preview of renamed files. Returns list of (old_path, new_name)."""
    results = []
    today = datetime.now().strftime(date_format)
    for i, fp in enumerate(file_paths):
        p = Path(fp)
        name = p.stem
        ext = p.suffix
        new_name = pattern
        new_name = new_name.replace("{name}", name)
        new_name = new_name.replace("{index}", str(start_index + i).zfill(pad_digits))
        new_name = new_name.replace("{date}", today)
        new_name += ext
        results.append((fp, new_name))
    return results


class KeyManager:
    def __init__(self, keys_data=None):
        self.keys = keys_data or []
        self.current_index = 0
        self._lock = threading.Lock()

    def add_key(self, key, remark="", monthly_limit=500):
        self.keys.append({
            "key": key,
            "remark": remark,
            "monthly_usage": 0,
            "monthly_limit": monthly_limit,
            "enabled": True,
            "in_use": False,
        })

    def remove_key(self, index):
        if 0 <= index < len(self.keys):
            self.keys.pop(index)

    def toggle_key(self, index):
        if 0 <= index < len(self.keys):
            self.keys[index]["enabled"] = not self.keys[index]["enabled"]

    def get_available_keys(self):
        return [
            k for k in self.keys
            if k["enabled"] and k["monthly_usage"] < k["monthly_limit"]
        ]

    def acquire_key(self):
        with self._lock:
            for offset in range(len(self.keys)):
                idx = (self.current_index + offset) % len(self.keys)
                k = self.keys[idx]
                if (k["enabled"] and k["monthly_usage"] < k["monthly_limit"]
                        and not k.get("in_use", False)):
                    k["in_use"] = True
                    self.current_index = (idx + 1) % len(self.keys)
                    return k
            return None

    def release_key(self, key_val):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["in_use"] = False
                    break

    def disable_key(self, key_val):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["enabled"] = False
                    k["in_use"] = False
                    break

    def update_usage(self, key_val, usage):
        with self._lock:
            for k in self.keys:
                if k["key"] == key_val:
                    k["monthly_usage"] = usage
                    k["in_use"] = False
                    break

    def check_compression_count(self, key_data):
        try:
            resp = requests.post(
                "https://api.tinify.com/shrink",
                auth=("api", key_data["key"]),
                data=b"",
                headers={"Content-Type": "application/octet-stream"},
                timeout=10,
            )
            count = resp.headers.get("Compression-Count")
            if count is not None:
                return int(count)
        except:
            pass
        return None

    def refresh_all_usage(self):
        for k in self.keys:
            count = self.check_compression_count(k)
            if count is not None:
                k["monthly_usage"] = count

    def save(self, config):
        config["api_keys"] = self.keys
        save_config(config)

    @classmethod
    def from_config(cls, config):
        return cls(config.get("api_keys", []))


class AddKeyDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, key_data=None):
        super().__init__(parent)
        self.setWindowTitle("编辑密钥" if edit_mode else "添加密钥")
        self.setMinimumWidth(450)
        self.key_data = key_data

        layout = QFormLayout(self)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("输入 Tinify API Key")
        self.key_input.setEchoMode(QLineEdit.Password)
        if key_data:
            self.key_input.setText(key_data["key"])
        layout.addRow("API Key:", self.key_input)

        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("可选，用于区分不同密钥（如：工作、个人）")
        if key_data:
            self.remark_input.setText(key_data.get("remark", ""))
        layout.addRow("备注:", self.remark_input)

        self.limit_input = QSpinBox()
        self.limit_input.setRange(1, 10000)
        self.limit_input.setValue(key_data.get("monthly_limit", 500) if key_data else 500)
        self.limit_input.setSuffix(" 次/月")
        layout.addRow("每月额度:", self.limit_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def validate_and_accept(self):
        if not self.key_input.text().strip():
            QMessageBox.warning(self, "警告", "API Key 不能为空！")
            return
        if len(self.key_input.text().strip()) < 10:
            QMessageBox.warning(self, "警告", "API Key 格式似乎不正确，请检查！")
            return
        self.accept()

    def get_data(self):
        return {
            "key": self.key_input.text().strip(),
            "remark": self.remark_input.text().strip(),
            "monthly_limit": self.limit_input.value(),
        }


class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 压缩历史")
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["时间", "文件数", "成功", "失败", "原始大小", "压缩后大小"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)

        for record in reversed(history):
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(record.get("time", "")))
            table.setItem(row, 1, QTableWidgetItem(str(record.get("total", 0))))
            table.setItem(row, 2, QTableWidgetItem(str(record.get("success", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(record.get("fail", 0))))
            table.setItem(row, 4, QTableWidgetItem(format_size(record.get("original_size", 0))))
            table.setItem(row, 5, QTableWidgetItem(format_size(record.get("compressed_size", 0))))

        layout.addWidget(table)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


class CompressWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)
    key_usage_updated = pyqtSignal()

    def __init__(self, key_manager, file_paths, output_dir,
                 overwrite=False, target_format="", resize_params=None):
        super().__init__()
        self.key_manager = key_manager
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.target_format = target_format
        self.resize_params = resize_params
        self._is_cancelled = False
        self._completed = 0
        self._total = 0
        self._success_count = 0
        self._fail_count = 0
        self._total_original_size = 0
        self._total_compressed_size = 0
        self._stats_lock = threading.Lock()

    def cancel(self):
        self._is_cancelled = True

    def compress_image(self, api_key, image_data, target_mime="", resize_params=None):
        try:
            resp = requests.post(
                "https://api.tinify.com/shrink",
                data=image_data,
                auth=("api", api_key),
                headers={"Content-Type": "application/octet-stream"},
                timeout=120,
            )

            count = None
            if "Compression-Count" in resp.headers:
                count = int(resp.headers["Compression-Count"])

            if resp.status_code == 429:
                return False, None, count, "QUOTA_EXCEEDED"
            if resp.status_code == 401:
                return False, None, count, "INVALID_KEY"

            resp.raise_for_status()

            img_url = resp.headers["Location"]

            operations = {}
            if target_mime:
                operations["convert"] = {"type": [target_mime]}
            if resize_params:
                operations["resize"] = resize_params

            if operations:
                op_resp = requests.post(
                    img_url,
                    json=operations,
                    auth=("api", api_key),
                    timeout=120,
                )
                if op_resp.status_code == 429:
                    return False, None, count, "QUOTA_EXCEEDED"
                if op_resp.status_code == 401:
                    return False, None, count, "INVALID_KEY"
                op_resp.raise_for_status()
                if "Location" in op_resp.headers:
                    img_url = op_resp.headers["Location"]
                else:
                    return True, op_resp.content, count, None

            img_resp = requests.get(img_url, auth=("api", api_key), timeout=120)
            img_resp.raise_for_status()

            return True, img_resp.content, count, None

        except requests.exceptions.Timeout:
            return False, None, None, "TIMEOUT"
        except requests.exceptions.ConnectionError:
            return False, None, None, "NETWORK"
        except requests.exceptions.HTTPError as e:
            return False, None, None, f"HTTP_{e.response.status_code}"
        except Exception as e:
            return False, None, None, str(e)

    def process_one_file(self, file_path):
        supported_ext = SUPPORTED_EXTENSIONS
        target_mime = FORMATS.get(self.target_format, {}).get("mime", "")
        target_ext = FORMATS.get(self.target_format, {}).get("ext", "")
        pil_only = FORMATS.get(self.target_format, {}).get("pil_only", False)
        is_bmp = Path(file_path).suffix.lower() == ".bmp"

        if is_bmp and not target_ext and not pil_only:
            target_ext = ".png"
            target_mime = "image/png"

        if Path(file_path).suffix.lower() not in supported_ext:
            self.log.emit(f"⏭ 跳过不支持的类型: {file_path}", False)
            return None

        input_path = Path(file_path)
        output_name = input_path.stem + target_ext if target_ext else input_path.name
        if self.output_dir:
            output_path = Path(self.output_dir) / output_name
        else:
            output_path = input_path.parent / output_name

        if output_path.exists() and not self.overwrite:
            self.log.emit(f"⏭ 跳过已存在文件: {output_path}", False)
            return None

        try:
            original_size = os.path.getsize(file_path)
            if is_bmp:
                with Image.open(file_path) as img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    image_data = buf.getvalue()
            else:
                with open(file_path, "rb") as f:
                    image_data = f.read()
        except Exception as e:
            self.log.emit(f"❌ 读取文件失败: {file_path} - {e}", True)
            return {"success": False, "original_size": 0, "compressed_size": 0}

        max_attempts = max(len(self.key_manager.keys) * 2, 4)
        for attempt in range(max_attempts):
            if self._is_cancelled:
                return None

            key = self.key_manager.acquire_key()
            if key is None:
                if attempt == 0:
                    self.log.emit("❌ 没有可用的密钥（请添加有效的 API Key）", True)
                else:
                    self.log.emit(f"❌ 所有可用密钥额度已用完或无效: {input_path.name}", True)
                return {"success": False, "original_size": original_size, "compressed_size": 0}

            key_id = key.get("remark") or key["key"][:8]
            self.log.emit(f"🔄 [密钥:{key_id}] 正在压缩: {input_path.name}", False)

            actual_mime = "image/png" if pil_only else target_mime
            success, compressed_data, count, error = self.compress_image(
                key["key"], image_data, actual_mime, self.resize_params
            )

            if count is not None:
                self.key_manager.update_usage(key["key"], count)

            if success:
                try:
                    if pil_only:
                        from PIL import Image as PILImg
                        from io import BytesIO as ImgBytesIO
                        pil_img = PILImg.open(ImgBytesIO(compressed_data))
                        if self.target_format == "ico":
                            pil_img = pil_img.convert("RGBA")
                            pil_img.save(output_path, format="ICO", sizes=[(256, 256)])
                        elif self.target_format == "pdf":
                            pil_img = pil_img.convert("RGB")
                            pil_img.save(output_path, format="PDF", resolution=150.0)
                    else:
                        with open(output_path, "wb") as f:
                            f.write(compressed_data)
                except Exception as e:
                    self.log.emit(f"❌ 写入文件失败: {output_path} - {e}", True)
                    self.key_manager.release_key(key["key"])
                    return {"success": False, "original_size": original_size, "compressed_size": 0}

                compressed_size = os.path.getsize(output_path)
                saved = original_size - compressed_size
                saved_percent = (saved / original_size) * 100
                self.log.emit(
                    f"✅ {input_path.name} | {original_size//1024}KB → {compressed_size//1024}KB | 节省 {saved_percent:.1f}%",
                    False,
                )
                return {"success": True, "original_size": original_size, "compressed_size": compressed_size}
            else:
                error_msgs = {
                    "QUOTA_EXCEEDED": "本月额度已用完",
                    "INVALID_KEY": "密钥无效",
                    "TIMEOUT": "请求超时",
                    "NETWORK": "网络错误",
                    "HTTP_413": "图片超过大小限制",
                    "HTTP_415": "不支持的图片格式",
                }
                msg = error_msgs.get(error, error)

                if error in ("QUOTA_EXCEEDED", "INVALID_KEY"):
                    self.key_manager.disable_key(key["key"])
                    self.log.emit(f"⚠ [密钥:{key_id}] {msg}，尝试下一个...", True)
                elif error in ("TIMEOUT", "NETWORK"):
                    self.key_manager.release_key(key["key"])
                    self.log.emit(f"⚠ [密钥:{key_id}] {msg}，重试中({attempt+1}/{max_attempts})...", True)
                    time.sleep(1)
                else:
                    self.key_manager.release_key(key["key"])
                    self.log.emit(f"❌ [密钥:{key_id}] {msg}", True)
                    return {"success": False, "original_size": original_size, "compressed_size": 0}

        return {"success": False, "original_size": original_size, "compressed_size": 0}

    def run(self):
        self._total = len(self.file_paths)
        self._completed = 0
        self._success_count = 0
        self._fail_count = 0
        self._total_original_size = 0
        self._total_compressed_size = 0

        available_keys = self.key_manager.get_available_keys()
        num_workers = max(1, min(len(available_keys), 3, len(self.file_paths)))

        if num_workers <= 1:
            for fp in self.file_paths:
                if self._is_cancelled:
                    self.log.emit("⚠ 用户取消了压缩任务", False)
                    break
                result = self.process_one_file(fp)
                if result is None:
                    pass
                elif result.get("success"):
                    self._success_count += 1
                    self._total_original_size += result["original_size"]
                    self._total_compressed_size += result["compressed_size"]
                else:
                    self._fail_count += 1

                self._completed += 1
                self.progress.emit(self._completed, self._total)
                self.key_usage_updated.emit()
        else:
            self.log.emit(f"🚀 启用 {num_workers} 个并发线程进行压缩", False)

            def safe_process(fp):
                if self._is_cancelled:
                    return None
                return self.process_one_file(fp)

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(safe_process, fp): fp for fp in self.file_paths}
                for future in as_completed(futures):
                    if self._is_cancelled:
                        self.log.emit("⚠ 用户取消了压缩任务", False)
                        for f in futures:
                            f.cancel()
                        break
                    result = future.result()
                    if result is None:
                        pass
                    elif result.get("success"):
                        self._success_count += 1
                        self._total_original_size += result["original_size"]
                        self._total_compressed_size += result["compressed_size"]
                    else:
                        self._fail_count += 1

                    self._completed += 1
                    self.progress.emit(self._completed, self._total)
                    self.key_usage_updated.emit()

        stats = {
            "total": self._total,
            "success": self._success_count,
            "fail": self._fail_count,
            "original_size": self._total_original_size,
            "compressed_size": self._total_compressed_size,
        }
        self.finished_signal.emit(stats)


class WatermarkWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, file_paths, output_dir, overwrite,
                 watermark_type, watermark_image_path,
                 watermark_text, font_path, font_size, font_color,
                 x_ratio, y_ratio, opacity, scale, margin_x, margin_y):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.watermark_type = watermark_type
        self.watermark_image_path = watermark_image_path
        self.watermark_text = watermark_text
        self.font_path = font_path
        self.font_size = font_size
        self.font_color = font_color
        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.opacity = opacity
        self.scale = scale
        self.margin_x = margin_x
        self.margin_y = margin_y
        self._is_cancelled = False
        self._loaded_wm_image = None

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.file_paths)
        success = 0
        fail = 0
        total_original = 0
        total_compressed = 0

        if self.watermark_type in ("image", "both") and self.watermark_image_path:
            try:
                self._loaded_wm_image = Image.open(self.watermark_image_path)
            except Exception as e:
                self.log.emit(f"❌ 无法加载水印图片: {self.watermark_image_path} - {e}", True)
                self.finished_signal.emit({"total": total, "success": 0, "fail": total,
                                           "original_size": 0, "compressed_size": 0})
                return

        for idx, fp in enumerate(self.file_paths):
            if self._is_cancelled:
                self.log.emit("⚠ 用户取消了水印任务", False)
                break

            self.log.emit(f"🔄 处理中: {Path(fp).name}", False)
            try:
                original_size = os.path.getsize(fp)
                ext = Path(fp).suffix.lower()
                if ext in (".ico", ".pdf"):
                    self.log.emit(f"⏭ 跳过不支持格式: {Path(fp).name}", False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                with Image.open(fp) as img:
                    result = apply_watermark_to_image(
                        img, self.watermark_type, self._loaded_wm_image,
                        self.watermark_text, self.font_path, self.font_size,
                        self.font_color, self.x_ratio, self.y_ratio,
                        self.opacity, self.scale, self.margin_x, self.margin_y,
                    )

                if self.output_dir:
                    out_path = Path(self.output_dir) / Path(fp).name
                elif self.overwrite:
                    out_path = Path(fp)
                else:
                    stem = Path(fp).stem
                    ext = Path(fp).suffix
                    out_path = Path(fp).parent / f"{stem}_watermarked{ext}"

                if out_path.exists() and not self.overwrite:
                    self.log.emit(f"⏭ 跳过已存在文件: {out_path.name}", False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                result.save(out_path, quality=95)
                compressed_size = os.path.getsize(out_path)
                total_original += original_size
                total_compressed += compressed_size
                success += 1
                self.log.emit(f"✅ {Path(fp).name} | 水印添加完成", False)

            except Exception as e:
                self.log.emit(f"❌ 处理失败: {Path(fp).name} - {e}", True)
                fail += 1

            self.progress.emit(idx + 1, total)

        self.finished_signal.emit({
            "total": total, "success": success, "fail": fail,
            "original_size": total_original, "compressed_size": total_compressed,
        })


class RenameWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, file_paths, pattern, start_index, pad_digits, date_format):
        super().__init__()
        self.file_paths = file_paths
        self.pattern = pattern
        self.start_index = start_index
        self.pad_digits = pad_digits
        self.date_format = date_format
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.file_paths)
        success = 0
        fail = 0
        today = datetime.now().strftime(self.date_format)

        for i, fp in enumerate(self.file_paths):
            if self._is_cancelled:
                self.log.emit("⚠ 用户取消了重命名任务", False)
                break

            p = Path(fp)
            name = p.stem
            ext = p.suffix
            parent = p.parent

            new_name = self.pattern
            new_name = new_name.replace("{name}", name)
            new_name = new_name.replace("{index}", str(self.start_index + i).zfill(self.pad_digits))
            new_name = new_name.replace("{date}", today)
            new_name += ext

            new_path = parent / new_name

            if new_path.exists() and new_path.resolve() != p.resolve():
                self.log.emit(f"⏭ 目标文件已存在: {new_name}", False)
                fail += 1
                self.progress.emit(i + 1, total)
                continue

            try:
                os.rename(fp, str(new_path))
                self.log.emit(f"✅ {p.name} → {new_name}", False)
                success += 1
            except Exception as e:
                self.log.emit(f"❌ 重命名失败: {p.name} - {e}", True)
                fail += 1

            self.progress.emit(i + 1, total)

        self.finished_signal.emit({
            "total": total, "success": success, "fail": fail,
            "original_size": 0, "compressed_size": 0,
        })


class PositionPreviewWidget(QWidget):
    positionChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 280)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: 1px solid #bbb; background: #f5f5f5;")

        self._base_pixmap = None
        self._wm_pixmap = None
        self._wm_x_ratio = 0.85
        self._wm_y_ratio = 0.85
        self._wm_opacity = 0.8
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._img_rect = None

    def set_base_image(self, pixmap):
        self._base_pixmap = pixmap
        self._calc_image_rect()
        self.update()

    def set_watermark(self, pixmap):
        self._wm_pixmap = pixmap
        self.update()

    def set_opacity(self, val):
        self._wm_opacity = val / 100.0
        self.update()

    def set_position_ratio(self, x_ratio, y_ratio):
        self._wm_x_ratio = max(0.0, min(1.0, x_ratio))
        self._wm_y_ratio = max(0.0, min(1.0, y_ratio))
        self.positionChanged.emit(self._wm_x_ratio, self._wm_y_ratio)
        self.update()

    def get_position_ratio(self):
        return (self._wm_x_ratio, self._wm_y_ratio)

    def _calc_image_rect(self):
        if not self._base_pixmap or self._base_pixmap.isNull():
            self._img_rect = None
            return
        w = self.width() - 4
        h = self.height() - 4
        pw = self._base_pixmap.width()
        ph = self._base_pixmap.height()
        scale = min(w / pw, h / ph)
        dw = int(pw * scale)
        dh = int(ph * scale)
        dx = (self.width() - dw) // 2
        dy = (self.height() - dh) // 2
        self._img_rect = QRect(dx, dy, dw, dh)

    def _wm_display_rect(self):
        if self._img_rect is None or not self._wm_pixmap or self._wm_pixmap.isNull():
            return None
        wm_w = self._wm_pixmap.width()
        wm_h = self._wm_pixmap.height()
        avail_w = max(1, self._img_rect.width() - wm_w)
        avail_h = max(1, self._img_rect.height() - wm_h)
        x = self._img_rect.x() + int(self._wm_x_ratio * avail_w)
        y = self._img_rect.y() + int(self._wm_y_ratio * avail_h)
        return QRect(x, y, wm_w, wm_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        if self._base_pixmap and not self._base_pixmap.isNull():
            if self._img_rect is None:
                self._calc_image_rect()
            if self._img_rect:
                scaled = self._base_pixmap.scaled(
                    self._img_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                painter.drawPixmap(self._img_rect.topLeft(), scaled)
        else:
            painter.fillRect(0, 0, w, h, QColor(245, 245, 245))
            painter.setPen(QColor(180, 180, 180))
            f = painter.font()
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(self.rect(), Qt.AlignCenter, "添加图片后可预览位置")

        if self._wm_pixmap and not self._wm_pixmap.isNull() and self._img_rect:
            wm_rect = self._wm_display_rect()
            if wm_rect:
                painter.setOpacity(self._wm_opacity)
                painter.drawPixmap(wm_rect.topLeft(), self._wm_pixmap)
                painter.setOpacity(1.0)
                pen = QPen(QColor(30, 100, 200), 1, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(wm_rect)

        painter.end()

    def resizeEvent(self, event):
        self._calc_image_rect()
        super().resizeEvent(event)

    def _hit_test_wm(self, pos):
        wm_rect = self._wm_display_rect()
        if wm_rect and wm_rect.contains(pos):
            return True
        return False

    def _pos_to_ratio(self, screen_x, screen_y):
        if self._img_rect is None:
            return (self._wm_x_ratio, self._wm_y_ratio)
        wm_w = self._wm_pixmap.width() if self._wm_pixmap else 1
        wm_h = self._wm_pixmap.height() if self._wm_pixmap else 1
        wm_x = screen_x - self._drag_offset_x
        wm_y = screen_y - self._drag_offset_y
        avail_w = max(1, self._img_rect.width() - wm_w)
        avail_h = max(1, self._img_rect.height() - wm_h)
        rx = (wm_x - self._img_rect.x()) / avail_w
        ry = (wm_y - self._img_rect.y()) / avail_h
        return (max(0.0, min(1.0, rx)), max(0.0, min(1.0, ry)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._hit_test_wm(event.pos()):
                self._dragging = True
                wm_rect = self._wm_display_rect()
                if wm_rect:
                    self._drag_offset_x = event.pos().x() - wm_rect.x()
                    self._drag_offset_y = event.pos().y() - wm_rect.y()
                self.setCursor(Qt.ClosedHandCursor)
            elif self._img_rect and self._img_rect.contains(event.pos()) and self._wm_pixmap \
                    and not self._wm_pixmap.isNull():
                self._dragging = True
                self._drag_offset_x = self._wm_pixmap.width() // 2
                self._drag_offset_y = self._wm_pixmap.height() // 2
                rx, ry = self._pos_to_ratio(event.pos().x(), event.pos().y())
                self._wm_x_ratio = rx
                self._wm_y_ratio = ry
                self.positionChanged.emit(rx, ry)
                self.update()
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            rx, ry = self._pos_to_ratio(event.pos().x(), event.pos().y())
            if abs(rx - self._wm_x_ratio) > 0.001 or abs(ry - self._wm_y_ratio) > 0.001:
                self._wm_x_ratio = rx
                self._wm_y_ratio = ry
                self.positionChanged.emit(rx, ry)
                self.update()
        else:
            if self._hit_test_wm(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            elif self._img_rect and self._img_rect.contains(event.pos()):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            if self._hit_test_wm(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🐼 TinyJPG 批量压缩助手")
        self.setMinimumSize(900, 700)

        self.worker = None
        self.config = load_config()
        self.key_manager = KeyManager.from_config(self.config)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(140)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background: #2c3e50;
                color: #ecf0f1;
                border: none;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 14px 12px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #34495e;
            }
        """)
        self.sidebar.addItem("📁  压缩任务")
        self.sidebar.addItem("💧  水印工具")
        self.sidebar.addItem("📝  批量重命名")
        self.sidebar.addItem("🔑  密钥管理")
        self.sidebar.addItem("📊  压缩历史")
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)

        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_compression_page())  # 0
        self.stack.addWidget(self.build_watermark_page())    # 1
        self.stack.addWidget(self.build_rename_page())       # 2
        self.stack.addWidget(self.build_key_page())          # 3
        self.stack.addWidget(self.build_history_page())      # 4
        root.addWidget(self.stack, 1)

    def build_compression_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        output_group = QGroupBox("📁 输出设置")
        output_layout = QVBoxLayout(output_group)

        row1 = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("留空则覆盖原文件")
        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        self.overwrite_checkbox = QCheckBox("覆盖已存在的文件")
        row1.addWidget(QLabel("输出目录:"))
        row1.addWidget(self.output_dir_input)
        row1.addWidget(self.browse_output_btn)
        row1.addWidget(self.overwrite_checkbox)
        output_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        for key, fmt in FORMATS.items():
            self.format_combo.addItem(fmt["label"], key)
        self.format_combo.setCurrentText(FORMATS[DEFAULT_FORMAT]["label"])
        row2.addWidget(self.format_combo)

        row2.addSpacing(16)
        self.resize_checkbox = QCheckBox("调整尺寸")
        self.resize_checkbox.toggled.connect(self.on_resize_toggled)
        row2.addWidget(self.resize_checkbox)

        row2.addWidget(QLabel("方法:"))
        self.resize_method_combo = QComboBox()
        for key, label in RESIZE_METHODS.items():
            self.resize_method_combo.addItem(label.split(" —")[0], key)
        self.resize_method_combo.setCurrentIndex(0)
        row2.addWidget(self.resize_method_combo)

        self.resize_width_input = QSpinBox()
        self.resize_width_input.setRange(0, 10000)
        self.resize_width_input.setValue(0)
        self.resize_width_input.setSpecialValueText("自动")
        self.resize_width_input.setSuffix(" px")
        row2.addWidget(QLabel("宽:"))
        row2.addWidget(self.resize_width_input)

        self.resize_height_input = QSpinBox()
        self.resize_height_input.setRange(0, 10000)
        self.resize_height_input.setValue(0)
        self.resize_height_input.setSpecialValueText("自动")
        self.resize_height_input.setSuffix(" px")
        row2.addWidget(QLabel("高:"))
        row2.addWidget(self.resize_height_input)

        for w in [self.resize_method_combo, self.resize_width_input,
                  self.resize_height_input]:
            w.setEnabled(False)

        row2.addStretch()
        output_layout.addLayout(row2)
        layout.addWidget(output_group)

        splitter = QSplitter(Qt.Vertical)

        file_group = QGroupBox("📋 待压缩图片列表")
        file_layout = QVBoxLayout(file_group)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setDragEnabled(True)
        self.file_list_widget.setAcceptDrops(True)
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        file_layout.addWidget(self.file_list_widget)

        info_bar = QHBoxLayout()
        self.file_count_label = QLabel("共 0 个文件")
        self.file_total_size_label = QLabel("")
        info_bar.addWidget(self.file_count_label)
        info_bar.addWidget(self.file_total_size_label)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.add_files_btn = QPushButton("📎 添加图片")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn = QPushButton("📁 添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_selected_btn = QPushButton("🗑 移除选中")
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.clear_all_btn = QPushButton("清空列表")
        self.clear_all_btn.clicked.connect(self.clear_all)
        btn_bar.addWidget(self.add_files_btn)
        btn_bar.addWidget(self.add_folder_btn)
        btn_bar.addWidget(self.remove_selected_btn)
        btn_bar.addWidget(self.clear_all_btn)
        file_layout.addLayout(btn_bar)

        splitter.addWidget(file_group)

        log_group = QGroupBox("📝 压缩日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        splitter.addWidget(log_group)
        splitter.setSizes([350, 180])

        layout.addWidget(splitter, 1)

        ctrl = QHBoxLayout()
        self.compress_btn = QPushButton("🚀 开始压缩")
        self.compress_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self.cancel_btn = QPushButton("⏹ 取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px 16px;")
        self.compress_btn.clicked.connect(self.start_compress)
        self.cancel_btn.clicked.connect(self.cancel_compress)
        ctrl.addWidget(self.compress_btn)
        ctrl.addWidget(self.cancel_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return page

    def build_watermark_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # ── Settings group ──
        settings_group = QGroupBox("💧 水印设置")
        settings_layout = QVBoxLayout(settings_group)

        # Type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("类型:"))
        self.wm_type_group = QButtonGroup(self)
        self.wm_type_image = QRadioButton("图片水印")
        self.wm_type_text = QRadioButton("文字水印")
        self.wm_type_both = QRadioButton("图片+文字")
        self.wm_type_group.addButton(self.wm_type_image, 0)
        self.wm_type_group.addButton(self.wm_type_text, 1)
        self.wm_type_group.addButton(self.wm_type_both, 2)
        self.wm_type_group.buttonClicked.connect(self.on_wm_type_changed)
        self.wm_type_image.setChecked(True)
        type_layout.addWidget(self.wm_type_image)
        type_layout.addWidget(self.wm_type_text)
        type_layout.addWidget(self.wm_type_both)
        type_layout.addStretch()
        settings_layout.addLayout(type_layout)

        # Image watermark row
        self.wm_image_row = QWidget()
        wm_img_layout = QHBoxLayout(self.wm_image_row)
        wm_img_layout.setContentsMargins(0, 0, 0, 0)
        wm_img_layout.addWidget(QLabel("水印图片:"))
        self.wm_image_path_input = QLineEdit()
        self.wm_image_path_input.setPlaceholderText("选择 PNG/图片作为水印...")
        wm_img_layout.addWidget(self.wm_image_path_input)
        self.wm_image_browse_btn = QPushButton("浏览...")
        self.wm_image_browse_btn.clicked.connect(self.on_wm_browse_image)
        wm_img_layout.addWidget(self.wm_image_browse_btn)
        self.wm_image_preview = QLabel()
        self.wm_image_preview.setFixedSize(48, 48)
        self.wm_image_preview.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        wm_img_layout.addWidget(self.wm_image_preview)
        settings_layout.addWidget(self.wm_image_row)

        # Text watermark row
        self.wm_text_row = QWidget()
        self.wm_text_row.setVisible(False)
        wm_txt_layout = QHBoxLayout(self.wm_text_row)
        wm_txt_layout.setContentsMargins(0, 0, 0, 0)
        wm_txt_layout.addWidget(QLabel("文字内容:"))
        self.wm_text_input = QLineEdit()
        self.wm_text_input.setPlaceholderText("输入水印文字...")
        self.wm_text_input.textChanged.connect(self._rebuild_wm_preview)
        wm_txt_layout.addWidget(self.wm_text_input)
        self.wm_font_btn = QPushButton("选择字体...")
        self.wm_font_btn.clicked.connect(self.on_wm_select_font)
        wm_txt_layout.addWidget(self.wm_font_btn)
        self.wm_font_size_spin = QSpinBox()
        self.wm_font_size_spin.setRange(8, 500)
        self.wm_font_size_spin.setValue(48)
        self.wm_font_size_spin.setSuffix(" px")
        self.wm_font_size_spin.valueChanged.connect(self._rebuild_wm_preview)
        wm_txt_layout.addWidget(QLabel("字号:"))
        wm_txt_layout.addWidget(self.wm_font_size_spin)
        self.wm_color_btn = QPushButton()
        self.wm_color_btn.setFixedSize(28, 28)
        self.wm_color_btn.setStyleSheet("background-color: white; border: 1px solid #999;")
        self.wm_color_btn.clicked.connect(self.on_wm_select_color)
        wm_txt_layout.addWidget(self.wm_color_btn)
        settings_layout.addWidget(self.wm_text_row)

        # Position preview
        self.wm_position_preview = PositionPreviewWidget()
        self.wm_position_preview.positionChanged.connect(self._on_wm_position_changed)
        settings_layout.addWidget(self.wm_position_preview, alignment=Qt.AlignCenter)

        # Controls row (margin, opacity, scale)
        controls_row = QHBoxLayout()

        controls_row.addWidget(QLabel("边距 X:"))
        self.wm_margin_x = QSpinBox()
        self.wm_margin_x.setRange(0, 500)
        self.wm_margin_x.setValue(20)
        self.wm_margin_x.setSuffix(" px")
        self.wm_margin_x.valueChanged.connect(self._rebuild_wm_preview)
        self.wm_margin_x.valueChanged.connect(self._on_wm_margin_changed)
        controls_row.addWidget(self.wm_margin_x)

        controls_row.addSpacing(12)
        controls_row.addWidget(QLabel("Y:"))
        self.wm_margin_y = QSpinBox()
        self.wm_margin_y.setRange(0, 500)
        self.wm_margin_y.setValue(20)
        self.wm_margin_y.setSuffix(" px")
        self.wm_margin_y.valueChanged.connect(self._rebuild_wm_preview)
        self.wm_margin_y.valueChanged.connect(self._on_wm_margin_changed)
        controls_row.addWidget(self.wm_margin_y)

        controls_row.addSpacing(20)
        controls_row.addWidget(QLabel("透明度:"))
        self.wm_opacity_slider = QSlider(Qt.Horizontal)
        self.wm_opacity_slider.setRange(1, 100)
        self.wm_opacity_slider.setValue(80)
        self.wm_opacity_slider.setFixedWidth(120)
        self.wm_opacity_slider.valueChanged.connect(self.on_wm_opacity_changed)
        controls_row.addWidget(self.wm_opacity_slider)
        self.wm_opacity_label = QLabel("80%")
        self.wm_opacity_label.setFixedWidth(35)
        controls_row.addWidget(self.wm_opacity_label)

        controls_row.addSpacing(20)
        controls_row.addWidget(QLabel("缩放:"))
        self.wm_scale_spin = QSpinBox()
        self.wm_scale_spin.setRange(1, 100)
        self.wm_scale_spin.setValue(15)
        self.wm_scale_spin.setSuffix(" %")
        self.wm_scale_spin.valueChanged.connect(self._rebuild_wm_preview)
        controls_row.addWidget(self.wm_scale_spin)

        controls_row.addStretch()
        settings_layout.addLayout(controls_row)

        # Output settings
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.wm_output_dir = QLineEdit()
        self.wm_output_dir.setPlaceholderText("留空则覆盖原文件")
        output_layout.addWidget(self.wm_output_dir)
        self.wm_output_browse = QPushButton("浏览...")
        self.wm_output_browse.clicked.connect(self.on_wm_browse_output)
        output_layout.addWidget(self.wm_output_browse)
        self.wm_overwrite = QCheckBox("覆盖原文件")
        output_layout.addWidget(self.wm_overwrite)
        output_layout.addStretch()
        settings_layout.addLayout(output_layout)

        layout.addWidget(settings_group)

        # ── File list ──
        file_group = QGroupBox("📋 待处理图片列表")
        file_layout = QVBoxLayout(file_group)
        self.wm_file_list = QListWidget()
        self.wm_file_list.setAcceptDrops(True)
        self.wm_file_list.setDragEnabled(True)
        self.wm_file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.wm_file_list.setDragDropMode(QAbstractItemView.InternalMove)
        file_layout.addWidget(self.wm_file_list)

        info_bar = QHBoxLayout()
        self.wm_file_count = QLabel("共 0 个文件")
        info_bar.addWidget(self.wm_file_count)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.wm_add_btn = QPushButton("📎 添加图片")
        self.wm_add_btn.clicked.connect(self.on_wm_add_files)
        self.wm_remove_btn = QPushButton("🗑 移除选中")
        self.wm_remove_btn.clicked.connect(self.on_wm_remove_selected)
        self.wm_clear_btn = QPushButton("清空列表")
        self.wm_clear_btn.clicked.connect(self.on_wm_clear)
        btn_bar.addWidget(self.wm_add_btn)
        btn_bar.addWidget(self.wm_remove_btn)
        btn_bar.addWidget(self.wm_clear_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)
        layout.addWidget(file_group, 1)

        # ── Buttons ──
        ctrl = QHBoxLayout()
        self.wm_start_btn = QPushButton("🚀 开始添加水印")
        self.wm_start_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self.wm_cancel_btn = QPushButton("⏹ 取消")
        self.wm_cancel_btn.setEnabled(False)
        self.wm_cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px 16px;")
        self.wm_start_btn.clicked.connect(self.on_wm_start)
        self.wm_cancel_btn.clicked.connect(self.on_wm_cancel)
        ctrl.addWidget(self.wm_start_btn)
        ctrl.addWidget(self.wm_cancel_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.wm_progress = QProgressBar()
        self.wm_progress.setVisible(False)
        layout.addWidget(self.wm_progress)

        self.wm_log = QTextEdit()
        self.wm_log.setReadOnly(True)
        self.wm_log.setFont(QFont("Consolas", 9))
        self.wm_log.setMaximumHeight(160)
        layout.addWidget(self.wm_log)

        # Init font state
        self.wm_font_family = "微软雅黑"
        self.wm_font_color = (255, 255, 255)

        return page

    def build_rename_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # ── Settings ──
        settings_group = QGroupBox("📝 重命名规则")
        settings_layout = QVBoxLayout(settings_group)

        # Pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("命名模式:"))
        self.rn_pattern_input = QLineEdit()
        self.rn_pattern_input.setPlaceholderText('例如: product_{index} 或 {name}_{index}')
        self.rn_pattern_input.textChanged.connect(self.on_rn_preview)
        pattern_layout.addWidget(self.rn_pattern_input)
        settings_layout.addLayout(pattern_layout)

        # Variable insert buttons
        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("插入变量:"))
        self.rn_ins_name = QPushButton("{name}")
        self.rn_ins_name.clicked.connect(lambda: self.rn_insert_var("{name}"))
        self.rn_ins_index = QPushButton("{index}")
        self.rn_ins_index.clicked.connect(lambda: self.rn_insert_var("{index}"))
        self.rn_ins_date = QPushButton("{date}")
        self.rn_ins_date.clicked.connect(lambda: self.rn_insert_var("{date}"))
        var_layout.addWidget(self.rn_ins_name)
        var_layout.addWidget(self.rn_ins_index)
        var_layout.addWidget(self.rn_ins_date)
        var_layout.addStretch()
        settings_layout.addLayout(var_layout)

        # Hint
        hint = QLabel("提示: {name}=原文件名  {index}=序号  {date}=当前日期")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        settings_layout.addWidget(hint)

        # Numeric options
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("起始序号:"))
        self.rn_start_index = QSpinBox()
        self.rn_start_index.setRange(0, 999999)
        self.rn_start_index.setValue(1)
        self.rn_start_index.valueChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_start_index)

        num_layout.addSpacing(12)
        num_layout.addWidget(QLabel("数字位数:"))
        self.rn_pad_digits = QSpinBox()
        self.rn_pad_digits.setRange(1, 10)
        self.rn_pad_digits.setValue(3)
        self.rn_pad_digits.valueChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_pad_digits)
        num_layout.addWidget(QLabel(" (001)"))

        num_layout.addSpacing(12)
        num_layout.addWidget(QLabel("日期格式:"))
        self.rn_date_format = QComboBox()
        self.rn_date_format.addItem("YYYYMMDD", "%Y%m%d")
        self.rn_date_format.addItem("YYYY-MM-DD", "%Y-%m-%d")
        self.rn_date_format.addItem("YYMMDD", "%y%m%d")
        self.rn_date_format.currentIndexChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_date_format)

        num_layout.addStretch()
        settings_layout.addLayout(num_layout)

        layout.addWidget(settings_group)

        # ── File list (table with preview) ──
        file_group = QGroupBox("📋 文件列表")
        file_layout = QVBoxLayout(file_group)

        self.rn_file_table = QTableWidget()
        self.rn_file_table.setColumnCount(3)
        self.rn_file_table.setHorizontalHeaderLabels(["原文件名", "→ 新文件名", "路径"])
        self.rn_file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rn_file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rn_file_table.setColumnHidden(2, True)  # hidden path column
        self.rn_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rn_file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.rn_file_table.verticalHeader().setVisible(False)
        self.rn_file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        file_layout.addWidget(self.rn_file_table)

        info_bar = QHBoxLayout()
        self.rn_file_count = QLabel("共 0 个文件")
        info_bar.addWidget(self.rn_file_count)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.rn_add_btn = QPushButton("📎 添加文件")
        self.rn_add_btn.clicked.connect(self.on_rn_add_files)
        self.rn_folder_btn = QPushButton("📁 添加文件夹")
        self.rn_folder_btn.clicked.connect(self.on_rn_add_folder)
        self.rn_remove_btn = QPushButton("🗑 移除选中")
        self.rn_remove_btn.clicked.connect(self.on_rn_remove_selected)
        self.rn_clear_btn = QPushButton("清空列表")
        self.rn_clear_btn.clicked.connect(self.on_rn_clear)
        btn_bar.addWidget(self.rn_add_btn)
        btn_bar.addWidget(self.rn_folder_btn)
        btn_bar.addWidget(self.rn_remove_btn)
        btn_bar.addWidget(self.rn_clear_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)

        layout.addWidget(file_group, 1)

        # ── Buttons ──
        ctrl = QHBoxLayout()
        self.rn_start_btn = QPushButton("🚀 开始重命名")
        self.rn_start_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self.rn_start_btn.clicked.connect(self.on_rn_start)
        ctrl.addWidget(self.rn_start_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.rn_progress = QProgressBar()
        self.rn_progress.setVisible(False)
        layout.addWidget(self.rn_progress)

        self.rn_log = QTextEdit()
        self.rn_log.setReadOnly(True)
        self.rn_log.setFont(QFont("Consolas", 9))
        self.rn_log.setMaximumHeight(160)
        layout.addWidget(self.rn_log)

        return page

    def build_key_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.key_table = QTableWidget()
        self.key_table.setColumnCount(4)
        self.key_table.setHorizontalHeaderLabels(["备注", "密钥", "已用/限额", "状态"])
        self.key_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.key_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.key_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.key_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.key_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.key_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.key_table.verticalHeader().setVisible(False)
        self.key_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.key_table, 1)

        btn_layout = QHBoxLayout()
        self.add_key_btn = QPushButton("➕ 添加密钥")
        self.add_key_btn.clicked.connect(self.add_key_dialog)
        self.edit_key_btn = QPushButton("✏️ 编辑密钥")
        self.edit_key_btn.clicked.connect(self.edit_key_dialog)
        self.remove_key_btn = QPushButton("🗑 删除密钥")
        self.remove_key_btn.clicked.connect(self.remove_key)
        self.toggle_key_btn = QPushButton("⏸ 禁用/启用")
        self.toggle_key_btn.clicked.connect(self.toggle_key)
        self.refresh_quota_btn = QPushButton("🔄 刷新额度")
        self.refresh_quota_btn.clicked.connect(self.refresh_quota)

        btn_layout.addWidget(self.add_key_btn)
        btn_layout.addWidget(self.edit_key_btn)
        btn_layout.addWidget(self.remove_key_btn)
        btn_layout.addWidget(self.toggle_key_btn)
        btn_layout.addWidget(self.refresh_quota_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.key_status_label = QLabel("")
        layout.addWidget(self.key_status_label)

        return page

    def build_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["时间", "文件数", "成功", "失败", "原始大小", "压缩后大小"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.history_table, 1)

        btn_bar = QHBoxLayout()
        self.refresh_history_btn = QPushButton("🔄 刷新")
        self.refresh_history_btn.clicked.connect(self.refresh_history_table)
        self.clear_history_btn = QPushButton("🗑 清空历史")
        self.clear_history_btn.clicked.connect(self.clear_history)
        btn_bar.addWidget(self.refresh_history_btn)
        btn_bar.addWidget(self.clear_history_btn)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        return page

    # ── Watermark handlers ──

    def on_wm_type_changed(self, btn):
        wm_type = self.wm_type_group.id(btn)
        self.wm_image_row.setVisible(wm_type in (0, 2))
        self.wm_text_row.setVisible(wm_type in (1, 2))
        self._rebuild_wm_preview()

    def on_wm_browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;所有文件 (*.*)"
        )
        if path:
            self.wm_image_path_input.setText(path)
            pixmap = QPixmap(path)
            self.wm_image_preview.setPixmap(
                pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self._rebuild_wm_preview()

    def on_wm_select_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.wm_font_family = font.family()
            self.wm_font_btn.setText(f"字体: {font.family()}")
            self.wm_font_size_spin.setValue(font.pointSize())
            self._rebuild_wm_preview()

    def on_wm_select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.wm_font_color = (color.red(), color.green(), color.blue())
            self.wm_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #999;"
            )
            self._rebuild_wm_preview()

    def on_wm_opacity_changed(self, val):
        self.wm_opacity_label.setText(f"{val}%")
        self.wm_position_preview.set_opacity(val)

    def _on_wm_position_changed(self, x_ratio, y_ratio):
        pass

    def _on_wm_margin_changed(self):
        pass

    def on_wm_browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.wm_output_dir.setText(dir_path)

    def on_wm_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.webp *.gif *.tiff *.tif *.bmp *.avif);;所有文件 (*.*)",
        )
        for f in files:
            self._wm_add_item(f)
        self._wm_update_count()
        self._wm_update_preview()

    def _wm_add_item(self, file_path):
        if not os.path.isfile(file_path):
            return
        for i in range(self.wm_file_list.count()):
            if self.wm_file_list.item(i).data(Qt.UserRole) == file_path:
                return
        size = os.path.getsize(file_path)
        item = QListWidgetItem(f"{Path(file_path).name}  ({format_size(size)})")
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)
        self.wm_file_list.addItem(item)

    def on_wm_remove_selected(self):
        for item in self.wm_file_list.selectedItems():
            self.wm_file_list.takeItem(self.wm_file_list.row(item))
        self._wm_update_count()
        self._wm_update_preview()

    def on_wm_clear(self):
        self.wm_file_list.clear()
        self._wm_update_count()
        self._wm_update_preview()

    def _wm_update_count(self):
        self.wm_file_count.setText(f"共 {self.wm_file_list.count()} 个文件")

    def _wm_update_preview(self):
        if self.wm_file_list.count() > 0:
            fp = self.wm_file_list.item(0).data(Qt.UserRole)
            if fp and os.path.isfile(fp):
                pixmap = QPixmap(fp)
                if not pixmap.isNull():
                    self.wm_position_preview.set_base_image(pixmap)
                    self._rebuild_wm_preview()
                    return
        self.wm_position_preview.set_base_image(QPixmap())
        self._rebuild_wm_preview()

    def _rebuild_wm_preview(self):
        wm_type_id = self.wm_type_group.checkedId()
        type_map = {0: "image", 1: "text", 2: "both"}
        wm_type = type_map.get(wm_type_id, "image")

        scale_pct = self.wm_scale_spin.value()
        pw = self.wm_position_preview

        disp_wm_w = max(10, int((pw.width() - 4) * scale_pct / 100))

        wm_pil = None

        if wm_type in ("image", "both"):
            img_path = self.wm_image_path_input.text().strip()
            if img_path and os.path.isfile(img_path):
                try:
                    wm_img = Image.open(img_path)
                    if wm_img.mode != 'RGBA':
                        wm_img = wm_img.convert('RGBA')
                    wm_h = max(1, int(wm_img.height * disp_wm_w / wm_img.width))
                    wm_img = wm_img.resize((disp_wm_w, wm_h), Image.LANCZOS)
                    wm_pil = wm_img
                except:
                    pass

        if wm_type in ("text", "both"):
            text = self.wm_text_input.text().strip()
            if text:
                font_path = find_font_path(self.wm_font_family)
                disp_font_size = min(50, max(8, self.wm_font_size_spin.value() // 2))
                txt_pil = render_text_watermark(text, font_path, disp_font_size, self.wm_font_color)
                if wm_pil is not None:
                    combined_w = max(wm_pil.width, txt_pil.width)
                    combined_h = wm_pil.height + 5 + txt_pil.height
                    combined = Image.new('RGBA', (combined_w, combined_h), (0, 0, 0, 0))
                    combined.paste(wm_pil, ((combined_w - wm_pil.width) // 2, 0), wm_pil)
                    combined.paste(txt_pil, ((combined_w - txt_pil.width) // 2, wm_pil.height + 5), txt_pil)
                    wm_pil = combined
                else:
                    wm_pil = txt_pil

        if wm_pil:
            buffer = BytesIO()
            wm_pil.save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            pw.set_watermark(pixmap)
        else:
            pw.set_watermark(QPixmap())

    def _wm_get_paths(self):
        paths = []
        for i in range(self.wm_file_list.count()):
            fp = self.wm_file_list.item(i).data(Qt.UserRole)
            if fp:
                paths.append(fp)
        return paths

    def on_wm_start(self):
        paths = self._wm_get_paths()
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加要处理的图片！")
            return

        wm_type_id = self.wm_type_group.checkedId()
        type_map = {0: "image", 1: "text", 2: "both"}
        wm_type = type_map.get(wm_type_id, "image")

        if wm_type in ("image", "both") and not self.wm_image_path_input.text():
            QMessageBox.warning(self, "警告", "请选择水印图片！")
            return
        if wm_type in ("text", "both") and not self.wm_text_input.text().strip():
            QMessageBox.warning(self, "警告", "请输入水印文字！")
            return

        font_path = find_font_path(self.wm_font_family)
        x_ratio, y_ratio = self.wm_position_preview.get_position_ratio()

        self.wm_start_btn.setEnabled(False)
        self.wm_cancel_btn.setEnabled(True)
        self.wm_progress.setVisible(True)
        self.wm_progress.setValue(0)
        self.wm_log.clear()

        self.wm_worker = WatermarkWorker(
            paths,
            self.wm_output_dir.text().strip(),
            self.wm_overwrite.isChecked(),
            wm_type,
            self.wm_image_path_input.text().strip(),
            self.wm_text_input.text().strip(),
            font_path,
            self.wm_font_size_spin.value(),
            self.wm_font_color,
            x_ratio,
            y_ratio,
            self.wm_opacity_slider.value(),
            self.wm_scale_spin.value(),
            self.wm_margin_x.value(),
            self.wm_margin_y.value(),
        )
        self.wm_worker.progress.connect(self._wm_update_progress)
        self.wm_worker.log.connect(self._wm_log)
        self.wm_worker.finished_signal.connect(self._wm_finished)
        self.wm_worker.start()

    def _wm_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔴 " if is_error else ""
        self.wm_log.append(f"[{timestamp}] {prefix}{message}")

    def _wm_update_progress(self, current, total):
        self.wm_progress.setMaximum(total)
        self.wm_progress.setValue(current)

    def _wm_finished(self, stats):
        self.wm_start_btn.setEnabled(True)
        self.wm_cancel_btn.setEnabled(False)
        self.wm_progress.setVisible(False)
        self._wm_log(f"\n{'='*50}")
        self._wm_log(f"✅ 水印处理完成！")
        self._wm_log(f"   总文件数: {stats['total']}")
        self._wm_log(f"   成功: {stats['success']}")
        self._wm_log(f"   失败: {stats['fail']}")
        QMessageBox.information(self, "完成", f"水印添加完成，成功 {stats['success']} 张！")

    def on_wm_cancel(self):
        if hasattr(self, 'wm_worker') and self.wm_worker and self.wm_worker.isRunning():
            self.wm_worker.cancel()
            self._wm_log("⏹ 正在取消水印处理...")

    # ── Rename handlers ──

    def rn_insert_var(self, var):
        cursor = self.rn_pattern_input.cursorPosition()
        text = self.rn_pattern_input.text()
        new_text = text[:cursor] + var + text[cursor:]
        self.rn_pattern_input.setText(new_text)
        self.rn_pattern_input.setCursorPosition(cursor + len(var))

    def on_rn_preview(self):
        paths = self._rn_get_paths()
        if not paths:
            return
        pattern = self.rn_pattern_input.text().strip()
        if not pattern:
            for i in range(len(paths)):
                self.rn_file_table.setItem(i, 1, QTableWidgetItem(""))
            return
        previews = generate_rename_preview(
            paths, pattern,
            self.rn_start_index.value(),
            self.rn_pad_digits.value(),
            self.rn_date_format.currentData(),
        )
        for i, (_, new_name) in enumerate(previews):
            if i < self.rn_file_table.rowCount():
                self.rn_file_table.setItem(i, 1, QTableWidgetItem(new_name))

    def on_rn_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "所有文件 (*.*)",
        )
        for f in files:
            self._rn_add_item(f)
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    full = os.path.join(root, file)
                    if self._rn_add_item(full):
                        count += 1
            self._rn_update_count()
            self.on_rn_preview()
            if count > 0:
                self._rn_log(f"✅ 已添加文件夹，共找到 {count} 个文件")

    def _rn_add_item(self, file_path):
        if not os.path.isfile(file_path):
            return False
        for i in range(self.rn_file_table.rowCount()):
            if self.rn_file_table.item(i, 2).text() == file_path:
                return False
        row = self.rn_file_table.rowCount()
        self.rn_file_table.insertRow(row)
        p = Path(file_path)
        self.rn_file_table.setItem(row, 0, QTableWidgetItem(p.name))
        self.rn_file_table.setItem(row, 1, QTableWidgetItem(""))
        self.rn_file_table.setItem(row, 2, QTableWidgetItem(file_path))
        return True

    def on_rn_remove_selected(self):
        for item in self.rn_file_table.selectedItems():
            self.rn_file_table.removeRow(item.row())
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_clear(self):
        self.rn_file_table.setRowCount(0)
        self._rn_update_count()

    def _rn_update_count(self):
        self.rn_file_count.setText(f"共 {self.rn_file_table.rowCount()} 个文件")

    def _rn_get_paths(self):
        paths = []
        for i in range(self.rn_file_table.rowCount()):
            fp = self.rn_file_table.item(i, 2).text()
            if fp:
                paths.append(fp)
        return paths

    def on_rn_start(self):
        paths = self._rn_get_paths()
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加要重命名的文件！")
            return

        pattern = self.rn_pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "警告", "请输入命名模式！")
            return

        if "{name}" not in pattern and "{index}" not in pattern and "{date}" not in pattern:
            reply = QMessageBox.question(
                self, "确认", "命名模式中未包含任何变量，所有文件将被重命名为相同名称，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.rn_start_btn.setEnabled(False)
        self.rn_progress.setVisible(True)
        self.rn_progress.setValue(0)
        self.rn_log.clear()

        self.rn_worker = RenameWorker(
            paths, pattern,
            self.rn_start_index.value(),
            self.rn_pad_digits.value(),
            self.rn_date_format.currentData(),
        )
        self.rn_worker.progress.connect(self._rn_update_progress)
        self.rn_worker.log.connect(self._rn_log)
        self.rn_worker.finished_signal.connect(self._rn_finished)
        self.rn_worker.start()

    def _rn_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔴 " if is_error else ""
        self.rn_log.append(f"[{timestamp}] {prefix}{message}")

    def _rn_update_progress(self, current, total):
        self.rn_progress.setMaximum(total)
        self.rn_progress.setValue(current)

    def _rn_finished(self, stats):
        self.rn_start_btn.setEnabled(True)
        self.rn_progress.setVisible(False)
        self._rn_log(f"\n{'='*50}")
        self._rn_log(f"✅ 重命名完成！")
        self._rn_log(f"   总文件数: {stats['total']}")
        self._rn_log(f"   成功: {stats['success']}")
        self._rn_log(f"   失败: {stats['fail']}")
        QMessageBox.information(self, "完成", f"重命名完成，成功 {stats['success']} 个文件！")
        self.on_rn_clear()

    # ── Original handlers (updated) ──

    def on_sidebar_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index == 4:
            self.refresh_history_table()

    def on_resize_toggled(self, enabled):
        for w in [self.resize_method_combo, self.resize_width_input,
                  self.resize_height_input]:
            w.setEnabled(enabled)

    def load_settings(self):
        saved_format = self.config.get("target_format", DEFAULT_FORMAT)
        idx = self.format_combo.findData(saved_format)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        saved_resize = self.config.get("resize", {})
        if saved_resize.get("enabled"):
            self.resize_checkbox.setChecked(True)
            method_idx = self.resize_method_combo.findData(saved_resize.get("method", DEFAULT_RESIZE_METHOD))
            if method_idx >= 0:
                self.resize_method_combo.setCurrentIndex(method_idx)
            self.resize_width_input.setValue(saved_resize.get("width", 0))
            self.resize_height_input.setValue(saved_resize.get("height", 0))
        self.refresh_key_table()
        self.key_manager.refresh_all_usage()
        self.refresh_key_table()

    def save_settings(self):
        self.config["target_format"] = self.format_combo.currentData()
        self.config["resize"] = {
            "enabled": self.resize_checkbox.isChecked(),
            "method": self.resize_method_combo.currentData(),
            "width": self.resize_width_input.value(),
            "height": self.resize_height_input.value(),
        }
        self.key_manager.save(self.config)

    def refresh_key_table(self):
        self.key_table.setRowCount(0)
        for k in self.key_manager.keys:
            row = self.key_table.rowCount()
            self.key_table.insertRow(row)

            remark = k.get("remark", "") or k["key"][:8] + "..."
            self.key_table.setItem(row, 0, QTableWidgetItem(remark))

            masked = k["key"][:6] + "*" * (len(k["key"]) - 8) + k["key"][-2:]
            key_item = QTableWidgetItem(masked)
            key_item.setToolTip(k["key"])
            self.key_table.setItem(row, 1, key_item)

            usage_text = f"{k['monthly_usage']} / {k['monthly_limit']}"
            usage_item = QTableWidgetItem(usage_text)
            remaining = k["monthly_limit"] - k["monthly_usage"]
            if remaining <= 0:
                usage_item.setForeground(QBrush(QColor("#f44336")))
            elif remaining < 100:
                usage_item.setForeground(QBrush(QColor("#FF9800")))
            else:
                usage_item.setForeground(QBrush(QColor("#4CAF50")))
            self.key_table.setItem(row, 2, usage_item)

            status = "✅ 启用" if k["enabled"] else "⛔ 禁用"
            status_item = QTableWidgetItem(status)
            if not k["enabled"]:
                status_item.setForeground(QBrush(QColor("#f44336")))
            self.key_table.setItem(row, 3, status_item)

        self.update_key_status()

    def refresh_history_table(self):
        self.history_table.setRowCount(0)
        for record in reversed(self.config.get("history", [])):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(record.get("time", "")))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(record.get("total", 0))))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(record.get("success", 0))))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.get("fail", 0))))
            self.history_table.setItem(row, 4, QTableWidgetItem(format_size(record.get("original_size", 0))))
            self.history_table.setItem(row, 5, QTableWidgetItem(format_size(record.get("compressed_size", 0))))

    def clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有压缩历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.config["history"] = []
            save_config(self.config)
            self.refresh_history_table()

    def update_key_status(self):
        total = len(self.key_manager.keys)
        enabled = sum(1 for k in self.key_manager.keys if k["enabled"])
        available = len(self.key_manager.get_available_keys())
        remaining_total = sum(
            k["monthly_limit"] - k["monthly_usage"]
            for k in self.key_manager.keys
            if k["enabled"]
        )
        limit_total = sum(
            k["monthly_limit"]
            for k in self.key_manager.keys
            if k["enabled"]
        )
        self.key_status_label.setText(
            f"共 {total} 个密钥 | {enabled} 个启用 | {available} 个可用 | "
            f"总剩余额度: {remaining_total}/{limit_total}"
        )

    def update_file_summary(self):
        count = self.file_list_widget.count()
        total_size = 0
        for i in range(count):
            fp = self.file_list_widget.item(i).data(Qt.UserRole)
            if fp and os.path.isfile(fp):
                total_size += os.path.getsize(fp)
        self.file_count_label.setText(f"共 {count} 个文件")
        self.file_total_size_label.setText(f"总计: {format_size(total_size)}")

    def add_item_to_list(self, file_path):
        if not os.path.isfile(file_path):
            return
        for i in range(self.file_list_widget.count()):
            if self.file_list_widget.item(i).data(Qt.UserRole) == file_path:
                return
        size = os.path.getsize(file_path)
        item = QListWidgetItem(f"{Path(file_path).name}  ({format_size(size)})")
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)
        self.file_list_widget.addItem(item)

    def get_file_paths(self):
        paths = []
        for i in range(self.file_list_widget.count()):
            fp = self.file_list_widget.item(i).data(Qt.UserRole)
            if fp:
                paths.append(fp)
        return paths

    def add_key_dialog(self):
        dialog = AddKeyDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            existing_keys = [k["key"] for k in self.key_manager.keys]
            if data["key"] in existing_keys:
                QMessageBox.warning(self, "警告", "该 API Key 已存在！")
                return
            self.key_manager.add_key(data["key"], data["remark"], data["monthly_limit"])
            self.refresh_key_table()
            self.save_settings()
            self.log(f"✅ 已添加密钥: {data['remark'] or data['key'][:8]}...")

    def edit_key_dialog(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个密钥")
            return
        key_data = self.key_manager.keys[row]
        dialog = AddKeyDialog(self, edit_mode=True, key_data=key_data)
        if dialog.exec_():
            data = dialog.get_data()
            if data["key"] != key_data["key"] and any(
                k["key"] == data["key"] for k in self.key_manager.keys
            ):
                QMessageBox.warning(self, "警告", "该 API Key 已存在！")
                return
            key_data["key"] = data["key"]
            key_data["remark"] = data["remark"]
            key_data["monthly_limit"] = data["monthly_limit"]
            self.refresh_key_table()
            self.save_settings()
            self.log(f"✅ 已更新密钥: {data['remark'] or data['key'][:8]}...")

    def remove_key(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个密钥")
            return
        key = self.key_manager.keys[row]
        remark = key.get("remark") or key["key"][:8]
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除密钥「{remark}」吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.key_manager.remove_key(row)
            self.refresh_key_table()
            self.save_settings()
            self.log(f"🗑 已删除密钥: {remark}")

    def toggle_key(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个密钥")
            return
        self.key_manager.toggle_key(row)
        self.refresh_key_table()
        self.save_settings()
        key = self.key_manager.keys[row]
        status = "启用" if key["enabled"] else "禁用"
        remark = key.get("remark") or key["key"][:8]
        self.log(f"⏸ 已{status}密钥: {remark}")

    def refresh_quota(self):
        if not self.key_manager.keys:
            QMessageBox.warning(self, "提示", "没有密钥可刷新")
            return
        self.refresh_quota_btn.setEnabled(False)
        self.refresh_quota_btn.setText("⏳ 刷新中...")
        QApplication.processEvents()

        self.key_manager.refresh_all_usage()
        self.refresh_key_table()
        self.save_settings()

        self.refresh_quota_btn.setText("🔄 刷新额度")
        self.refresh_quota_btn.setEnabled(True)
        self.log("✅ 已刷新所有密钥的当前使用额度")

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "图片文件 (*.jpg *.jpeg *.png *.webp *.gif *.tiff *.tif *.bmp *.avif);;所有文件 (*.*)",
        )
        for f in files:
            self.add_item_to_list(f)
        self.update_file_summary()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含图片的文件夹")
        if folder:
            supported_ext = SUPPORTED_EXTENSIONS
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in supported_ext:
                        count_before = self.file_list_widget.count()
                        self.add_item_to_list(os.path.join(root, file))
                        if self.file_list_widget.count() > count_before:
                            count += 1
            self.update_file_summary()
            self.log(f"✅ 已添加文件夹，共找到 {count} 张图片")

    def remove_selected(self):
        for item in self.file_list_widget.selectedItems():
            row = self.file_list_widget.row(item)
            self.file_list_widget.takeItem(row)
        self.update_file_summary()

    def clear_all(self):
        self.file_list_widget.clear()
        self.update_file_summary()

    def log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔴 " if is_error else ""
        self.log_text.append(f"[{timestamp}] {prefix}{message}")

    def start_compress(self):
        if not self.key_manager.get_available_keys():
            QMessageBox.warning(
                self, "警告",
                "没有可用的 API Key！\n请先在「密钥管理」中添加有效的密钥并确保额度未用完。\n可在 https://tinypng.com/developers 免费获取",
            )
            return

        file_paths = self.get_file_paths()
        if not file_paths:
            QMessageBox.warning(self, "警告", "请先添加要压缩的图片！")
            return

        oversize_files = [fp for fp in file_paths if os.path.getsize(fp) > MAX_FREE_SIZE]
        if oversize_files:
            names = "\n".join(
                f"  • {Path(fp).name} ({format_size(os.path.getsize(fp))})"
                for fp in oversize_files[:5]
            )
            extra = f"\n  ... 及其他 {len(oversize_files)-5} 个" if len(oversize_files) > 5 else ""
            reply = QMessageBox.warning(
                self, "文件大小警告",
                f"以下 {len(oversize_files)} 个文件超过 TinyPNG 免费版 5MB 限制，可能压缩失败：\n\n{names}{extra}\n\n是否继续？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.save_settings()

        self.compress_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        output_dir = self.output_dir_input.text().strip()
        overwrite = self.overwrite_checkbox.isChecked()
        target_format = self.format_combo.currentData()

        resize_params = None
        if self.resize_checkbox.isChecked():
            method = self.resize_method_combo.currentData()
            w = self.resize_width_input.value()
            h = self.resize_height_input.value()
            params = {"method": method}
            if w > 0:
                params["width"] = w
            if h > 0:
                params["height"] = h
            if len(params) > 1:
                resize_params = params

        available_count = len(self.key_manager.get_available_keys())
        fmt_label = FORMATS[target_format]["label"]
        resize_label = f" + 调整尺寸({resize_params['method']})" if resize_params else ""
        self.log(f"🚀 开始压缩任务，共 {len(file_paths)} 个文件，可用密钥 {available_count} 个，输出格式: {fmt_label}{resize_label}")

        self.worker = CompressWorker(
            self.key_manager, file_paths, output_dir, overwrite,
            target_format, resize_params,
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log)
        self.worker.finished_signal.connect(self.compress_finished)
        self.worker.key_usage_updated.connect(self.refresh_key_table)
        self.worker.start()

    def cancel_compress(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log("⏹ 正在取消压缩...")

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def compress_finished(self, stats):
        self.compress_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.log("\n" + "=" * 50)
        self.log(f"📊 压缩完成！")
        self.log(f"   总文件数: {stats['total']}")
        self.log(f"   成功: {stats['success']}")
        self.log(f"   失败: {stats['fail']}")

        if stats["original_size"] > 0:
            saved = stats["original_size"] - stats["compressed_size"]
            saved_percent = (saved / stats["original_size"]) * 100
            self.log(f"   原始大小: {stats['original_size'] / (1024*1024):.2f} MB")
            self.log(f"   压缩后大小: {stats['compressed_size'] / (1024*1024):.2f} MB")
            self.log(f"   节省空间: {saved / (1024*1024):.2f} MB ({saved_percent:.1f}%)")

        self.log("=" * 50)
        QMessageBox.information(self, "压缩完成", f"成功压缩 {stats['success']} 张图片！")

        record = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": stats["total"],
            "success": stats["success"],
            "fail": stats["fail"],
            "original_size": stats["original_size"],
            "compressed_size": stats["compressed_size"],
        }
        history = self.config.get("history", [])
        history.append(record)
        if len(history) > 100:
            history = history[-100:]
        self.config["history"] = history

        self.refresh_key_table()
        self.save_settings()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        current_idx = self.sidebar.currentRow()
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                ext = Path(file_path).suffix.lower()
                if current_idx == 2:
                    self._rn_add_item(file_path)
                elif ext in SUPPORTED_EXTENSIONS:
                    if current_idx == 0:
                        self.add_item_to_list(file_path)
                    elif current_idx == 1:
                        self._wm_add_item(file_path)
            elif os.path.isdir(file_path):
                if current_idx == 2:
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            self._rn_add_item(os.path.join(root, file))
                else:
                    supported_ext = SUPPORTED_EXTENSIONS
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            if Path(file).suffix.lower() in supported_ext:
                                full = os.path.join(root, file)
                                if current_idx == 0:
                                    self.add_item_to_list(full)
                                elif current_idx == 1:
                                    self._wm_add_item(full)
        if current_idx == 0:
            self.update_file_summary()
        elif current_idx == 1:
            self._wm_update_count()
            self._wm_update_preview()
        elif current_idx == 2:
            self._rn_update_count()
            self.on_rn_preview()
        event.acceptProposedAction()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TinyJPG Compressor")
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    if os.path.isfile(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    window = MainWindow()
    if os.path.isfile(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
