import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QLineEdit, QSpinBox, QComboBox, QHeaderView,
    QAbstractItemView, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from i18n import T
from core.image_utils import generate_rename_preview
from core.workers.rename_worker import RenameWorker
from widgets.drop_zone import DropZone


class RenamePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_list_expanded = False
        self.build_rename_page()

    # ── UI construction ──────────────────────────────────────────────

    def build_rename_page(self):
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
        self.drop_zone.add_files_clicked.connect(self.on_rn_add_files)
        self.drop_zone.add_folder_clicked.connect(self.on_rn_add_folder)
        self.drop_zone.files_dropped.connect(self._on_rn_paths_dropped)
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
        self.rn_file_toggle = QPushButton()
        self.rn_file_toggle.setCursor(Qt.PointingHandCursor)
        self.rn_file_toggle.clicked.connect(self._toggle_file_list)
        left_col.addWidget(self.rn_file_toggle)

        # collapsible file list
        self.rn_file_list_widget = QWidget()
        self.rn_file_list_widget.setVisible(False)
        fl_layout = QVBoxLayout(self.rn_file_list_widget)
        fl_layout.setContentsMargins(0, 0, 0, 0)
        fl_layout.setSpacing(6)

        self.rn_file_table = QTableWidget()
        self.rn_file_table.setColumnCount(3)
        self.rn_file_table.setHorizontalHeaderLabels([
            T('app.original_name'), T('app.new_name'), T('app.path'),
        ])
        self.rn_file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rn_file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rn_file_table.setColumnHidden(2, True)
        self.rn_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rn_file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.rn_file_table.verticalHeader().setVisible(False)
        self.rn_file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rn_file_table.setMaximumHeight(200)
        fl_layout.addWidget(self.rn_file_table)

        fl_btns = QHBoxLayout()
        fl_btns.setSpacing(6)
        self.rn_add_btn = QPushButton()
        self.rn_add_btn.setProperty("class", "primary")
        self.rn_add_btn.clicked.connect(self.on_rn_add_files)
        self.rn_folder_btn = QPushButton()
        self.rn_folder_btn.clicked.connect(self.on_rn_add_folder)
        self.rn_remove_btn = QPushButton()
        self.rn_remove_btn.clicked.connect(self.on_rn_remove_selected)
        self.rn_clear_btn = QPushButton()
        self.rn_clear_btn.clicked.connect(self.on_rn_clear)
        fl_btns.addWidget(self.rn_add_btn)
        fl_btns.addWidget(self.rn_folder_btn)
        fl_btns.addWidget(self.rn_remove_btn)
        fl_btns.addWidget(self.rn_clear_btn)
        fl_btns.addStretch()
        fl_layout.addLayout(fl_btns)

        left_col.addWidget(self.rn_file_list_widget)

        # action bar
        ctrl = QHBoxLayout()
        ctrl.addStretch()
        self.rn_start_btn = QPushButton()
        self.rn_start_btn.setProperty("class", "primary")
        self.rn_cancel_btn = QPushButton()
        self.rn_cancel_btn.setEnabled(False)
        self.rn_cancel_btn.setProperty("class", "danger")
        self.rn_start_btn.clicked.connect(self.on_rn_start)
        self.rn_cancel_btn.clicked.connect(self.on_rn_cancel)
        ctrl.addWidget(self.rn_cancel_btn)
        ctrl.addWidget(self.rn_start_btn)
        left_col.addLayout(ctrl)

        self.rn_progress = QProgressBar()
        self.rn_progress.setVisible(False)
        left_col.addWidget(self.rn_progress)

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

        # pattern input
        self._rn_label_pattern = QLabel()
        self._rn_label_pattern.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_pattern)
        self.rn_pattern_input = QLineEdit()
        self.rn_pattern_input.textChanged.connect(self.on_rn_preview)
        sr.addWidget(self.rn_pattern_input)

        # variable buttons
        self._rn_label_insert_var = QLabel()
        self._rn_label_insert_var.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_insert_var)
        var_layout = QHBoxLayout()
        var_layout.setSpacing(6)
        self.rn_ins_name = QPushButton("{name}")
        self.rn_ins_name.clicked.connect(lambda: self.rn_insert_var("{name}"))
        self.rn_ins_index = QPushButton("{index}")
        self.rn_ins_index.clicked.connect(lambda: self.rn_insert_var("{index}"))
        self.rn_ins_date = QPushButton("{date}")
        self.rn_ins_date.clicked.connect(lambda: self.rn_insert_var("{date}"))
        var_layout.addWidget(self.rn_ins_name)
        var_layout.addWidget(self.rn_ins_index)
        var_layout.addWidget(self.rn_ins_date)
        var_layout.addStretch()
        sr.addLayout(var_layout)

        # hint
        self.hint = QLabel()
        self.hint.setStyleSheet("color: #888; font-size: 11px;")
        self.hint.setWordWrap(True)
        sr.addWidget(self.hint)

        # separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep1)

        # start index
        self._rn_label_start_index = QLabel()
        self._rn_label_start_index.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_start_index)
        self.rn_start_index = QSpinBox()
        self.rn_start_index.setRange(0, 999999)
        self.rn_start_index.setValue(1)
        self.rn_start_index.valueChanged.connect(self.on_rn_preview)
        sr.addWidget(self.rn_start_index)

        # pad digits
        self._rn_label_pad_digits = QLabel()
        self._rn_label_pad_digits.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_pad_digits)
        pad_row = QHBoxLayout()
        pad_row.setSpacing(6)
        self.rn_pad_digits = QSpinBox()
        self.rn_pad_digits.setRange(1, 10)
        self.rn_pad_digits.setValue(3)
        self.rn_pad_digits.valueChanged.connect(self.on_rn_preview)
        pad_row.addWidget(self.rn_pad_digits)
        pad_row.addWidget(QLabel(" (001)"))
        pad_row.addStretch()
        sr.addLayout(pad_row)

        # date format
        self._rn_label_date_format = QLabel()
        self._rn_label_date_format.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_date_format)
        self.rn_date_format = QComboBox()
        self.rn_date_format.addItem("YYYYMMDD", "%Y%m%d")
        self.rn_date_format.addItem("YYYY-MM-DD", "%Y-%m-%d")
        self.rn_date_format.addItem("YYMMDD", "%y%m%d")
        self.rn_date_format.currentIndexChanged.connect(self.on_rn_preview)
        sr.addWidget(self.rn_date_format)

        # separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("border: none; border-top: 1px solid #e5e7eb;")
        sr.addWidget(sep2)

        # log label
        self._rn_label_log = QLabel()
        self._rn_label_log.setObjectName("settingsLabel")
        sr.addWidget(self._rn_label_log)

        self.rn_log = QTextEdit()
        self.rn_log.setReadOnly(True)
        self.rn_log.setFont(QFont("Consolas", 9))
        self.rn_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sr.addWidget(self.rn_log, 1)

        split.addWidget(self.settings_panel, 3)

        content_root.addLayout(split)
        outer.addWidget(self.content_widget, 1)

        self._sync_empty_state()

    # ── i18n ─────────────────────────────────────────────────────────

    def retranslate(self):
        self.page_title.setText(T("rename.page_title"))
        self.page_subtitle.setText(T("rename.hero_subtitle"))
        self.drop_zone.set_texts(
            T("compress.drop_title"),
            T("compress.drop_hint"),
            T("app.add_files"),
            T("app.add_folder"),
        )
        self.settings_title.setText(T("rename.page_title"))
        self._rn_label_pattern.setText(T("rename.pattern") + ":")
        self.rn_pattern_input.setPlaceholderText(T("rename.pattern_placeholder"))
        self._rn_label_insert_var.setText(T("app.insert_var") + ":")
        self.hint.setText(T("rename.hint"))
        self._rn_label_start_index.setText(T("app.start_index") + ":")
        self._rn_label_pad_digits.setText(T("app.pad_digits") + ":")
        self._rn_label_date_format.setText(T("app.date_format") + ":")
        self._rn_label_log.setText(T("compress.log_title"))
        self.rn_start_btn.setText(T("rename.start_btn"))
        self.rn_cancel_btn.setText(T("app.cancel"))
        self.rn_add_btn.setText(T("app.add_files"))
        self.rn_folder_btn.setText(T("app.add_folder"))
        self.rn_remove_btn.setText(T("app.remove_selected"))
        self.rn_clear_btn.setText(T("app.clear_list"))
        self.rn_file_table.setHorizontalHeaderLabels([
            T('app.original_name'), T('app.new_name'), T('app.path'),
        ])
        self._rn_update_count()
        self._update_file_toggle()

    # ── empty / file state ───────────────────────────────────────────

    def _sync_empty_state(self):
        has_files = self.rn_file_table.rowCount() > 0
        self.drop_zone.setVisible(not has_files)
        self.content_widget.setVisible(has_files)

    def _update_file_toggle(self):
        count = self.rn_file_table.rowCount()
        arrow = "\u25be" if self._file_list_expanded else "\u25b8"
        text = T("app.file_count", count=count)
        self.rn_file_toggle.setText(f"{text} {arrow}")

    def _toggle_file_list(self):
        self._file_list_expanded = not self._file_list_expanded
        self.rn_file_list_widget.setVisible(self._file_list_expanded)
        self._update_file_toggle()

    # ── file management ──────────────────────────────────────────────

    def _on_rn_paths_dropped(self, paths):
        for path in paths:
            if os.path.isfile(path):
                self._rn_add_item(path)
            elif os.path.isdir(path):
                for root, _dirs, files in os.walk(path):
                    for file in files:
                        self._rn_add_item(os.path.join(root, file))
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, T("app.select_image_files"), "",
            T("app.all_files_filter"),
        )
        for f in files:
            self._rn_add_item(f)
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, T("app.select_folder"))
        if folder:
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    full = os.path.join(root, file)
                    if self._rn_add_item(full):
                        count += 1
            self._rn_update_count()
            self.on_rn_preview()
            if count > 0:
                self._rn_log(T("rename.add_folder_result", count=count))

    def on_rn_remove_selected(self):
        for item in self.rn_file_table.selectedItems():
            self.rn_file_table.removeRow(item.row())
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_clear(self):
        self.rn_file_table.setRowCount(0)
        self._rn_update_count()

    # ── public helpers (called by main.py drag-drop) ─────────────────

    def rn_add_item_direct(self, file_path):
        self._rn_add_item(file_path)

    def rn_refresh_after_drop(self):
        self._rn_update_count()
        self.on_rn_preview()

    # ── internal ─────────────────────────────────────────────────────

    def _rn_add_item(self, file_path):
        if not os.path.isfile(file_path):
            return False
        for i in range(self.rn_file_table.rowCount()):
            if self.rn_file_table.item(i, 2).text() == file_path:
                return False
        row = self.rn_file_table.rowCount()
        self.rn_file_table.insertRow(row)
        p = Path(file_path)
        self.rn_file_table.setItem(row, 0, QTableWidgetItem(p.name))
        self.rn_file_table.setItem(row, 1, QTableWidgetItem(""))
        self.rn_file_table.setItem(row, 2, QTableWidgetItem(file_path))
        return True

    def _rn_get_paths(self):
        paths = []
        for i in range(self.rn_file_table.rowCount()):
            fp = self.rn_file_table.item(i, 2).text()
            if fp:
                paths.append(fp)
        return paths

    def _rn_update_count(self):
        self._update_file_toggle()
        self._sync_empty_state()

    # ── rename logic ─────────────────────────────────────────────────

    def rn_insert_var(self, var):
        cursor = self.rn_pattern_input.cursorPosition()
        text = self.rn_pattern_input.text()
        new_text = text[:cursor] + var + text[cursor:]
        self.rn_pattern_input.setText(new_text)
        self.rn_pattern_input.setCursorPosition(cursor + len(var))

    def on_rn_preview(self):
        paths = self._rn_get_paths()
        if not paths:
            return
        pattern = self.rn_pattern_input.text().strip()
        if not pattern:
            for i in range(len(paths)):
                self.rn_file_table.setItem(i, 1, QTableWidgetItem(""))
            return
        previews = generate_rename_preview(
            paths, pattern,
            self.rn_start_index.value(),
            self.rn_pad_digits.value(),
            self.rn_date_format.currentData(),
        )
        for i, (_, new_name) in enumerate(previews):
            if i < self.rn_file_table.rowCount():
                self.rn_file_table.setItem(i, 1, QTableWidgetItem(new_name))

    def on_rn_start(self):
        paths = self._rn_get_paths()
        if not paths:
            QMessageBox.warning(self, T("app.warning"), T("app.add_files_first_rn"))
            return

        pattern = self.rn_pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, T("app.warning"), T("app.enter_pattern"))
            return

        if "{name}" not in pattern and "{index}" not in pattern and "{date}" not in pattern:
            confirm_msg = QMessageBox(self)
            confirm_msg.setIcon(QMessageBox.Question)
            confirm_msg.setWindowTitle(T("app.confirm"))
            confirm_msg.setText(T("app.no_variables_in_pattern"))
            confirm_yes = confirm_msg.addButton(T("app.yes"), QMessageBox.YesRole)
            confirm_msg.addButton(T("app.no"), QMessageBox.NoRole)
            confirm_msg.setDefaultButton(confirm_yes)
            confirm_msg.exec_()
            if confirm_msg.clickedButton() != confirm_yes:
                return

        self.rn_start_btn.setEnabled(False)
        self.rn_cancel_btn.setEnabled(True)
        self.rn_progress.setVisible(True)
        self.rn_progress.setValue(0)
        self.rn_log.clear()

        self.rn_worker = RenameWorker(
            paths, pattern,
            self.rn_start_index.value(),
            self.rn_pad_digits.value(),
            self.rn_date_format.currentData(),
        )
        self.rn_worker.progress.connect(self._rn_update_progress)
        self.rn_worker.log.connect(self._rn_log)
        self.rn_worker.finished_signal.connect(self._rn_finished)
        self.rn_worker.start()

    def on_rn_cancel(self):
        if hasattr(self, 'rn_worker') and self.rn_worker and self.rn_worker.isRunning():
            self.rn_worker.cancel()
            self._rn_log(T("worker.rename_cancelled"))

    def _rn_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
        self.rn_log.append(f"[{timestamp}] {prefix}{message}")

    def _rn_update_progress(self, current, total):
        self.rn_progress.setMaximum(total)
        self.rn_progress.setValue(current)

    def _rn_finished(self, stats):
        self.rn_start_btn.setEnabled(True)
        self.rn_cancel_btn.setEnabled(False)
        self.rn_progress.setVisible(False)
        self._rn_log(f"\n{'='*50}")
        self._rn_log(T("rename.finished"))
        self._rn_log(T("compress.stats_total", count=stats['total']))
        self._rn_log(T("compress.stats_success", count=stats['success']))
        self._rn_log(T("compress.stats_fail", count=stats['fail']))
        QMessageBox.information(self, T("app.done"), T("rename.done_msg", count=stats['success']))
        self.on_rn_clear()
