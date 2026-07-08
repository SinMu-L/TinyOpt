import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from i18n import T


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
                self.log.emit(T("worker.rename_cancelled"), False)
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
                self.log.emit(T("worker.rename_skip_exists", name=new_name), False)
                fail += 1
                self.progress.emit(i + 1, total)
                continue

            try:
                os.rename(fp, str(new_path))
                self.log.emit(T("worker.rename_success", old=p.name, new=new_name), False)
                success += 1
            except Exception as e:
                self.log.emit(T("worker.rename_failed", name=p.name, error=str(e)), True)
                fail += 1

            self.progress.emit(i + 1, total)

        self.finished_signal.emit({
            "total": total, "success": success, "fail": fail,
            "original_size": 0, "compressed_size": 0,
        })
