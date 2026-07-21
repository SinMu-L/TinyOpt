import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QLineEdit, QCheckBox,
    QAbstractItemView, QSpinBox, QSlider, QFrame,
    QFontDialog, QColorDialog, QButtonGroup, QRadioButton,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap

from i18n import T
from core.config import SUPPORTED_EXTENSIONS
from core.utils import find_font_path
from core.image_utils import render_text_watermark
from core.workers.watermark_worker import WatermarkWorker
from widgets.drop_zone import DropZone
from widgets.position_preview import PositionPreviewWidget


class WatermarkPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wm_font_family = "\u5fae\u8f6f\u96c5\u9ed1"
        self.wm_font_color = (255, 255, 255)
        self._file_list_expanded = False
        self.build_watermark_page()

    # ── UI construction ──────────────────────────────────────────────

    def build_watermark_page(self):
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
        self.drop_zone.add_files_clicked.connect(self.on_wm_add_files)
        self.drop_zone.add_folder_clicked.connect(self.on_wm_add_folder)
        self.drop_zone.files_dropped.connect(self._on_wm_paths_dropped)
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
        self.wm_file_toggle = QPushButton()
        self.wm_file_toggle.setCursor(Qt.PointingHandCursor)
        self.wm_file_toggle.clicked.connect(self._toggle_file_list)
        left_col.addWidget(self.wm_file_toggle)

        # collapsible file list
        self.wm_file_list_widget = QWidget()
        self.wm_file_list_widget.setVisible(False)
        fl_layout = QVBoxLayout(self.wm_file_list_widget)
        fl_layout.setContentsMargins(0, 0, 0, 0)
        fl_layout.setSpacing(6)

        self.wm_file_list = QListWidget()
        self.wm_file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.wm_file_list.setMaximumHeight(120)
        fl_layout.addWidget(self.wm_file_list)

        fl_btns = QHBoxLayout()
        fl_btns.setSpacing(6)
        self.wm_add_btn = QPushButton()
        self.wm_add_btn.setProperty("class", "primary")
        self.wm_add_btn.clicked.connect(self.on_wm_add_files)
        self.wm_remove_btn = QPushButton()
        self.wm_remove_btn.clicked.connect(self.on_wm_remove_selected)
        self.wm_clear_btn = QPushButton()
        self.wm_clear_btn.clicked.connect(self.on_wm_clear)
        fl_btns.addWidget(self.wm_add_btn)
        fl_btns.addWidget(self.wm_remove_btn)
        fl_btns.addWidget(self.wm_clear_btn)
        fl_btns.addStretch()
        fl_layout.addLayout(fl_btns)

        left_col.addWidget(self.wm_file_list_widget)

        # position preview (stretches)
        self.wm_position_preview = PositionPreviewWidget()
        self.wm_position_preview.positionChanged.connect(self._on_wm_position_changed)
        self.wm_position_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_col.addWidget(self.wm_position_preview, 1)

        # action bar
        ctrl = QHBoxLayout()
        ctrl.addStretch()
        self.wm_start_btn = QPushButton()
        self.wm_start_btn.setProperty("class", "primary")
        self.wm_cancel_btn = QPushButton()
        self.wm_cancel_btn.setEnabled(False)
        self.wm_cancel_btn.setProperty("class", "danger")
        self.wm_start_btn.clicked.connect(self.on_wm_start)
        self.wm_cancel_btn.clicked.connect(self.on_wm_cancel)
        ctrl.addWidget(self.wm_cancel_btn)
        ctrl.addWidget(self.wm_start_btn)
        left_col.addLayout(ctrl)

        self.wm_progress = QProgressBar()
        self.wm_progress.setVisible(False)
        left_col.addWidget(self.wm_progress)

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

        # type selection
        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        self._wm_label_type = QLabel()
        self._wm_label_type.setObjectName("settingsLabel")
        type_row.addWidget(self._wm_label_type)
        self.wm_type_group = QButtonGroup(self)
        self.wm_type_image = QRadioButton()
        self.wm_type_text = QRadioButton()
        self.wm_type_both = QRadioButton()
        self.wm_type_group.addButton(self.wm_type_image, 0)
        self.wm_type_group.addButton(self.wm_type_text, 1)
        self.wm_type_group.addButton(self.wm_type_both, 2)
        self.wm_type_group.buttonClicked.connect(self.on_wm_type_changed)
        self.wm_type_image.setChecked(True)
        type_row.addWidget(self.wm_type_image)
        type_row.addWidget(self.wm_type_text)
        type_row.addWidget(self.wm_type_both)
        type_row.addStretch()
        sr.addLayout(type_row)

        # image watermark row
        self.wm_image_row = QWidget()
        wm_img_layout = QVBoxLayout(self.wm_image_row)
        wm_img_layout.setContentsMargins(0, 0, 0, 0)
        wm_img_layout.setSpacing(6)

        img_top = QHBoxLayout()
        img_top.setSpacing(4)
        self._wm_label_image = QLabel()
        self._wm_label_image.setObjectName("settingsLabel")
        img_top.addWidget(self._wm_label_image)
        img_top.addStretch()
        self.wm_image_browse_btn = QPushButton()
        self.wm_image_browse_btn.setFixedWidth(56)
        self.wm_image_browse_btn.clicked.connect(self.on_wm_browse_image)
        img_top.addWidget(self.wm_image_browse_btn)
        wm_img_layout.addLayout(img_top)

        img_bot = QHBoxLayout()
        img_bot.setSpacing(6)
        self.wm_image_path_input = QLineEdit()
        img_bot.addWidget(self.wm_image_path_input, 1)
        self.wm_image_preview = QLabel()
        self.wm_image_preview.setFixedSize(40, 40)
        self.wm_image_preview.setStyleSheet("border: 1px solid #d1d5db; background: #f9fafb; border-radius: 4px;")
        img_bot.addWidget(self.wm_image_preview)
        wm_img_layout.addLayout(img_bot)

        img_scale_row = QHBoxLayout()
        img_scale_row.setSpacing(6)
        self._wm_label_image_scale = QLabel()
        img_scale_row.addWidget(self._wm_label_image_scale)
        self.wm_image_scale_spin = QSpinBox()
        self.wm_image_scale_spin.setRange(1, 100)
        self.wm_image_scale_spin.setValue(15)
        self.wm_image_scale_spin.setSuffix(" %")
        self.wm_image_scale_spin.valueChanged.connect(self._rebuild_wm_preview)
        img_scale_row.addWidget(self.wm_image_scale_spin)
        self._wm_label_image_rot = QLabel()
        img_scale_row.addWidget(self._wm_label_image_rot)
        self.wm_image_rotation_spin = QSpinBox()
        self.wm_image_rotation_spin.setRange(0, 360)
        self.wm_image_rotation_spin.setValue(0)
        self.wm_image_rotation_spin.setSuffix("\u00b0")
        self.wm_image_rotation_spin.valueChanged.connect(self._rebuild_wm_preview)
        img_scale_row.addWidget(self.wm_image_rotation_spin)
        img_scale_row.addStretch()
        wm_img_layout.addLayout(img_scale_row)

        sr.addWidget(self.wm_image_row)

        # text watermark row
        self.wm_text_row = QWidget()
        self.wm_text_row.setVisible(False)
        wm_txt_outer = QVBoxLayout(self.wm_text_row)
        wm_txt_outer.setContentsMargins(0, 0, 0, 0)
        wm_txt_outer.setSpacing(6)

        self._wm_label_text = QLabel()
        self._wm_label_text.setObjectName("settingsLabel")
        wm_txt_outer.addWidget(self._wm_label_text)
        self.wm_text_input = QLineEdit()
        self.wm_text_input.textChanged.connect(self._rebuild_wm_preview)
        wm_txt_outer.addWidget(self.wm_text_input)

        wm_txt_bot = QHBoxLayout()
        wm_txt_bot.setSpacing(6)
        self.wm_font_btn = QPushButton()
        self.wm_font_btn.clicked.connect(self.on_wm_select_font)
        wm_txt_bot.addWidget(self.wm_font_btn)
        self._wm_label_font_size = QLabel()
        wm_txt_bot.addWidget(self._wm_label_font_size)
        self.wm_font_size_spin = QSpinBox()
        self.wm_font_size_spin.setRange(8, 500)
        self.wm_font_size_spin.setValue(48)
        self.wm_font_size_spin.setSuffix(" px")
        self.wm_font_size_spin.valueChanged.connect(self._rebuild_wm_preview)
        wm_txt_bot.addWidget(self.wm_font_size_spin)
        self.wm_color_btn = QPushButton()
        self.wm_color_btn.setFixedSize(28, 28)
        self.wm_color_btn.setStyleSheet("background-color: white; border: 1px solid #999; border-radius: 4px;")
        self.wm_color_btn.clicked.connect(self.on_wm_select_color)
        wm_txt_bot.addWidget(self.wm_color_btn)
        wm_txt_bot.addStretch()
        wm_txt_outer.addLayout(wm_txt_bot)

        txt_scale_row = QHBoxLayout()
        txt_scale_row.setSpacing(6)
        self._wm_label_text_scale = QLabel()
        txt_scale_row.addWidget(self._wm_label_text_scale)
        self.wm_text_scale_spin = QSpinBox()
        self.wm_text_scale_spin.setRange(1, 100)
        self.wm_text_scale_spin.setValue(15)
        self.wm_text_scale_spin.setSuffix(" %")
        self.wm_text_scale_spin.valueChanged.connect(self._rebuild_wm_preview)
        txt_scale_row.addWidget(self.wm_text_scale_spin)
        self._wm_label_text_rot = QLabel()
        txt_scale_row.addWidget(self._wm_label_text_rot)
        self.wm_text_rotation_spin = QSpinBox()
        self.wm_text_rotation_spin.setRange(0, 360)
        self.wm_text_rotation_spin.setValue(0)
        self.wm_text_rotation_spin.setSuffix("\u00b0")
        self.wm_text_rotation_spin.valueChanged.connect(self._rebuild_wm_preview)
        txt_scale_row.addWidget(self.wm_text_rotation_spin)
        txt_scale_row.addStretch()
        wm_txt_outer.addLayout(txt_scale_row)

        sr.addWidget(self.wm_text_row)

        # separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep1)

        # opacity
        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(6)
        self._wm_label_opacity = QLabel()
        opacity_row.addWidget(self._wm_label_opacity)
        self.wm_opacity_slider = QSlider(Qt.Horizontal)
        self.wm_opacity_slider.setRange(1, 100)
        self.wm_opacity_slider.setValue(80)
        self.wm_opacity_slider.valueChanged.connect(self.on_wm_opacity_changed)
        opacity_row.addWidget(self.wm_opacity_slider, 1)
        self.wm_opacity_label = QLabel("80%")
        self.wm_opacity_label.setFixedWidth(35)
        opacity_row.addWidget(self.wm_opacity_label)
        sr.addLayout(opacity_row)

        # separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep2)

        # output dir
        self._wm_label_output_dir = QLabel()
        self._wm_label_output_dir.setObjectName("settingsLabel")
        sr.addWidget(self._wm_label_output_dir)

        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.wm_output_dir = QLineEdit()
        self.wm_output_browse = QPushButton()
        self.wm_output_browse.setFixedWidth(56)
        self.wm_output_browse.clicked.connect(self.on_wm_browse_output)
        out_row.addWidget(self.wm_output_dir, 1)
        out_row.addWidget(self.wm_output_browse)
        sr.addLayout(out_row)

        self.wm_overwrite = QCheckBox()
        sr.addWidget(self.wm_overwrite)

        # log label
        self._wm_label_log = QLabel()
        self._wm_label_log.setObjectName("settingsLabel")
        sr.addWidget(self._wm_label_log)

        self.wm_log = QTextEdit()
        self.wm_log.setReadOnly(True)
        self.wm_log.setFont(QFont("Consolas", 9))
        self.wm_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sr.addWidget(self.wm_log, 1)

        split.addWidget(self.settings_panel, 3)

        content_root.addLayout(split)
        outer.addWidget(self.content_widget, 1)

        self._sync_empty_state()

    # ── i18n ─────────────────────────────────────────────────────────

    def retranslate(self):
        self.page_title.setText(T("watermark.page_title"))
        sub = T("watermark.hero_subtitle")
        self.page_subtitle.setText(sub if not sub.startswith("watermark.") else "\u62d6\u5165\u591a\u5f20\u56fe\u7247\uff0c\u7edf\u4e00\u6dfb\u52a0\u6587\u5b57\u6216\u56fe\u7247\u6c34\u5370")
        self.drop_zone.set_texts(
            T("compress.drop_title"),
            T("compress.drop_hint"),
            T("app.add_files"),
            T("app.add_folder"),
        )
        self.settings_title.setText(T("watermark.page_title"))
        self._wm_label_type.setText(T("watermark.type") + ":")
        self.wm_type_image.setText(T("watermark.type_image"))
        self.wm_type_text.setText(T("watermark.type_text"))
        self.wm_type_both.setText(T("watermark.type_both"))
        self._wm_label_image.setText(T("watermark.image_label"))
        self.wm_image_path_input.setPlaceholderText(T("watermark.image_placeholder"))
        self.wm_image_browse_btn.setText(T("app.browse"))
        self._wm_label_text.setText(T("watermark.text_label"))
        self.wm_text_input.setPlaceholderText(T("watermark.text_placeholder"))
        self.wm_font_btn.setText(T("watermark.font_btn"))
        self._wm_label_font_size.setText(T("watermark.font_size") + ":")
        self._wm_label_opacity.setText(T("watermark.opacity") + ":")
        self._wm_label_image_scale.setText(T("watermark.scale") + ":")
        self._wm_label_image_rot.setText(T("watermark.rotation") + ":")
        self._wm_label_text_scale.setText(T("watermark.scale") + ":")
        self._wm_label_text_rot.setText(T("watermark.rotation") + ":")
        self._wm_label_output_dir.setText(T("app.output_dir") + ":")
        self.wm_output_dir.setPlaceholderText(T("app.output_dir_placeholder"))
        self.wm_output_browse.setText(T("app.browse"))
        self.wm_overwrite.setText(T("app.overwrite_original"))
        log_title = T("watermark.log_title")
        self._wm_label_log.setText(log_title if not log_title.startswith("watermark.") else T("compress.log_title"))
        self.wm_start_btn.setText(T("watermark.start_btn"))
        self.wm_cancel_btn.setText(T("watermark.cancel_btn"))
        self.wm_add_btn.setText(T("app.add_files"))
        self.wm_remove_btn.setText(T("app.remove_selected"))
        self.wm_clear_btn.setText(T("app.clear_list"))
        self._wm_update_count()

    # ── empty / file state ───────────────────────────────────────────

    def _sync_empty_state(self):
        has_files = self.wm_file_list.count() > 0
        self.drop_zone.setVisible(not has_files)
        self.content_widget.setVisible(has_files)

    def _update_file_toggle(self):
        count = self.wm_file_list.count()
        arrow = "\u25be" if self._file_list_expanded else "\u25b8"
        self.wm_file_toggle.setText("\u5171 {} \u4e2a\u6587\u4ef6 {}".format(count, arrow))

    def _toggle_file_list(self):
        self._file_list_expanded = not self._file_list_expanded
        self.wm_file_list_widget.setVisible(self._file_list_expanded)
        self._update_file_toggle()

    # ── file management ──────────────────────────────────────────────

    def _on_wm_paths_dropped(self, paths):
        for path in paths:
            if os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    self._wm_add_item(path)
            elif os.path.isdir(path):
                for root, _dirs, files in os.walk(path):
                    for file in files:
                        if Path(file).suffix.lower() in SUPPORTED_EXTENSIONS:
                            self._wm_add_item(os.path.join(root, file))
        self._wm_update_count()
        self._wm_update_preview()

    def on_wm_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, T("app.select_image_files"), "",
            T("app.image_files_filter"),
        )
        for f in files:
            self._wm_add_item(f)
        self._wm_update_count()
        self._wm_update_preview()

    def on_wm_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, T("app.select_folder"))
        if folder:
            supported_ext = SUPPORTED_EXTENSIONS
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if Path(file).suffix.lower() in supported_ext:
                        self._wm_add_item(os.path.join(root, file))
        self._wm_update_count()
        self._wm_update_preview()

    def _wm_add_item(self, file_path):
        if not os.path.isfile(file_path):
            return
        for i in range(self.wm_file_list.count()):
            if self.wm_file_list.item(i).data(Qt.UserRole) == file_path:
                return
        size = os.path.getsize(file_path)
        item = QListWidgetItem(f"{file_path}  ({self._format_size(size)})")
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
        self._update_file_toggle()
        self._sync_empty_state()

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

    # ── settings callbacks ───────────────────────────────────────────

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
                pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
                f"background-color: {color.name()}; border: 1px solid #999; border-radius: 4px;"
            )
            self._rebuild_wm_preview()

    def on_wm_opacity_changed(self, val):
        self.wm_opacity_label.setText(f"{val}%")
        self.wm_position_preview.set_opacity(val)

    def _on_wm_position_changed(self, x_ratio, y_ratio):
        pass

    def on_wm_browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, T("app.select_output_dir"))
        if dir_path:
            self.wm_output_dir.setText(dir_path)

    def _rebuild_wm_preview(self):
        wm_type_id = self.wm_type_group.checkedId()
        type_map = {0: "image", 1: "text", 2: "both"}
        wm_type = type_map.get(wm_type_id, "image")

        image_scale = self.wm_image_scale_spin.value()
        image_rotation = self.wm_image_rotation_spin.value()
        text_scale = self.wm_text_scale_spin.value()
        text_rotation = self.wm_text_rotation_spin.value()
        pw = self.wm_position_preview

        wm_pil = None

        if wm_type in ("image", "both"):
            img_path = self.wm_image_path_input.text().strip()
            if img_path and os.path.isfile(img_path):
                try:
                    wm_img = Image.open(img_path)
                    if wm_img.mode != 'RGBA':
                        wm_img = wm_img.convert('RGBA')
                    disp_w = max(10, int((pw.width() - 4) * image_scale / 100))
                    wm_h = max(1, int(wm_img.height * disp_w / wm_img.width))
                    wm_img = wm_img.resize((disp_w, wm_h), Image.LANCZOS)
                    if image_rotation:
                        wm_img = wm_img.rotate(image_rotation, expand=True, resample=Image.BICUBIC)
                    wm_pil = wm_img
                except:
                    pass

        if wm_type in ("text", "both"):
            text = self.wm_text_input.text().strip()
            if text:
                font_path = find_font_path(self.wm_font_family)
                disp_font_size = min(50, max(8, self.wm_font_size_spin.value() // 2))
                txt_pil = render_text_watermark(text, font_path, disp_font_size, self.wm_font_color)
                disp_w = max(10, int((pw.width() - 4) * text_scale / 100))
                txt_h = max(1, int(txt_pil.height * disp_w / txt_pil.width))
                txt_pil = txt_pil.resize((disp_w, txt_h), Image.LANCZOS)
                if text_rotation:
                    txt_pil = txt_pil.rotate(text_rotation, expand=True, resample=Image.BICUBIC)
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

    # ── compress workflow ────────────────────────────────────────────

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
            self.wm_image_scale_spin.value(),
            self.wm_text_scale_spin.value(),
            0,  # margin_x — removed, replaced by drag positioning
            0,  # margin_y — removed, replaced by drag positioning
            self.wm_image_rotation_spin.value(),
            self.wm_text_rotation_spin.value(),
        )
        self.wm_worker.progress.connect(self._wm_update_progress)
        self.wm_worker.log.connect(self._wm_log)
        self.wm_worker.finished_signal.connect(self._wm_finished)
        self.wm_worker.start()

    def _wm_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
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
