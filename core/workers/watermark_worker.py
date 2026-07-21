import os
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal

from i18n import T
from core.image_utils import apply_watermark_to_image


class WatermarkWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, file_paths, output_dir, overwrite,
                 watermark_type, watermark_image_path,
                 watermark_text, font_path, font_size, font_color,
                 x_ratio, y_ratio, opacity,
                 image_scale, text_scale, margin_x, margin_y,
                 image_rotation, text_rotation):
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
        self.image_scale = image_scale
        self.text_scale = text_scale
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.image_rotation = image_rotation
        self.text_rotation = text_rotation
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
                self.log.emit(T("worker.watermark_failed", name=Path(self.watermark_image_path).name, error=str(e)), True)
                self.finished_signal.emit({"total": total, "success": 0, "fail": total,
                                            "original_size": 0, "compressed_size": 0})
                return

        for idx, fp in enumerate(self.file_paths):
            if self._is_cancelled:
                self.log.emit(T("worker.watermark_cancelled"), False)
                break

            self.log.emit(T("worker.watermark_processing", name=Path(fp).name), False)
            try:
                original_size = os.path.getsize(fp)
                ext = Path(fp).suffix.lower()
                if ext in (".ico", ".pdf"):
                    self.log.emit(T("worker.watermark_skip_format", name=Path(fp).name), False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                with Image.open(fp) as img:
                    result = apply_watermark_to_image(
                        img, self.watermark_type, self._loaded_wm_image,
                        self.watermark_text, self.font_path, self.font_size,
                        self.font_color, self.x_ratio, self.y_ratio,
                        self.opacity,
                        self.image_scale, self.text_scale,
                        self.margin_x, self.margin_y,
                        self.image_rotation, self.text_rotation,
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
                    self.log.emit(T("worker.watermark_skip_exists", name=out_path.name), False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                result.save(out_path, quality=95)
                compressed_size = os.path.getsize(out_path)
                total_original += original_size
                total_compressed += compressed_size
                success += 1
                self.log.emit(T("worker.watermark_success", name=Path(fp).name), False)

            except Exception as e:
                self.log.emit(T("worker.watermark_failed", name=Path(fp).name, error=str(e)), True)
                fail += 1

            self.progress.emit(idx + 1, total)

        self.finished_signal.emit({
            "total": total, "success": success, "fail": fail,
            "original_size": total_original, "compressed_size": total_compressed,
        })
