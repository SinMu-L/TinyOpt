import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QLineEdit, QCheckBox, QComboBox, QSpinBox, QAbstractItemView, QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from i18n import T
from core.config import (
    SUPPORTED_EXTENSIONS, FORMATS, MAX_FREE_SIZE,
    DEFAULT_FORMAT, DEFAULT_RESIZE_METHOD, RESIZE_METHODS,
    save_config,
)
from core.utils import format_size
from core.workers.compress_worker import CompressWorker
from widgets.drop_zone import DropZone


class CompressPage(QWidget):
    log_message = pyqtSignal(str, bool)
    keys_changed = pyqtSignal()
    history_updated = pyqtSignal()

    def __init__(self, config, key_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.key_manager = key_manager
        self.worker = None
        self.setup_ui()
        self.retranslate()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        header = QVBoxLayout()
        header.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("pageSubtitle")
        self.page_subtitle.setWordWrap(True)
        header.addWidget(self.page_title)
        header.addWidget(self.page_subtitle)
        outer.addLayout(header)

        # main split: left (7) + right settings panel (3)
        split = QHBoxLayout()
        split.setSpacing(14)

        # ========== LEFT COLUMN ==========
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        self.drop_zone = DropZone()
        self.drop_zone.add_files_clicked.connect(self.add_files)
        self.drop_zone.add_folder_clicked.connect(self.add_folder)
        self.drop_zone.files_dropped.connect(self._on_paths_dropped)
        left_col.addWidget(self.drop_zone)

        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        file_layout = QVBoxLayout(self.file_card)
        file_layout.setContentsMargins(12, 12, 12, 12)
        file_layout.setSpacing(8)

        self.file_list_widget = QListWidget()
        self.file_list_widget.setDragEnabled(True)
        self.file_list_widget.setAcceptDrops(True)
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.file_list_widget.setMinimumHeight(160)
        self.file_list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        file_layout.addWidget(self.file_list_widget, 1)

        info_bar = QHBoxLayout()
        self.file_count_label = QLabel()
        self.file_total_size_label = QLabel("")
        info_bar.addWidget(self.file_count_label)
        info_bar.addWidget(self.file_total_size_label)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)
        self.add_files_btn = QPushButton()
        self.add_files_btn.setProperty("class", "primary")
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_selected_btn = QPushButton()
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.clear_all_btn = QPushButton()
        self.clear_all_btn.clicked.connect(self.clear_all)
        btn_bar.addWidget(self.add_files_btn)
        btn_bar.addWidget(self.add_folder_btn)
        btn_bar.addWidget(self.remove_selected_btn)
        btn_bar.addWidget(self.clear_all_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)

        left_col.addWidget(self.file_card, 1)

        self.ready_bar = QFrame()
        self.ready_bar.setObjectName("readyBar")
        ready_layout = QHBoxLayout(self.ready_bar)
        ready_layout.setContentsMargins(14, 10, 14, 10)
        self.ready_label = QLabel()
        self.ready_label.setObjectName("readyLabel")
        ready_layout.addWidget(self.ready_label)
        ready_layout.addStretch()

        self.compress_btn = QPushButton()
        self.compress_btn.setProperty("class", "primary")
        self.cancel_btn = QPushButton()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setProperty("class", "danger")
        self.compress_btn.clicked.connect(self.start_compress)
        self.cancel_btn.clicked.connect(self.cancel_compress)
        ready_layout.addWidget(self.cancel_btn)
        ready_layout.addWidget(self.compress_btn)
        left_col.addWidget(self.ready_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_col.addWidget(self.progress_bar)

        split.addLayout(left_col, 7)

        # ========== RIGHT SETTINGS PANEL ==========
        self.settings_panel = QFrame()
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setMinimumWidth(260)
        sr = QVBoxLayout(self.settings_panel)
        sr.setContentsMargins(14, 14, 14, 14)
        sr.setSpacing(10)

        self.settings_title = QLabel()
        self.settings_title.setObjectName("settingsPanelTitle")
        sr.addWidget(self.settings_title)

        self._cp_label_format = QLabel()
        self._cp_label_format.setObjectName("settingsLabel")
        self.format_combo = QComboBox()
        self._rebuild_format_combo(self.format_combo)
        sr.addWidget(self._cp_label_format)
        sr.addWidget(self.format_combo)

        self.resize_checkbox = QCheckBox()
        self.resize_checkbox.toggled.connect(self.on_resize_toggled)
        sr.addWidget(self.resize_checkbox)

        self._cp_label_resize_method = QLabel()
        self._cp_label_resize_method.setObjectName("settingsLabel")
        self.resize_method_combo = QComboBox()
        self._rebuild_resize_method_combo(self.resize_method_combo)
        sr.addWidget(self._cp_label_resize_method)
        sr.addWidget(self.resize_method_combo)

        wh_row = QHBoxLayout()
        wh_row.setSpacing(6)
        self._cp_label_width = QLabel()
        wh_row.addWidget(self._cp_label_width)
        self.resize_width_input = QSpinBox()
        self.resize_width_input.setRange(0, 10000)
        self.resize_width_input.setValue(0)
        wh_row.addWidget(self.resize_width_input)
        self._cp_label_height = QLabel()
        wh_row.addWidget(self._cp_label_height)
        self.resize_height_input = QSpinBox()
        self.resize_height_input.setRange(0, 10000)
        self.resize_height_input.setValue(0)
        wh_row.addWidget(self.resize_height_input)
        wh_row.addStretch()
        sr.addLayout(wh_row)

        for w in [self.resize_method_combo, self.resize_width_input,
                  self.resize_height_input]:
            w.setEnabled(False)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep)

        self._cp_label_output = QLabel()
        self._cp_label_output.setObjectName("settingsLabel")
        sr.addWidget(self._cp_label_output)

        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.output_dir_input = QLineEdit()
        self.browse_output_btn = QPushButton()
        self.browse_output_btn.setFixedWidth(56)
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        out_row.addWidget(self.output_dir_input, 1)
        out_row.addWidget(self.browse_output_btn)
        sr.addLayout(out_row)

        self.overwrite_checkbox = QCheckBox()
        self.overwrite_checkbox.toggled.connect(self.on_overwrite_toggled)
        sr.addWidget(self.overwrite_checkbox)

        self.local_fallback_checkbox = QCheckBox()
        sr.addWidget(self.local_fallback_checkbox)

        self._cp_label_log = QLabel()
        self._cp_label_log.setObjectName("settingsLabel")
        sr.addWidget(self._cp_label_log)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sr.addWidget(self.log_text, 1)

        split.addWidget(self.settings_panel, 3)

        outer.addLayout(split, 1)

        self._sync_empty_state()

    def retranslate(self):
        self._retranslate_compression_page()

    def _retranslate_compression_page(self):
        self.page_title.setText(T("compress.hero_title"))
        self.page_subtitle.setText(T("compress.hero_subtitle"))
        self.drop_zone.set_texts(
            T("compress.drop_title"),
            T("compress.drop_hint"),
            T("app.add_files"),
            T("app.add_folder"),
        )
        self.settings_title.setText(T("app.more_settings"))
        self._cp_label_format.setText(T("compress.format_label"))
        self._rebuild_format_combo(self.format_combo)
        self.resize_checkbox.setText(T("app.resize"))
        self._cp_label_resize_method.setText(T("compress.resize_method_label"))
        self._rebuild_resize_method_combo(self.resize_method_combo)
        self._cp_label_width.setText(T("compress.width_label"))
        self._cp_label_height.setText(T("compress.height_label"))
        self.resize_width_input.setSpecialValueText(T("app.auto"))
        self.resize_height_input.setSpecialValueText(T("app.auto"))
        self.resize_width_input.setSuffix(T("app.px"))
        self.resize_height_input.setSuffix(T("app.px"))
        self._cp_label_output.setText(T("app.output_dir"))
        self.output_dir_input.setPlaceholderText(T("app.output_dir_placeholder"))
        self.browse_output_btn.setText(T("app.browse"))
        self.overwrite_checkbox.setText(T("app.overwrite"))
        self.local_fallback_checkbox.setText(T("compress.local_fallback"))
        self.local_fallback_checkbox.setToolTip(T("compress.local_fallback_tooltip"))
        self._cp_label_log.setText(T("compress.log_title"))
        self.compress_btn.setText(T("compress.start_btn"))
        self.cancel_btn.setText(T("compress.cancel_btn"))
        self.add_files_btn.setText(T("app.add_files"))
        self.add_folder_btn.setText(T("app.add_folder"))
        self.remove_selected_btn.setText(T("app.remove_selected"))
        self.clear_all_btn.setText(T("app.clear_list"))
        self.update_file_summary()

    def _rebuild_format_combo(self, combo):
        combo.clear()
        for key in FORMATS:
            label_key = "format." + (key if key else "raw")
            combo.addItem(T(label_key), key)
        saved = self.config.get("target_format", DEFAULT_FORMAT)
        idx = combo.findData(saved)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _rebuild_resize_method_combo(self, combo):
        combo.clear()
        for key in RESIZE_METHODS:
            label_key = "resize." + key
            text = T(label_key).split(" \u2014")[0]
            combo.addItem(text, key)

    def _sync_empty_state(self):
        has_files = self.file_list_widget.count() > 0
        self.drop_zone.setVisible(not has_files)
        self.file_card.setVisible(has_files)
        self.ready_bar.setVisible(has_files)

    def update_file_summary(self):
        count = self.file_list_widget.count()
        total_size = 0
        for i in range(count):
            fp = self.file_list_widget.item(i).data(Qt.UserRole)
            if fp and os.path.isfile(fp):
                total_size += os.path.getsize(fp)
        self.file_count_label.setText(T("app.file_count", count=count))
        self.file_total_size_label.setText(
            T("app.file_total", size=format_size(total_size)) if total_size > 0 else ""
        )
        self.ready_label.setText(T("compress.files_ready", count=count))
        self._sync_empty_state()

    def add_item_to_list(self, file_path):
        if not os.path.isfile(file_path):
            return
        for i in range(self.file_list_widget.count()):
            if self.file_list_widget.item(i).data(Qt.UserRole) == file_path:
                return
        size = os.path.getsize(file_path)
        item = QListWidgetItem(f"{file_path}  ({format_size(size)})")
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

    def _on_paths_dropped(self, paths):
        for path in paths:
            if os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    self.add_item_to_list(path)
            elif os.path.isdir(path):
                for root, _dirs, files in os.walk(path):
                    for file in files:
                        if Path(file).suffix.lower() in SUPPORTED_EXTENSIONS:
                            self.add_item_to_list(os.path.join(root, file))
        self.update_file_summary()

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, T("app.select_image_files"), "",
            T("app.image_files_filter"),
        )
        for f in files:
            self.add_item_to_list(f)
        self.update_file_summary()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, T("app.select_folder"))
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
            if count > 0:
                self.log(T("app.folder_added", count=count))

    def remove_selected(self):
        for item in self.file_list_widget.selectedItems():
            row = self.file_list_widget.row(item)
            self.file_list_widget.takeItem(row)
        self.update_file_summary()

    def clear_all(self):
        self.file_list_widget.clear()
        self.update_file_summary()

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, T("app.select_output_dir"))
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def on_resize_toggled(self, enabled):
        for w in [self.resize_method_combo, self.resize_width_input,
                  self.resize_height_input]:
            w.setEnabled(enabled)

    def on_overwrite_toggled(self, checked):
        if not checked:
            self.output_dir_input.setEnabled(True)
            self.browse_output_btn.setEnabled(True)
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(T("compress.overwrite_confirm_title"))
        msg.setText(T("compress.overwrite_confirm_msg"))
        yes_btn = msg.addButton(T("app.yes"), QMessageBox.YesRole)
        no_btn = msg.addButton(T("app.no"), QMessageBox.NoRole)
        msg.setDefaultButton(no_btn)
        msg.exec_()
        if msg.clickedButton() == no_btn:
            self.overwrite_checkbox.blockSignals(True)
            self.overwrite_checkbox.setChecked(False)
            self.overwrite_checkbox.blockSignals(False)
            return

        self.output_dir_input.setEnabled(False)
        self.browse_output_btn.setEnabled(False)

    def log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
        self.log_text.append(f"[{timestamp}] {prefix}{message}")
        self.log_message.emit(message, is_error)

    def _save_compress_settings(self):
        self.config["target_format"] = self.format_combo.currentData()
        self.config["resize"] = {
            "enabled": self.resize_checkbox.isChecked(),
            "method": self.resize_method_combo.currentData(),
            "width": self.resize_width_input.value(),
            "height": self.resize_height_input.value(),
        }
        self.config["local_fallback"] = self.local_fallback_checkbox.isChecked()
        self.key_manager.save(self.config)

    def load_settings(self):
        saved_format = self.config.get("target_format", DEFAULT_FORMAT)
        idx = self.format_combo.findData(saved_format)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        saved_resize = self.config.get("resize", {})
        if saved_resize.get("enabled"):
            self.resize_checkbox.setChecked(True)
            method_idx = self.resize_method_combo.findData(
                saved_resize.get("method", DEFAULT_RESIZE_METHOD)
            )
            if method_idx >= 0:
                self.resize_method_combo.setCurrentIndex(method_idx)
            self.resize_width_input.setValue(saved_resize.get("width", 0))
            self.resize_height_input.setValue(saved_resize.get("height", 0))
        self.local_fallback_checkbox.setChecked(self.config.get("local_fallback", False))

    def save_settings(self):
        self._save_compress_settings()

    def start_compress(self):
        if not self.key_manager.get_available_keys():
            QMessageBox.warning(
                self, T("app.warning"), T("app.no_keys_available"),
            )
            return

        file_paths = self.get_file_paths()
        if not file_paths:
            QMessageBox.warning(self, T("app.warning"), T("app.add_files_first"))
            return

        oversize_files = [fp for fp in file_paths if os.path.getsize(fp) > MAX_FREE_SIZE]
        if oversize_files:
            names = "\n".join(
                f"  \u2022 {Path(fp).name} ({format_size(os.path.getsize(fp))})"
                for fp in oversize_files[:5]
            )
            extra = (
                T("compress.and_others", count=len(oversize_files) - 5)
                if len(oversize_files) > 5 else ""
            )
            oversize_msg = QMessageBox(self)
            oversize_msg.setIcon(QMessageBox.Warning)
            oversize_msg.setWindowTitle(T("compress.oversize_warning_title"))
            oversize_msg.setText(
                T("compress.oversize_warning_msg", count=len(oversize_files), files=names + extra)
            )
            oversize_yes = oversize_msg.addButton(T("app.yes"), QMessageBox.YesRole)
            oversize_msg.addButton(T("app.no"), QMessageBox.NoRole)
            oversize_msg.setDefaultButton(oversize_yes)
            oversize_msg.exec_()
            if oversize_msg.clickedButton() != oversize_yes:
                return

        self._save_compress_settings()

        self.compress_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        overwrite = self.overwrite_checkbox.isChecked()
        output_dir = "" if overwrite else self.output_dir_input.text().strip()
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
        label_key = "format." + (target_format if target_format else "raw")
        fmt_label = T(label_key)
        resize_label = (
            T("compress.resize_label", method=resize_params["method"])
            if resize_params else ""
        )
        self.log(T(
            "compress.start_log",
            total=len(file_paths),
            keys=available_count,
            format=fmt_label,
            resize=resize_label,
        ))

        self.worker = CompressWorker(
            self.key_manager, file_paths, output_dir, overwrite,
            target_format, resize_params,
            use_local_fallback=self.local_fallback_checkbox.isChecked(),
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log)
        self.worker.finished_signal.connect(self.compress_finished)
        self.worker.key_usage_updated.connect(lambda: self.keys_changed.emit())
        self.worker.start()

    def cancel_compress(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log(T("worker.cancel_compress"))

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def compress_finished(self, stats):
        self.compress_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.log("\n" + "=" * 50)
        self.log(T("compress.finished"))
        self.log(T("compress.stats_total", count=stats["total"]))
        self.log(T("compress.stats_success", count=stats["success"]))
        self.log(T("compress.stats_fail", count=stats["fail"]))

        if stats["original_size"] > 0:
            saved = stats["original_size"] - stats["compressed_size"]
            saved_percent = (saved / stats["original_size"]) * 100
            self.log(T("compress.stats_original", size=stats["original_size"] / (1024 * 1024)))
            self.log(T("compress.stats_compressed", size=stats["compressed_size"] / (1024 * 1024)))
            self.log(T(
                "compress.stats_saved",
                size=saved / (1024 * 1024),
                percent=f"{saved_percent:.1f}",
            ))

        self.log("=" * 50)
        QMessageBox.information(self, T("compress.finished"), T("compress.msg_done", count=stats["success"]))

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

        self.keys_changed.emit()
        self._save_compress_settings()
        save_config(self.config)
        self.history_updated.emit()
