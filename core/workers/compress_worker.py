import os
import time
import threading
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal
import requests

from i18n import T
from core.config import SUPPORTED_EXTENSIONS, FORMATS
from core.image_utils import local_compress_image


class CompressWorker(QThread):
    progress = pyqtSignal(int, int)
    log = pyqtSignal(str, bool)
    finished_signal = pyqtSignal(dict)
    key_usage_updated = pyqtSignal()

    def __init__(self, key_manager, file_paths, output_dir,
                 overwrite=False, target_format="", resize_params=None,
                 use_local_fallback=False, local_quality=85):
        super().__init__()
        self.key_manager = key_manager
        self.file_paths = file_paths
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.target_format = target_format
        self.resize_params = resize_params
        self.use_local_fallback = use_local_fallback
        self.local_quality = local_quality
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
            self.log.emit(T("worker.skip_type", path=file_path), False)
            return None

        input_path = Path(file_path)
        output_name = input_path.stem + target_ext if target_ext else input_path.name
        if self.output_dir:
            output_path = Path(self.output_dir) / output_name
        else:
            output_path = input_path.parent / output_name

        if output_path.exists() and not self.overwrite:
            self.log.emit(T("worker.skip_exists", path=str(output_path)), False)
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
            self.log.emit(T("worker.read_failed", path=file_path, error=str(e)), True)
            return {"success": False, "original_size": 0, "compressed_size": 0}

        max_attempts = max(len(self.key_manager.keys) * 2, 4)
        for attempt in range(max_attempts):
            if self._is_cancelled:
                return None

            key = self.key_manager.acquire_key()
            if key is None:
                if attempt == 0:
                    self.log.emit(T("worker.no_available_key"), True)
                else:
                    self.log.emit(T("worker.all_keys_exhausted", name=input_path.name), True)
                return {"success": False, "original_size": original_size, "compressed_size": 0}

            key_id = key.get("remark") or key["key"][:8]
            self.log.emit(T("worker.compressing", key=key_id, name=input_path.name), False)

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
                    self.log.emit(T("worker.write_failed", path=str(output_path), error=str(e)), True)
                    self.key_manager.release_key(key["key"])
                    return {"success": False, "original_size": original_size, "compressed_size": 0}

                compressed_size = os.path.getsize(output_path)
                saved = original_size - compressed_size
                saved_percent = (saved / original_size) * 100
                self.log.emit(
                    T("worker.compress_success", name=input_path.name,
                      original=original_size // 1024, compressed=compressed_size // 1024,
                      percent=f"{saved_percent:.1f}"),
                    False,
                )
                return {"success": True, "original_size": original_size, "compressed_size": compressed_size}
            else:
                error_msgs = {
                    "QUOTA_EXCEEDED": T("worker.error_quota"),
                    "INVALID_KEY": T("worker.error_invalid_key"),
                    "TIMEOUT": T("worker.error_timeout"),
                    "NETWORK": T("worker.error_network"),
                    "HTTP_413": T("worker.error_413"),
                    "HTTP_415": T("worker.error_415"),
                }
                msg = error_msgs.get(error, error)

                if error in ("QUOTA_EXCEEDED", "INVALID_KEY"):
                    self.key_manager.disable_key(key["key"])
                    self.log.emit(T("worker.key_warning", key=key_id, error=msg), True)
                elif error in ("TIMEOUT", "NETWORK"):
                    self.key_manager.release_key(key["key"])
                    self.log.emit(T("worker.key_retry", key=key_id, error=msg, attempt=attempt + 1, max=max_attempts), True)
                    time.sleep(1)
                else:
                    self.key_manager.release_key(key["key"])
                    self.log.emit(T("worker.key_failed", key=key_id, error=msg), True)
                    return {"success": False, "original_size": original_size, "compressed_size": 0}

        if self.use_local_fallback:
            self.log.emit(T("worker.local_fallback", name=input_path.name), False)
            fmt = self.target_format
            if is_bmp and not fmt:
                fmt = "png"
            success, compressed_data, error = local_compress_image(
                image_data, Path(file_path).suffix.lower(),
                target_format=fmt, resize_params=self.resize_params,
                quality=self.local_quality,
            )
            if success:
                try:
                    fmt_for_ext = fmt or (".png" if is_bmp else Path(file_path).suffix.lower())
                    ext_map = {"jpeg": ".jpg", "jpg": ".jpg", "jpeg": ".jpg", "tif": ".tiff"}
                    ext = ext_map.get(fmt_for_ext, "." + fmt_for_ext) if fmt else Path(file_path).suffix.lower()
                    output_name = input_path.stem + ext
                    output_path = (Path(self.output_dir) / output_name) if self.output_dir else (input_path.parent / output_name)
                    if output_path.exists() and not self.overwrite:
                        self.log.emit(T("worker.skip_exists", path=str(output_path)), False)
                        return None
                    with open(output_path, "wb") as f:
                        f.write(compressed_data)
                except Exception as e:
                    self.log.emit(T("worker.write_failed", path=str(output_path), error=str(e)), True)
                    return {"success": False, "original_size": original_size, "compressed_size": 0}
                compressed_size = os.path.getsize(output_path)
                saved = original_size - compressed_size
                saved_percent = (saved / original_size) * 100
                self.log.emit(
                    T("worker.compress_success", name=input_path.name,
                      original=original_size // 1024, compressed=compressed_size // 1024,
                      percent=f"{saved_percent:.1f}"),
                    False,
                )
                return {"success": True, "original_size": original_size, "compressed_size": compressed_size}
            else:
                self.log.emit(T("worker.local_fallback_failed", name=input_path.name, error=error), True)

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
                    self.log.emit(T("worker.compress_cancelled"), False)
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
            self.log.emit(T("worker.concurrent_start", count=num_workers), False)

            def safe_process(fp):
                if self._is_cancelled:
                    return None
                return self.process_one_file(fp)

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(safe_process, fp): fp for fp in self.file_paths}
                for future in as_completed(futures):
                    if self._is_cancelled:
                        self.log.emit(T("worker.compress_cancelled"), False)
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
