import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QLineEdit, QCheckBox,
    QAbstractItemView, QSpinBox, QComboBox, QColorDialog,
    QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap

from i18n import T
from core.config import (
    SUPPORTED_EXTENSIONS, RATIO_MODES, RATIO_PRESETS, RATIO_ANCHORS, RATIO_FILL_COLORS,
)
from core.workers.ratio_worker import AspectRatioWorker
from widgets.drop_zone import DropZone
from widgets.crop_graphics import CropGraphicsPreview


class RatioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ratio_fill_rgb = (255, 255, 255)
        self._file_list_expanded = False
        self.build_ratio_page()

    # ── UI construction ──────────────────────────────────────────────

    def build_ratio_page(self):
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

        # ── empty state: drop zone ──
        self.drop_zone = DropZone()
        self.drop_zone.add_files_clicked.connect(self._on_ratio_add_files)
        self.drop_zone.add_folder_clicked.connect(self._on_ratio_add_folder)
        self.drop_zone.files_dropped.connect(self._on_ratio_paths_dropped)
        outer.addWidget(self.drop_zone, 1)

        # ── files state: content area ──
        self.content_widget = QWidget()
        content_root = QVBoxLayout(self.content_widget)
        content_root.setContentsMargins(0, 0, 0, 0)
        content_root.setSpacing(0)

        split = QHBoxLayout()
        split.setSpacing(14)

        # ========== LEFT COLUMN ==========
        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        # file list toggle
        self.ratio_file_toggle = QPushButton()
        self.ratio_file_toggle.setCursor(Qt.PointingHandCursor)
        self.ratio_file_toggle.clicked.connect(self._toggle_file_list)
        left_col.addWidget(self.ratio_file_toggle)

        # collapsible file list
        self.ratio_file_list_widget = QWidget()
        self.ratio_file_list_widget.setVisible(False)
        fl_layout = QVBoxLayout(self.ratio_file_list_widget)
        fl_layout.setContentsMargins(0, 0, 0, 0)
        fl_layout.setSpacing(6)

        self.ratio_file_list = QListWidget()
        self.ratio_file_list.setAcceptDrops(True)
        self.ratio_file_list.setDragEnabled(True)
        self.ratio_file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ratio_file_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.ratio_file_list.setMaximumHeight(200)
        fl_layout.addWidget(self.ratio_file_list)

        fl_btns = QHBoxLayout()
        fl_btns.setSpacing(6)
        self.ratio_add_btn = QPushButton()
        self.ratio_add_btn.setProperty("class", "primary")
        self.ratio_add_btn.clicked.connect(self._on_ratio_add_files)
        self.ratio_folder_btn = QPushButton()
        self.ratio_folder_btn.clicked.connect(self._on_ratio_add_folder)
        self.ratio_remove_btn = QPushButton()
        self.ratio_remove_btn.clicked.connect(self._on_ratio_remove)
        self.ratio_clear_btn = QPushButton()
        self.ratio_clear_btn.clicked.connect(self._on_ratio_clear)
        fl_btns.addWidget(self.ratio_add_btn)
        fl_btns.addWidget(self.ratio_folder_btn)
        fl_btns.addWidget(self.ratio_remove_btn)
        fl_btns.addWidget(self.ratio_clear_btn)
        fl_btns.addStretch()
        fl_layout.addLayout(fl_btns)

        left_col.addWidget(self.ratio_file_list_widget)

        # crop preview (stretches)
        self.ratio_preview = CropGraphicsPreview()
        self.ratio_preview.cropRectChanged.connect(self._on_ratio_crop_changed)
        self.ratio_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_col.addWidget(self.ratio_preview, 1)

        # action bar
        ctrl = QHBoxLayout()
        ctrl.addStretch()
        self.ratio_start_btn = QPushButton()
        self.ratio_start_btn.setProperty("class", "primary")
        self.ratio_cancel_btn = QPushButton()
        self.ratio_cancel_btn.setEnabled(False)
        self.ratio_cancel_btn.setProperty("class", "danger")
        self.ratio_start_btn.clicked.connect(self._on_ratio_start)
        self.ratio_cancel_btn.clicked.connect(self._on_ratio_cancel)
        ctrl.addWidget(self.ratio_cancel_btn)
        ctrl.addWidget(self.ratio_start_btn)
        left_col.addLayout(ctrl)

        self.ratio_progress = QProgressBar()
        self.ratio_progress.setVisible(False)
        left_col.addWidget(self.ratio_progress)

        split.addLayout(left_col, 7)

        # ========== RIGHT SETTINGS PANEL ==========
        self.settings_panel = QFrame()
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setMinimumWidth(270)
        sr = QVBoxLayout(self.settings_panel)
        sr.setContentsMargins(14, 14, 14, 14)
        sr.setSpacing(10)

        self.settings_title = QLabel()
        self.settings_title.setObjectName("settingsPanelTitle")
        sr.addWidget(self.settings_title)

        # mode
        self._ratio_label_mode = QLabel()
        self._ratio_label_mode.setObjectName("settingsLabel")
        sr.addWidget(self._ratio_label_mode)
        self.ratio_mode_combo = QComboBox()
        for key in RATIO_MODES:
            self.ratio_mode_combo.addItem(T("ratio." + key), key)
        self.ratio_mode_combo.setCurrentIndex(0)
        self.ratio_mode_combo.currentIndexChanged.connect(self._on_ratio_mode_changed)
        sr.addWidget(self.ratio_mode_combo)

        # anchor
        self._ratio_label_anchor = QLabel()
        self._ratio_label_anchor.setObjectName("settingsLabel")
        sr.addWidget(self._ratio_label_anchor)
        self.ratio_anchor_combo = QComboBox()
        for key in RATIO_ANCHORS:
            self.ratio_anchor_combo.addItem(T("ratio.anchor_" + key), key)
        self.ratio_anchor_combo.setCurrentIndex(0)
        sr.addWidget(self.ratio_anchor_combo)

        # fill color row (visible only when mode=pad)
        self._ratio_fill_row = QWidget()
        self._ratio_fill_row.setVisible(False)
        fill_layout = QVBoxLayout(self._ratio_fill_row)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        fill_layout.setSpacing(6)
        self._ratio_label_fill = QLabel()
        self._ratio_label_fill.setObjectName("settingsLabel")
        fill_layout.addWidget(self._ratio_label_fill)
        fill_row = QHBoxLayout()
        fill_row.setSpacing(6)
        self.ratio_fill_combo = QComboBox()
        for key in RATIO_FILL_COLORS:
            self.ratio_fill_combo.addItem(T("ratio.fill_color_" + key), key)
        self.ratio_fill_combo.addItem(T("ratio.fill_color_custom"), "custom")
        self.ratio_fill_combo.setCurrentIndex(0)
        self.ratio_fill_combo.currentIndexChanged.connect(self._on_ratio_fill_changed)
        fill_row.addWidget(self.ratio_fill_combo)
        self.ratio_fill_color_btn = QPushButton()
        self.ratio_fill_color_btn.setFixedSize(28, 28)
        self.ratio_fill_color_btn.setStyleSheet("background-color: white; border: 1px solid #999; border-radius: 4px;")
        self.ratio_fill_color_btn.clicked.connect(self._on_ratio_custom_fill)
        self.ratio_fill_color_btn.setVisible(False)
        fill_row.addWidget(self.ratio_fill_color_btn)
        fill_row.addStretch()
        fill_layout.addLayout(fill_row)
        sr.addWidget(self._ratio_fill_row)

        # separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep1)

        # ratio preset
        self._ratio_label_ratio = QLabel()
        self._ratio_label_ratio.setObjectName("settingsLabel")
        sr.addWidget(self._ratio_label_ratio)
        self.ratio_preset_combo = QComboBox()
        for key in RATIO_PRESETS:
            self.ratio_preset_combo.addItem(T("ratio.preset_" + key.replace(":", "_")), key)
        self.ratio_preset_combo.addItem(T("ratio.preset_custom"), "custom")
        self.ratio_preset_combo.setCurrentIndex(0)
        self.ratio_preset_combo.currentIndexChanged.connect(self._on_ratio_preset_changed)
        sr.addWidget(self.ratio_preset_combo)

        # custom ratio
        self._ratio_custom_row = QWidget()
        custom_layout = QHBoxLayout(self._ratio_custom_row)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(6)
        self._ratio_label_custom = QLabel()
        custom_layout.addWidget(self._ratio_label_custom)
        self.ratio_custom_w = QSpinBox()
        self.ratio_custom_w.setRange(1, 100)
        self.ratio_custom_w.setValue(1)
        self.ratio_custom_w.setFixedWidth(60)
        self.ratio_custom_w.setEnabled(False)
        custom_layout.addWidget(self.ratio_custom_w)
        self._ratio_custom_sep = QLabel(":")
        custom_layout.addWidget(self._ratio_custom_sep)
        self.ratio_custom_h = QSpinBox()
        self.ratio_custom_h.setRange(1, 100)
        self.ratio_custom_h.setValue(1)
        self.ratio_custom_h.setFixedWidth(60)
        self.ratio_custom_h.setEnabled(False)
        custom_layout.addWidget(self.ratio_custom_h)
        self.ratio_swap_btn = QPushButton("\u21c4")
        self.ratio_swap_btn.setFixedWidth(36)
        self.ratio_swap_btn.setEnabled(False)
        self.ratio_swap_btn.clicked.connect(self._on_ratio_swap)
        custom_layout.addWidget(self.ratio_swap_btn)
        custom_layout.addStretch()
        sr.addWidget(self._ratio_custom_row)

        # separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep2)

        # output dir
        self._ratio_output_label = QLabel()
        self._ratio_output_label.setObjectName("settingsLabel")
        sr.addWidget(self._ratio_output_label)

        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.ratio_output_dir = QLineEdit()
        self.ratio_output_browse = QPushButton()
        self.ratio_output_browse.setFixedWidth(56)
        self.ratio_output_browse.clicked.connect(self._on_ratio_browse_output)
        out_row.addWidget(self.ratio_output_dir, 1)
        out_row.addWidget(self.ratio_output_browse)
        sr.addLayout(out_row)

        self.ratio_overwrite = QCheckBox()
        sr.addWidget(self.ratio_overwrite)

        # separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep3)

        # log label
        self._ratio_label_log = QLabel()
        self._ratio_label_log.setObjectName("settingsLabel")
        sr.addWidget(self._ratio_label_log)

        self.ratio_log = QTextEdit()
        self.ratio_log.setReadOnly(True)
        self.ratio_log.setFont(QFont("Consolas", 9))
        self.ratio_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sr.addWidget(self.ratio_log, 1)

        split.addWidget(self.settings_panel, 3)

        content_root.addLayout(split)
        outer.addWidget(self.content_widget, 1)

        self._sync_empty_state()

    # ── i18n ─────────────────────────────────────────────────────────

    def retranslate(self):
        self.page_title.setText(T("ratio_page.page_title"))
        sub = T("ratio_page.page_title")
        self.page_subtitle.setText(
            sub if not sub.startswith("ratio_page.") else "\u8c03\u6574\u56fe\u7247\u6bd4\u4f8b\uff0c\u652f\u6301\u88c1\u526a\u3001\u586b\u5145\u3001\u62c9\u4f38"
        )
        self.drop_zone.set_texts(
            T("compress.drop_title"),
            T("compress.drop_hint"),
            T("app.add_files"),
            T("app.add_folder"),
        )
        self.settings_title.setText(T("ratio_page.page_title"))
        self._ratio_label_mode.setText(T("ratio_page.mode_label"))
        self._ratio_label_anchor.setText(T("ratio_page.anchor_label"))
        self._ratio_label_fill.setText(T("ratio_page.fill_color_label"))
        self._ratio_label_ratio.setText(T("ratio_page.ratio_label"))
        self._ratio_label_custom.setText(T("ratio_page.custom_ratio"))
        self._ratio_output_label.setText(T("app.output_dir") + ":")
        self.ratio_output_dir.setPlaceholderText(T("app.output_dir_placeholder"))
        self.ratio_output_browse.setText(T("app.browse"))
        self.ratio_overwrite.setText(T("app.overwrite_original"))
        self._ratio_label_log.setText(T("compress.log_title"))
        self.ratio_start_btn.setText(T("ratio_page.start_btn"))
        self.ratio_cancel_btn.setText(T("app.cancel"))
        self.ratio_add_btn.setText(T("app.add_files"))
        self.ratio_folder_btn.setText(T("app.add_folder"))
        self.ratio_remove_btn.setText(T("app.remove_selected"))
        self.ratio_clear_btn.setText(T("app.clear_list"))

        saved_key = self.ratio_mode_combo.currentData()
        self.ratio_mode_combo.clear()
        for key in RATIO_MODES:
            self.ratio_mode_combo.addItem(T("ratio." + key), key)
        idx = self.ratio_mode_combo.findData(saved_key)
        if idx >= 0:
            self.ratio_mode_combo.setCurrentIndex(idx)

        saved_a = self.ratio_anchor_combo.currentData()
        self.ratio_anchor_combo.clear()
        for key in RATIO_ANCHORS:
            self.ratio_anchor_combo.addItem(T("ratio.anchor_" + key), key)
        idx = self.ratio_anchor_combo.findData(saved_a)
        if idx >= 0:
            self.ratio_anchor_combo.setCurrentIndex(idx)

        self._ratio_update_count()

    # ── empty / file state ───────────────────────────────────────────

    def _sync_empty_state(self):
        has_files = self.ratio_file_list.count() > 0
        self.drop_zone.setVisible(not has_files)
        self.content_widget.setVisible(has_files)

    def _update_file_toggle(self):
        count = self.ratio_file_list.count()
        arrow = "\u25be" if self._file_list_expanded else "\u25b8"
        self.ratio_file_toggle.setText("\u5171 {} \u4e2a\u6587\u4ef6 {}".format(count, arrow))

    def _toggle_file_list(self):
        self._file_list_expanded = not self._file_list_expanded
        self.ratio_file_list_widget.setVisible(self._file_list_expanded)
        self._update_file_toggle()

    # ── file management ──────────────────────────────────────────────

    def _on_ratio_paths_dropped(self, paths):
        for path in paths:
            if os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    self._ratio_add_item(path)
            elif os.path.isdir(path):
                for root, _dirs, files in os.walk(path):
                    for file in files:
                        if Path(file).suffix.lower() in SUPPORTED_EXTENSIONS:
                            self._ratio_add_item(os.path.join(root, file))
        self._ratio_update_count()
        self._ratio_update_preview()

    def _on_ratio_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, T("app.select_image_files"), "",
            T("app.image_files_filter"),
        )
        for f in files:
            self._ratio_add_item(f)
        self._ratio_update_count()
        self._ratio_update_preview()

    def _on_ratio_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, T("app.select_folder"))
        if folder:
            count = 0
            supported_ext = SUPPORTED_EXTENSIONS
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in supported_ext:
                        if self._ratio_add_item(os.path.join(root, file)):
                            count += 1
            self._ratio_update_count()
            self._ratio_update_preview()
            if count > 0:
                self._ratio_log(T("app.folder_added", count=count))

    def _on_ratio_remove(self):
        for item in self.ratio_file_list.selectedItems():
            self.ratio_file_list.takeItem(self.ratio_file_list.row(item))
        self._ratio_update_count()
        self._ratio_update_preview()

    def _on_ratio_clear(self):
        self.ratio_file_list.clear()
        self._ratio_update_count()
        self._ratio_update_preview()

    # ── public helpers (called by main.py drag-drop) ─────────────────

    def ratio_add_item_direct(self, file_path):
        self._ratio_add_item(file_path)

    def ratio_refresh_after_drop(self):
        self._ratio_update_count()
        self._ratio_update_preview()

    # ── internal ─────────────────────────────────────────────────────

    def _ratio_add_item(self, file_path):
        if not os.path.isfile(file_path):
            return False
        for i in range(self.ratio_file_list.count()):
            if self.ratio_file_list.item(i).data(Qt.UserRole) == file_path:
                return False
        size = os.path.getsize(file_path)
        item = QListWidgetItem(f"{file_path}  ({self._format_size(size)})")
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)
        self.ratio_file_list.addItem(item)
        return True

    def _ratio_get_paths(self):
        paths = []
        for i in range(self.ratio_file_list.count()):
            fp = self.ratio_file_list.item(i).data(Qt.UserRole)
            if fp:
                paths.append(fp)
        return paths

    def _ratio_update_count(self):
        self._update_file_toggle()
        self._sync_empty_state()

    # ── ratio logic ──────────────────────────────────────────────────

    def _on_ratio_mode_changed(self, idx):
        mode = self.ratio_mode_combo.currentData()
        is_pad = mode == "pad"
        self._ratio_fill_row.setVisible(is_pad)
        self.ratio_anchor_combo.setEnabled(True)
        self._on_ratio_preset_changed(self.ratio_preset_combo.currentIndex())

    def _on_ratio_fill_changed(self, idx):
        key = self.ratio_fill_combo.currentData()
        if key in RATIO_FILL_COLORS:
            self._ratio_fill_rgb = RATIO_FILL_COLORS[key]
            self.ratio_fill_color_btn.setVisible(False)
        else:
            self.ratio_fill_color_btn.setVisible(True)

    def _on_ratio_custom_fill(self):
        color = QColorDialog.getColor(QColor(*self._ratio_fill_rgb), self, T("ratio_page.fill_color_label"))
        if color.isValid():
            self._ratio_fill_rgb = (color.red(), color.green(), color.blue())
            self.ratio_fill_color_btn.setStyleSheet(
                f"background-color: rgb({self._ratio_fill_rgb[0]},{self._ratio_fill_rgb[1]},{self._ratio_fill_rgb[2]}); "
                f"border: 1px solid #999; border-radius: 4px;"
            )

    def _on_ratio_preset_changed(self, idx):
        key = self.ratio_preset_combo.currentData()
        if key and key in RATIO_PRESETS:
            w, h = RATIO_PRESETS[key]
            self.ratio_custom_w.setEnabled(False)
            self.ratio_custom_h.setEnabled(False)
            self.ratio_swap_btn.setEnabled(False)
        else:
            w = self.ratio_custom_w.value()
            h = self.ratio_custom_h.value()
            self.ratio_custom_w.setEnabled(True)
            self.ratio_custom_h.setEnabled(True)
            self.ratio_swap_btn.setEnabled(True)
        self._update_ratio_preview()

    def _on_ratio_swap(self):
        w = self.ratio_custom_w.value()
        h = self.ratio_custom_h.value()
        self.ratio_custom_w.setValue(h)
        self.ratio_custom_h.setValue(w)
        self._update_ratio_preview()

    def _on_ratio_crop_changed(self, rect):
        pass

    def _get_ratio_values(self):
        key = self.ratio_preset_combo.currentData()
        if key and key in RATIO_PRESETS:
            w, h = RATIO_PRESETS[key]
        else:
            w = self.ratio_custom_w.value()
            h = self.ratio_custom_h.value()
        return w, h

    def _get_crop_pixel_rect(self):
        return self.ratio_preview.get_crop_pixel_rect()

    def _update_ratio_preview(self):
        w, h = self._get_ratio_values()
        self.ratio_preview.set_target_ratio(w, h)
        self._ratio_update_preview()

    def _ratio_update_preview(self):
        if self.ratio_file_list.count() > 0:
            fp = self.ratio_file_list.item(0).data(Qt.UserRole)
            if fp and os.path.isfile(fp):
                pixmap = QPixmap(fp)
                if not pixmap.isNull():
                    self.ratio_preview.set_base_image(pixmap)
                    w, h = self._get_ratio_values()
                    self.ratio_preview.set_target_ratio(w, h)
                    return
        self.ratio_preview.set_base_image(QPixmap())

    def _on_ratio_browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, T("app.select_output_dir"))
        if dir_path:
            self.ratio_output_dir.setText(dir_path)

    # ── compress workflow ────────────────────────────────────────────

    def _on_ratio_start(self):
        paths = self._ratio_get_paths()
        if not paths:
            QMessageBox.warning(self, T("app.warning"), T("app.add_files_first_ratio"))
            return

        w, h = self._get_ratio_values()
        mode = self.ratio_mode_combo.currentData()
        anchor = self.ratio_anchor_combo.currentData()
        fill_color = self._ratio_fill_rgb
        crop_rect = self._get_crop_pixel_rect()

        self.ratio_start_btn.setEnabled(False)
        self.ratio_cancel_btn.setEnabled(True)
        self.ratio_progress.setVisible(True)
        self.ratio_progress.setValue(0)
        self.ratio_log.clear()

        self.ratio_worker = AspectRatioWorker(
            paths,
            self.ratio_output_dir.text().strip(),
            self.ratio_overwrite.isChecked(),
            w, h, mode, anchor, fill_color, crop_rect,
        )
        self.ratio_worker.progress.connect(self._ratio_update_progress)
        self.ratio_worker.log.connect(self._ratio_log)
        self.ratio_worker.finished_signal.connect(self._ratio_finished)
        self.ratio_worker.start()

    def _on_ratio_cancel(self):
        if hasattr(self, 'ratio_worker') and self.ratio_worker and self.ratio_worker.isRunning():
            self.ratio_worker.cancel()
            self._ratio_log(T("worker.cancel_ratio"))

    def _ratio_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
        self.ratio_log.append(f"[{timestamp}] {prefix}{message}")

    def _ratio_update_progress(self, current, total):
        self.ratio_progress.setMaximum(total)
        self.ratio_progress.setValue(current)

    def _ratio_finished(self, stats):
        self.ratio_start_btn.setEnabled(True)
        self.ratio_cancel_btn.setEnabled(False)
        self.ratio_progress.setVisible(False)
        self._ratio_log(f"\n{'='*50}")
        self._ratio_log(T("ratio_page.finished"))
        self._ratio_log(T("compress.stats_total", count=stats['total']))
        self._ratio_log(T("compress.stats_success", count=stats['success']))
        self._ratio_log(T("compress.stats_fail", count=stats['fail']))
        QMessageBox.information(self, T("app.done"), T("ratio_page.done_msg", count=stats['success']))

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024*1024):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024} KB"
        return f"{size_bytes} B"
