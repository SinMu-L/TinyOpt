import sys
import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QListWidget, QStackedWidget, QComboBox, QSplitter,
    QMessageBox, QAbstractItemView, QCheckBox, QSpinBox, QGroupBox, QPushButton,
    QTextEdit, QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSlider, QDialog, QFormLayout, QSpinBox,
    QDialogButtonBox, QFontDialog, QColorDialog, QButtonGroup, QRadioButton,
    QGraphicsView, QGraphicsScene, QProgressBar, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QRect, QRectF, QPointF
from PyQt5.QtGui import (QDragEnterEvent, QDropEvent, QFont, QColor, QBrush, QIcon,
    QPixmap, QPainter, QPen, QPolygonF, QPainterPath, QTransform)
from PIL import Image, ImageDraw, ImageFont

from i18n import T, set_language, get_language, on_language_change

from core.config import SUPPORTED_EXTENSIONS, FORMATS, DEFAULT_FORMAT, RESIZE_METHODS, DEFAULT_RESIZE_METHOD, load_config, save_config
from core.key_manager import KeyManager
from core.pages.compress_page import CompressPage
from core.pages.watermark_page import WatermarkPage
from core.pages.rename_page import RenamePage
from core.pages.ratio_page import RatioPage
from core.pages.key_page import KeyPage
from core.pages.history_page import HistoryPage
from core.pages.website_page import WebsitePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 700)
        self.worker = None
        self.config = load_config()
        self.key_manager = KeyManager.from_config(self.config)
        self.init_ui()
        self.load_settings()
        on_language_change(self.retranslate_ui)
        self.retranslate_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar_widget = QWidget()
        sidebar_widget.setObjectName('sidebarWidget')
        sidebar_widget.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName('sidebar')
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.addItem("\U0001f4c1  " + T("sidebar.compress").strip())
        self.sidebar.addItem("\U0001f4a7  " + T("sidebar.watermark").strip())
        self.sidebar.addItem("\U0001f4dd  " + T("sidebar.rename").strip())
        self.sidebar.addItem("\U0001f4d0  " + T("sidebar.ratio").strip())
        self.sidebar.addItem("\U0001f511  " + T("sidebar.key_manage").strip())
        self.sidebar.addItem("\U0001f4ca  " + T("sidebar.history").strip())
        self.sidebar.addItem("\U0001f310  " + T("sidebar.website").strip())
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)
        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName('langCombo')
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(0 if get_language() == "zh" else 1)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        self.lang_combo.setMaximumWidth(164)
        sidebar_layout.addWidget(self.sidebar, 1)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(self.lang_combo)

        root.addWidget(sidebar_widget)

        self.compress_page = CompressPage(self.config, self.key_manager)
        self.watermark_page = WatermarkPage()
        self.rename_page = RenamePage()
        self.ratio_page = RatioPage()
        self.key_page = KeyPage(self.config, self.key_manager)
        self.history_page = HistoryPage(self.config)
        self.website_page = WebsitePage(self.config)

        self.compress_page.log_message.connect(self._on_page_log)
        self.compress_page.keys_changed.connect(self._on_keys_changed)
        self.compress_page.history_updated.connect(self._on_history_updated)
        self.key_page.log_message.connect(self._on_page_log)
        self.key_page.keys_changed.connect(self._on_keys_changed)
        self.website_page.log_message.connect(self._on_page_log)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.compress_page)   # 0
        self.stack.addWidget(self.watermark_page)   # 1
        self.stack.addWidget(self.rename_page)      # 2
        self.stack.addWidget(self.ratio_page)       # 3
        self.stack.addWidget(self.key_page)         # 4
        self.stack.addWidget(self.history_page)     # 5
        self.stack.addWidget(self.website_page)     # 6
        root.addWidget(self.stack, 1)

    def _on_lang_changed(self, idx):
        lang = self.lang_combo.itemData(idx)
        set_language(lang)
        self.config['language'] = lang
        save_config(self.config)

    def retranslate_ui(self):
        self.setWindowTitle(T('app.title'))
        self.sidebar.item(0).setText('\U0001f4c1  ' + T('sidebar.compress').strip())
        self.sidebar.item(1).setText('\U0001f4a7  ' + T('sidebar.watermark').strip())
        self.sidebar.item(2).setText('\U0001f4dd  ' + T('sidebar.rename').strip())
        self.sidebar.item(3).setText('\U0001f4d0  ' + T('sidebar.ratio').strip())
        self.sidebar.item(4).setText('\U0001f511  ' + T('sidebar.key_manage').strip())
        self.sidebar.item(5).setText('\U0001f4ca  ' + T('sidebar.history').strip())
        self.sidebar.item(6).setText('\U0001f310  ' + T('sidebar.website').strip())
        for page in [self.compress_page, self.watermark_page, self.rename_page,
                     self.ratio_page, self.key_page, self.history_page,
                     self.website_page]:
            page.retranslate()

    def on_sidebar_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index == 5:
            self.history_page.refresh_history_table()

    def load_settings(self):
        self.compress_page.load_settings()
        saved_lang = self.config.get("language", "zh")
        idx = self.lang_combo.findData(saved_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.key_page.refresh_key_table()
        self.key_manager.refresh_all_usage()
        self.key_page.refresh_key_table()

    def save_settings(self):
        self.compress_page.save_settings()
        self.key_manager.save(self.config)

    def _on_page_log(self, message, is_error=False):
        pass

    def _on_keys_changed(self):
        self.save_settings()

    def _on_history_updated(self):
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
                    self.rename_page._rn_add_item(file_path)
                elif ext in SUPPORTED_EXTENSIONS:
                    if current_idx == 0:
                        self.compress_page.add_item_to_list(file_path)
                    elif current_idx == 1:
                        self.watermark_page._wm_add_item(file_path)
                    elif current_idx == 3:
                        self.ratio_page._ratio_add_item(file_path)
            elif os.path.isdir(file_path):
                supported_ext = SUPPORTED_EXTENSIONS
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        full = os.path.join(root, file)
                        if current_idx == 2:
                            self.rename_page._rn_add_item(full)
                        elif Path(file).suffix.lower() in supported_ext:
                            if current_idx == 0:
                                self.compress_page.add_item_to_list(full)
                            elif current_idx == 1:
                                self.watermark_page._wm_add_item(full)
                            elif current_idx == 3:
                                self.ratio_page._ratio_add_item(full)
        if current_idx == 0:
            self.compress_page.update_file_summary()
        elif current_idx == 1:
            self.watermark_page._wm_update_count()
            self.watermark_page._wm_update_preview()
        elif current_idx == 2:
            self.rename_page._rn_update_count()
            self.rename_page.on_rn_preview()
        elif current_idx == 3:
            self.ratio_page._ratio_update_count()
            self.ratio_page._ratio_update_preview()
        event.acceptProposedAction()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TinyJPG Compressor")
    app.setStyleSheet(APP_STYLESHEET)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    if os.path.isfile(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    window = MainWindow()
    if os.path.isfile(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec_())

APP_STYLESHEET = """
QMainWindow, QDialog {
    background: #ffffff;
}

QWidget#sidebarWidget {
    background: #f8fafc;
}

QListWidget#sidebar {
    background: #f8fafc;
    border: none;
    border-right: 1px solid #e2e8f0;
    font-size: 13px;
    outline: none;
}
QListWidget#sidebar::item {
    padding: 12px 16px 12px 14px;
    border-left: 3px solid transparent;
    color: #475569;
}
QListWidget#sidebar::item:selected {
    background: #eff6ff;
    color: #2563eb;
    border-left: 3px solid #2563eb;
    font-weight: 600;
}
QListWidget#sidebar::item:hover:!selected {
    background: #f1f5f9;
    color: #334155;
}

QComboBox#langCombo {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 10px;
    color: #475569;
    font-size: 12px;
}
QComboBox#langCombo::drop-down {
    border: none;
    width: 20px;
}
QComboBox#langCombo QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #475569;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: #1e293b;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #2563eb;
    font-size: 13px;
}

QPushButton {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 7px 16px;
    background: #ffffff;
    color: #475569;
    font-size: 13px;
}
QPushButton:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
}
QPushButton:pressed {
    background: #f1f5f9;
}
QPushButton[class="primary"] {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
    font-weight: 600;
}
QPushButton[class="primary"]:hover {
    background: #1d4ed8;
}
QPushButton[class="primary"]:pressed {
    background: #1e40af;
}
QPushButton[class="danger"] {
    background: #ef4444;
    color: #ffffff;
    border: 1px solid #ef4444;
    font-weight: 600;
}
QPushButton[class="danger"]:hover {
    background: #dc2626;
}
QPushButton[class="danger"]:pressed {
    background: #b91c1c;
}
QPushButton:disabled {
    background: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

QListWidget {
    background: #f8fafc;
    border: 2px dashed #cbd5e1;
    border-radius: 8px;
    padding: 8px;
    color: #475569;
}
QListWidget::item {
    padding: 6px 8px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background: #dbeafe;
    color: #1e40af;
}
QListWidget::item:hover:!selected {
    background: #f1f5f9;
}

QLineEdit {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 10px;
    background: #ffffff;
    color: #1e293b;
}
QLineEdit:focus {
    border-color: #2563eb;
}

QComboBox {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 6px 10px;
    background: #ffffff;
    color: #1e293b;
}
QComboBox:hover {
    border-color: #cbd5e1;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #1e293b;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
}

QSpinBox {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 4px 8px;
    background: #ffffff;
    color: #1e293b;
}
QSpinBox:focus {
    border-color: #2563eb;
}

QCheckBox, QRadioButton {
    spacing: 6px;
    color: #475569;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background: #e2e8f0;
    height: 8px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6);
    border-radius: 4px;
}

QTableWidget {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    background: #ffffff;
    gridline-color: #f1f5f9;
}
QTableWidget::item {
    padding: 6px 8px;
    color: #475569;
}
QTableWidget::item:selected {
    background: #eff6ff;
    color: #2563eb;
}
QHeaderView::section {
    background: #f8fafc;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}

QSplitter::handle {
    background: #e2e8f0;
    height: 2px;
}
QSplitter::handle:hover {
    background: #2563eb;
}

QTextEdit {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    background: #f8fafc;
    color: #475569;
    padding: 8px;
}

QLabel {
    color: #475569;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2563eb;
    border: 2px solid #ffffff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #2563eb;
    border-radius: 3px;
}
"""


if __name__ == "__main__":
    main()
