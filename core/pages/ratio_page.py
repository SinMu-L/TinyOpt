import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QLineEdit, QCheckBox, QGroupBox,
    QAbstractItemView, QSpinBox, QComboBox, QColorDialog,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPixmap

from i18n import T
from core.config import (
    SUPPORTED_EXTENSIONS, RATIO_MODES, RATIO_PRESETS, RATIO_ANCHORS, RATIO_FILL_COLORS,
)
from core.workers.ratio_worker import AspectRatioWorker
from widgets.crop_graphics import CropGraphicsPreview


class RatioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_ratio_page()

    def build_ratio_page(self):
        page = self
        layout = QVBoxLayout(page)

        self.ratio_settings_group = QGroupBox()
        settings_layout = QVBoxLayout(self.ratio_settings_group)

        row1 = QHBoxLayout()
        self._ratio_label_mode = QLabel()
        row1.addWidget(self._ratio_label_mode)
        self.ratio_mode_combo = QComboBox()
        for key in RATIO_MODES:
            self.ratio_mode_combo.addItem(T("ratio." + key), key)
        self.ratio_mode_combo.setCurrentIndex(0)
        self.ratio_mode_combo.currentIndexChanged.connect(self._on_ratio_mode_changed)
        row1.addWidget(self.ratio_mode_combo)
        row1.addSpacing(16)

        self._ratio_label_anchor = QLabel()
        row1.addWidget(self._ratio_label_anchor)
        self.ratio_anchor_combo = QComboBox()
        for key in RATIO_ANCHORS:
            self.ratio_anchor_combo.addItem(T("ratio.anchor_" + key), key)
        self.ratio_anchor_combo.setCurrentIndex(0)
        row1.addWidget(self.ratio_anchor_combo)

        self._ratio_fill_row = QWidget()
        fill_layout = QHBoxLayout(self._ratio_fill_row)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        self._ratio_label_fill = QLabel()
        fill_layout.addWidget(self._ratio_label_fill)
        self.ratio_fill_combo = QComboBox()
        for key in RATIO_FILL_COLORS:
            self.ratio_fill_combo.addItem(T("ratio.fill_color_" + key), key)
        self.ratio_fill_combo.addItem(T("ratio.fill_color_custom"), "custom")
        self.ratio_fill_combo.setCurrentIndex(0)
        self.ratio_fill_combo.currentIndexChanged.connect(self._on_ratio_fill_changed)
        fill_layout.addWidget(self.ratio_fill_combo)
        self.ratio_fill_color_btn = QPushButton()
        self.ratio_fill_color_btn.setFixedSize(28, 28)
        self.ratio_fill_color_btn.setStyleSheet("background-color: white; border: 1px solid #999;")
        self.ratio_fill_color_btn.clicked.connect(self._on_ratio_custom_fill)
        self.ratio_fill_color_btn.setVisible(False)
        fill_layout.addWidget(self.ratio_fill_color_btn)
        fill_layout.addStretch()
        self._ratio_fill_row.setVisible(False)
        row1.addWidget(self._ratio_fill_row)
        row1.addStretch()
        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self._ratio_label_ratio = QLabel()
        row2.addWidget(self._ratio_label_ratio)
        self.ratio_preset_combo = QComboBox()
        for key in RATIO_PRESETS:
            self.ratio_preset_combo.addItem(T("ratio.preset_" + key.replace(":", "_")), key)
        self.ratio_preset_combo.addItem(T("ratio.preset_custom"), "custom")
        self.ratio_preset_combo.setCurrentIndex(0)
        self.ratio_preset_combo.currentIndexChanged.connect(self._on_ratio_preset_changed)
        row2.addWidget(self.ratio_preset_combo)
        row2.addSpacing(8)

        self._ratio_label_custom = QLabel()
        row2.addWidget(self._ratio_label_custom)
        self.ratio_custom_w = QSpinBox()
        self.ratio_custom_w.setRange(1, 100)
        self.ratio_custom_w.setValue(1)
        self.ratio_custom_w.setFixedWidth(60)
        self.ratio_custom_w.setEnabled(False)
        row2.addWidget(self.ratio_custom_w)
        self._ratio_custom_sep = QLabel(":")
        row2.addWidget(self._ratio_custom_sep)
        self.ratio_custom_h = QSpinBox()
        self.ratio_custom_h.setRange(1, 100)
        self.ratio_custom_h.setValue(1)
        self.ratio_custom_h.setFixedWidth(60)
        self.ratio_custom_h.setEnabled(False)
        row2.addWidget(self.ratio_custom_h)
        self.ratio_swap_btn = QPushButton("⇄")
        self.ratio_swap_btn.setFixedWidth(36)
        self.ratio_swap_btn.setEnabled(False)
        self.ratio_swap_btn.clicked.connect(self._on_ratio_swap)
        row2.addWidget(self.ratio_swap_btn)
        row2.addStretch()
        settings_layout.addLayout(row2)

        self.ratio_preview = CropGraphicsPreview()
        self.ratio_preview.cropRectChanged.connect(self._on_ratio_crop_changed)
        settings_layout.addWidget(self.ratio_preview, alignment=Qt.AlignCenter)

        layout.addWidget(self.ratio_settings_group)

        output_layout = QHBoxLayout()
        self._ratio_output_label = QLabel()
        output_layout.addWidget(self._ratio_output_label)
        self.ratio_output_dir = QLineEdit()
        output_layout.addWidget(self.ratio_output_dir)
        self.ratio_output_browse = QPushButton()
        self.ratio_output_browse.clicked.connect(self._on_ratio_browse_output)
        output_layout.addWidget(self.ratio_output_browse)
        self.ratio_overwrite = QCheckBox()
        output_layout.addWidget(self.ratio_overwrite)
        output_layout.addStretch()
        layout.addLayout(output_layout)

        self.ratio_file_group = QGroupBox()
        file_layout = QVBoxLayout(self.ratio_file_group)
        self.ratio_file_list = QListWidget()
        self.ratio_file_list.setAcceptDrops(True)
        self.ratio_file_list.setDragEnabled(True)
        self.ratio_file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ratio_file_list.setDragDropMode(QAbstractItemView.InternalMove)
        file_layout.addWidget(self.ratio_file_list)

        info_bar = QHBoxLayout()
        self.ratio_file_count = QLabel()
        info_bar.addWidget(self.ratio_file_count)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.ratio_add_btn = QPushButton()
        self.ratio_add_btn.clicked.connect(self._on_ratio_add_files)
        self.ratio_folder_btn = QPushButton()
        self.ratio_folder_btn.clicked.connect(self._on_ratio_add_folder)
        self.ratio_remove_btn = QPushButton()
        self.ratio_remove_btn.clicked.connect(self._on_ratio_remove)
        self.ratio_clear_btn = QPushButton()
        self.ratio_clear_btn.clicked.connect(self._on_ratio_clear)
        btn_bar.addWidget(self.ratio_add_btn)
        btn_bar.addWidget(self.ratio_folder_btn)
        btn_bar.addWidget(self.ratio_remove_btn)
        btn_bar.addWidget(self.ratio_clear_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)
        layout.addWidget(self.ratio_file_group, 1)

        ctrl = QHBoxLayout()
        self.ratio_start_btn = QPushButton()
        self.ratio_start_btn.setProperty('class', 'primary')
        self.ratio_cancel_btn = QPushButton()
        self.ratio_cancel_btn.setEnabled(False)
        self.ratio_cancel_btn.setProperty('class', 'danger')
        self.ratio_start_btn.clicked.connect(self._on_ratio_start)
        self.ratio_cancel_btn.clicked.connect(self._on_ratio_cancel)
        ctrl.addWidget(self.ratio_start_btn)
        ctrl.addWidget(self.ratio_cancel_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.ratio_progress = QProgressBar()
        self.ratio_progress.setVisible(False)
        layout.addWidget(self.ratio_progress)

        self.ratio_log = QTextEdit()
        self.ratio_log.setReadOnly(True)
        self.ratio_log.setFont(QFont("Consolas", 9))
        self.ratio_log.setMaximumHeight(160)
        layout.addWidget(self.ratio_log)

        self._ratio_fill_rgb = (255, 255, 255)

    def retranslate(self):
        self.ratio_settings_group.setTitle(T('ratio_page.page_title'))
        self._ratio_label_mode.setText(T('ratio_page.mode_label'))
        self._ratio_label_ratio.setText(T('ratio_page.ratio_label'))
        self._ratio_label_custom.setText(T('ratio_page.custom_ratio'))
        self._ratio_label_anchor.setText(T('ratio_page.anchor_label'))
        self._ratio_label_fill.setText(T('ratio_page.fill_color_label'))
        self._ratio_output_label.setText(T('app.output_dir') + ':')
        self.ratio_output_dir.setPlaceholderText(T('app.output_dir_placeholder'))
        self.ratio_output_browse.setText(T('app.browse'))
        self.ratio_overwrite.setText(T('app.overwrite_original'))
        self.ratio_file_group.setTitle(T('ratio_page.task_title'))
        self.ratio_start_btn.setText(T('ratio_page.start_btn'))
        self.ratio_cancel_btn.setText(T('ratio_page.cancel_btn'))
        self.ratio_add_btn.setText(T('app.add_files'))
        self.ratio_folder_btn.setText(T('app.add_folder'))
        self.ratio_remove_btn.setText(T('app.remove_selected'))
        self.ratio_clear_btn.setText(T('app.clear_list'))

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
                f"border: 1px solid #999;"
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

    def _ratio_update_count(self):
        self.ratio_file_count.setText(T("app.file_count", count=self.ratio_file_list.count()))

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

    def _on_ratio_browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, T("app.select_output_dir"))
        if dir_path:
            self.ratio_output_dir.setText(dir_path)

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

    def _ratio_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔴 " if is_error else ""
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

    def _on_ratio_cancel(self):
        if hasattr(self, 'ratio_worker') and self.ratio_worker and self.ratio_worker.isRunning():
            self.ratio_worker.cancel()
            self._ratio_log(T("worker.cancel_ratio"))

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024*1024):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024} KB"
        return f"{size_bytes} B"
