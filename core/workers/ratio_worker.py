import os
import math
from pathlib import Path

from PIL import Image as PILImg
from PyQt5.QtCore import QThread, pyqtSignal

from i18n import T
from core.image_utils import adjust_aspect_ratio


class AspectRatioWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, file_paths, output_dir, overwrite, target_w, target_h,
                 mode, anchor, fill_color, crop_rect=None):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.target_w = target_w
        self.target_h = target_h
        self.mode = mode
        self.anchor = anchor
        self.fill_color = fill_color
        self.crop_rect = crop_rect
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.file_paths)
        success = 0
        fail = 0
        total_original = 0
        total_compressed = 0

        for idx, fp in enumerate(self.file_paths):
            if self._is_cancelled:
                self.log.emit(T("worker.ratio_cancelled"), False)
                break

            self.log.emit(T("worker.ratio_processing", name=Path(fp).name), False)
            try:
                original_size = os.path.getsize(fp)
                ext = Path(fp).suffix.lower()
                if ext in (".ico", ".pdf"):
                    self.log.emit(T("worker.ratio_skip_format", name=Path(fp).name), False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                img = PILImg.open(fp)
                if self.mode == "crop" and self.crop_rect and self.crop_rect.isValid():
                    r = self.crop_rect
                    result = img.crop((int(r.left()), int(r.top()),
                                       int(r.right()), int(r.bottom())))
                    if result.mode == "RGBA":
                        result = result.convert("RGB")
                else:
                    result = adjust_aspect_ratio(
                        img, self.target_w, self.target_h,
                        mode=self.mode, anchor=self.anchor,
                        fill_color=self.fill_color,
                    )
                img.close()

                if self.output_dir:
                    out_path = Path(self.output_dir) / Path(fp).name
                elif self.overwrite:
                    out_path = Path(fp)
                else:
                    stem = Path(fp).stem
                    out_path = Path(fp).parent / f"{stem}_ratio{ext}"

                if out_path.exists() and not self.overwrite and out_path.resolve() != Path(fp).resolve():
                    self.log.emit(T("worker.ratio_skip_exists", name=out_path.name), False)
                    fail += 1
                    self.progress.emit(idx + 1, total)
                    continue

                save_kwargs = {"quality": 95}
                if ext in (".jpg", ".jpeg"):
                    save_kwargs["quality"] = 95
                    if result.mode == "RGBA":
                        result = result.convert("RGB")
                elif ext == ".png":
                    save_kwargs = {}
                    if result.mode == "RGBA":
                        result = result.convert("RGBA")
                    result.save(out_path)
                    compressed_size = os.path.getsize(out_path)
                    total_original += original_size
                    total_compressed += compressed_size
                    success += 1
                    self.log.emit(T("worker.ratio_success", name=Path(fp).name), False)
                    self.progress.emit(idx + 1, total)
                    continue

                result.save(out_path, **save_kwargs)
                compressed_size = os.path.getsize(out_path)
                total_original += original_size
                total_compressed += compressed_size
                success += 1
                self.log.emit(T("worker.ratio_success", name=Path(fp).name), False)

            except Exception as e:
                self.log.emit(T("worker.ratio_failed", name=Path(fp).name, error=str(e)), True)
                fail += 1

            self.progress.emit(idx + 1, total)

        self.finished_signal.emit({
            "total": total, "success": success, "fail": fail,
            "original_size": total_original, "compressed_size": total_compressed,
        })
