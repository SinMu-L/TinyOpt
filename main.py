import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QStackedWidget, QComboBox, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon

from i18n import T, set_language, get_language, on_language_change
from styles.theme import APP_STYLESHEET

from core.config import SUPPORTED_EXTENSIONS, load_config, save_config
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
        self.setMinimumSize(1000, 720)
        self.setAcceptDrops(True)
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
        sidebar_widget.setFixedWidth(170)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(12, 16, 12, 12)
        sidebar_layout.setSpacing(8)

        brand = QFrame()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(8, 0, 8, 8)
        brand_layout.setSpacing(2)
        self.brand_title = QLabel()
        self.brand_title.setObjectName('brandTitle')
        self.brand_subtitle = QLabel()
        self.brand_subtitle.setObjectName('brandSubtitle')
        brand_layout.addWidget(self.brand_title)
        brand_layout.addWidget(self.brand_subtitle)
        sidebar_layout.addWidget(brand)

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
        self.lang_combo.addItem("\U0001f310  中文", "zh")
        self.lang_combo.addItem("\U0001f310  English", "en")
        self.lang_combo.setCurrentIndex(0 if get_language() == "zh" else 1)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        sidebar_layout.addWidget(self.sidebar, 1)
        sidebar_layout.addWidget(self.lang_combo)

        root.addWidget(sidebar_widget)

        content_host = QWidget()
        content_host.setObjectName('contentHost')
        content_layout = QVBoxLayout(content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

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
        content_layout.addWidget(self.stack)
        root.addWidget(content_host, 1)

    def _on_lang_changed(self, idx):
        lang = self.lang_combo.itemData(idx)
        set_language(lang)
        self.config['language'] = lang
        save_config(self.config)

    def retranslate_ui(self):
        self.setWindowTitle(T('app.title'))
        self.brand_title.setText(T('app.brand_name'))
        self.brand_subtitle.setText(T('app.brand_tagline'))
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
                    self.rename_page.rn_add_item_direct(file_path)
                elif ext in SUPPORTED_EXTENSIONS:
                    if current_idx == 0:
                        self.compress_page.add_item_to_list(file_path)
                    elif current_idx == 1:
                        self.watermark_page._wm_add_item(file_path)
                    elif current_idx == 3:
                        self.ratio_page.ratio_add_item_direct(file_path)
            elif os.path.isdir(file_path):
                supported_ext = SUPPORTED_EXTENSIONS
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        full = os.path.join(root, file)
                        if current_idx == 2:
                            self.rename_page.rn_add_item_direct(full)
                        elif Path(file).suffix.lower() in supported_ext:
                            if current_idx == 0:
                                self.compress_page.add_item_to_list(full)
                            elif current_idx == 1:
                                self.watermark_page._wm_add_item(full)
                            elif current_idx == 3:
                                self.ratio_page.ratio_add_item_direct(full)
        if current_idx == 0:
            self.compress_page.update_file_summary()
        elif current_idx == 1:
            self.watermark_page._wm_update_count()
            self.watermark_page._wm_update_preview()
        elif current_idx == 2:
            self.rename_page.rn_refresh_after_drop()
        elif current_idx == 3:
            self.ratio_page.ratio_refresh_after_drop()
        event.acceptProposedAction()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TinyOpt")
    app.setStyleSheet(APP_STYLESHEET)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    if os.path.isfile(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
