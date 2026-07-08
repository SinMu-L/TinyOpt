import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QLineEdit, QCheckBox, QGroupBox,
    QAbstractItemView, QSpinBox, QSlider,
    QFontDialog, QColorDialog, QButtonGroup, QRadioButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap

from i18n import T
from core.utils import find_font_path
from core.image_utils import render_text_watermark
from core.workers.watermark_worker import WatermarkWorker
from widgets.position_preview import PositionPreviewWidget


class WatermarkPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_watermark_page()

    def build_watermark_page(self):
        page = self
        layout = QVBoxLayout(page)

        # ── Settings group ──
        self.wm_settings_group = QGroupBox()
        settings_layout = QVBoxLayout(self.wm_settings_group)

        # Type selection
        type_layout = QHBoxLayout()
        self._wm_label_type = QLabel()
        type_layout.addWidget(self._wm_label_type)
        self.wm_type_group = QButtonGroup(self)
        self.wm_type_image = QRadioButton()
        self.wm_type_text = QRadioButton()
        self.wm_type_both = QRadioButton()
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
        self._wm_label_image = QLabel()
        wm_img_layout.addWidget(self._wm_label_image)
        self.wm_image_path_input = QLineEdit()
        wm_img_layout.addWidget(self.wm_image_path_input)
        self.wm_image_browse_btn = QPushButton()
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
        self._wm_label_text = QLabel()
        wm_txt_layout.addWidget(self._wm_label_text)
        self.wm_text_input = QLineEdit()
        self.wm_text_input.textChanged.connect(self._rebuild_wm_preview)
        wm_txt_layout.addWidget(self.wm_text_input)
        self.wm_font_btn = QPushButton()
        self.wm_font_btn.clicked.connect(self.on_wm_select_font)
        wm_txt_layout.addWidget(self.wm_font_btn)
        self.wm_font_size_spin = QSpinBox()
        self.wm_font_size_spin.setRange(8, 500)
        self.wm_font_size_spin.setValue(48)
        self.wm_font_size_spin.setSuffix(" px")
        self.wm_font_size_spin.valueChanged.connect(self._rebuild_wm_preview)
        self._wm_label_font_size = QLabel()
        wm_txt_layout.addWidget(self._wm_label_font_size)
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

        self._wm_label_margin_x = QLabel()
        controls_row.addWidget(self._wm_label_margin_x)
        self.wm_margin_x = QSpinBox()
        self.wm_margin_x.setRange(0, 500)
        self.wm_margin_x.setValue(20)
        self.wm_margin_x.setSuffix(" px")
        self.wm_margin_x.valueChanged.connect(self._rebuild_wm_preview)
        self.wm_margin_x.valueChanged.connect(self._on_wm_margin_changed)
        controls_row.addWidget(self.wm_margin_x)

        controls_row.addSpacing(12)
        self._wm_label_margin_y = QLabel()
        controls_row.addWidget(self._wm_label_margin_y)
        self.wm_margin_y = QSpinBox()
        self.wm_margin_y.setRange(0, 500)
        self.wm_margin_y.setValue(20)
        self.wm_margin_y.setSuffix(" px")
        self.wm_margin_y.valueChanged.connect(self._rebuild_wm_preview)
        self.wm_margin_y.valueChanged.connect(self._on_wm_margin_changed)
        controls_row.addWidget(self.wm_margin_y)

        controls_row.addSpacing(20)
        self._wm_label_opacity = QLabel()
        controls_row.addWidget(self._wm_label_opacity)
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
        self._wm_label_scale = QLabel()
        controls_row.addWidget(self._wm_label_scale)
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
        self._wm_label_output_dir = QLabel()
        output_layout.addWidget(self._wm_label_output_dir)
        self.wm_output_dir = QLineEdit()
        output_layout.addWidget(self.wm_output_dir)
        self.wm_output_browse = QPushButton()
        self.wm_output_browse.clicked.connect(self.on_wm_browse_output)
        output_layout.addWidget(self.wm_output_browse)
        self.wm_overwrite = QCheckBox()
        output_layout.addWidget(self.wm_overwrite)
        output_layout.addStretch()
        settings_layout.addLayout(output_layout)

        layout.addWidget(self.wm_settings_group)

        # ── File list ──
        self.wm_file_group = QGroupBox()
        file_layout = QVBoxLayout(self.wm_file_group)
        self.wm_file_list = QListWidget()
        self.wm_file_list.setAcceptDrops(True)
        self.wm_file_list.setDragEnabled(True)
        self.wm_file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.wm_file_list.setDragDropMode(QAbstractItemView.InternalMove)
        file_layout.addWidget(self.wm_file_list)

        info_bar = QHBoxLayout()
        self.wm_file_count = QLabel()
        info_bar.addWidget(self.wm_file_count)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.wm_add_btn = QPushButton()
        self.wm_add_btn.clicked.connect(self.on_wm_add_files)
        self.wm_remove_btn = QPushButton()
        self.wm_remove_btn.clicked.connect(self.on_wm_remove_selected)
        self.wm_clear_btn = QPushButton()
        self.wm_clear_btn.clicked.connect(self.on_wm_clear)
        btn_bar.addWidget(self.wm_add_btn)
        btn_bar.addWidget(self.wm_remove_btn)
        btn_bar.addWidget(self.wm_clear_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)
        layout.addWidget(self.wm_file_group, 1)

        # ── Buttons ──
        ctrl = QHBoxLayout()
        self.wm_start_btn = QPushButton()
        self.wm_start_btn.setProperty('class', 'primary')
        self.wm_cancel_btn = QPushButton()
        self.wm_cancel_btn.setEnabled(False)
        self.wm_cancel_btn.setProperty('class', 'danger')
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

    def _retranslate_watermark_page(self):
        self.wm_settings_group.setTitle(T('watermark.page_title'))
        self._wm_label_type.setText(T('watermark.type') + ':')
        self.wm_type_image.setText(T('watermark.type_image'))
        self.wm_type_text.setText(T('watermark.type_text'))
        self.wm_type_both.setText(T('watermark.type_both'))
        self._wm_label_image.setText(T('watermark.image_label') + ':')
        self.wm_image_path_input.setPlaceholderText(T('watermark.image_placeholder'))
        self.wm_image_browse_btn.setText(T('app.browse'))
        self._wm_label_text.setText(T('watermark.text_label') + ':')
        self.wm_text_input.setPlaceholderText(T('watermark.text_placeholder'))
        self.wm_font_btn.setText(T('watermark.font_btn'))
        self._wm_label_font_size.setText(T('watermark.font_size') + ':')
        self._wm_label_margin_x.setText(T('watermark.margin_x') + ':')
        self._wm_label_margin_y.setText(T('watermark.margin_y') + ':')
        self._wm_label_opacity.setText(T('watermark.opacity') + ':')
        self._wm_label_scale.setText(T('watermark.scale') + ':')
        self.wm_scale_spin.setSuffix(T('watermark.percent'))
        self._wm_label_output_dir.setText(T('app.output_dir') + ':')
        self.wm_output_dir.setPlaceholderText(T('app.output_dir_placeholder'))
        self.wm_output_browse.setText(T('app.browse'))
        self.wm_overwrite.setText(T('app.overwrite_original'))
        self.wm_file_group.setTitle(T('watermark.task_title'))
        self.wm_start_btn.setText(T('watermark.start_btn'))
        self.wm_cancel_btn.setText(T('watermark.cancel_btn'))
        self.wm_add_btn.setText(T('app.add_files'))
        self.wm_remove_btn.setText(T('app.remove_selected'))
        self.wm_clear_btn.setText(T('app.clear_list'))
        self._wm_update_count()

    def on_wm_type_changed(self, btn):
        wm_type = self.wm_type_group.id(btn)
        self.wm_image_row.setVisible(wm_type in (0, 2))
        self.wm_text_row.setVisible(wm_type in (1, 2))
        self._rebuild_wm_preview()

    def on_wm_browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, T("app.select_watermark_image_title"), "",
            T("app.watermark_image_filter"),
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
            self.wm_font_btn.setText(T("watermark.font_label", name=font.family()))
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
        dir_path = QFileDialog.getExistingDirectory(self, T("app.select_output_dir"))
        if dir_path:
            self.wm_output_dir.setText(dir_path)

    def on_wm_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, T("app.select_image_files"), "",
            T("app.image_files_filter"),
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
        item = QListWidgetItem(f"{Path(file_path).name}  ({self._format_size(size)})")
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
        self.wm_file_count.setText(T("app.file_count", count=self.wm_file_list.count()))

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
            QMessageBox.warning(self, T("app.warning"), T("app.add_files_first_wm"))
            return

        wm_type_id = self.wm_type_group.checkedId()
        type_map = {0: "image", 1: "text", 2: "both"}
        wm_type = type_map.get(wm_type_id, "image")

        if wm_type in ("image", "both") and not self.wm_image_path_input.text():
            QMessageBox.warning(self, T("app.warning"), T("app.select_watermark_image"))
            return
        if wm_type in ("text", "both") and not self.wm_text_input.text().strip():
            QMessageBox.warning(self, T("app.warning"), T("app.enter_watermark_text"))
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
        self._wm_log(T("watermark.finished"))
        self._wm_log(T("compress.stats_total", count=stats['total']))
        self._wm_log(T("compress.stats_success", count=stats['success']))
        self._wm_log(T("compress.stats_fail", count=stats['fail']))
        QMessageBox.information(self, T("app.done"), T("watermark.done_msg", count=stats['success']))

    def on_wm_cancel(self):
        if hasattr(self, 'wm_worker') and self.wm_worker and self.wm_worker.isRunning():
            self.wm_worker.cancel()
            self._wm_log(T("worker.cancel_watermark"))

    @staticmethod
    def _format_size(size_bytes):
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024*1024):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes // 1024} KB"
        return f"{size_bytes} B"
