import os
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QProgressBar, QTextEdit, QFileDialog, QMessageBox,
    QLineEdit, QGroupBox, QSpinBox, QComboBox, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt

from i18n import T
from core.image_utils import generate_rename_preview
from core.workers.rename_worker import RenameWorker


class RenamePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.retranslate()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.rn_settings_group = QGroupBox()
        settings_layout = QVBoxLayout(self.rn_settings_group)

        pattern_layout = QHBoxLayout()
        self._rn_label_pattern = QLabel()
        pattern_layout.addWidget(self._rn_label_pattern)
        self.rn_pattern_input = QLineEdit()
        self.rn_pattern_input.textChanged.connect(self.on_rn_preview)
        pattern_layout.addWidget(self.rn_pattern_input)
        settings_layout.addLayout(pattern_layout)

        var_layout = QHBoxLayout()
        self._rn_label_insert_var = QLabel()
        var_layout.addWidget(self._rn_label_insert_var)
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
        settings_layout.addLayout(var_layout)

        self.hint = QLabel()
        self.hint.setStyleSheet("color: #888; font-size: 11px;")
        settings_layout.addWidget(self.hint)

        num_layout = QHBoxLayout()
        self._rn_label_start_index = QLabel()
        num_layout.addWidget(self._rn_label_start_index)
        self.rn_start_index = QSpinBox()
        self.rn_start_index.setRange(0, 999999)
        self.rn_start_index.setValue(1)
        self.rn_start_index.valueChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_start_index)

        num_layout.addSpacing(12)
        self._rn_label_pad_digits = QLabel()
        num_layout.addWidget(self._rn_label_pad_digits)
        self.rn_pad_digits = QSpinBox()
        self.rn_pad_digits.setRange(1, 10)
        self.rn_pad_digits.setValue(3)
        self.rn_pad_digits.valueChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_pad_digits)
        num_layout.addWidget(QLabel(" (001)"))

        num_layout.addSpacing(12)
        self._rn_label_date_format = QLabel()
        num_layout.addWidget(self._rn_label_date_format)
        self.rn_date_format = QComboBox()
        self.rn_date_format.addItem("YYYYMMDD", "%Y%m%d")
        self.rn_date_format.addItem("YYYY-MM-DD", "%Y-%m-%d")
        self.rn_date_format.addItem("YYMMDD", "%y%m%d")
        self.rn_date_format.currentIndexChanged.connect(self.on_rn_preview)
        num_layout.addWidget(self.rn_date_format)

        num_layout.addStretch()
        settings_layout.addLayout(num_layout)

        layout.addWidget(self.rn_settings_group)

        self.rn_file_group = QGroupBox()
        file_layout = QVBoxLayout(self.rn_file_group)

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
        file_layout.addWidget(self.rn_file_table)

        info_bar = QHBoxLayout()
        self.rn_file_count = QLabel()
        info_bar.addWidget(self.rn_file_count)
        info_bar.addStretch()
        file_layout.addLayout(info_bar)

        btn_bar = QHBoxLayout()
        self.rn_add_btn = QPushButton()
        self.rn_add_btn.clicked.connect(self.on_rn_add_files)
        self.rn_folder_btn = QPushButton()
        self.rn_folder_btn.clicked.connect(self.on_rn_add_folder)
        self.rn_remove_btn = QPushButton()
        self.rn_remove_btn.clicked.connect(self.on_rn_remove_selected)
        self.rn_clear_btn = QPushButton()
        self.rn_clear_btn.clicked.connect(self.on_rn_clear)
        btn_bar.addWidget(self.rn_add_btn)
        btn_bar.addWidget(self.rn_folder_btn)
        btn_bar.addWidget(self.rn_remove_btn)
        btn_bar.addWidget(self.rn_clear_btn)
        btn_bar.addStretch()
        file_layout.addLayout(btn_bar)

        layout.addWidget(self.rn_file_group, 1)

        ctrl = QHBoxLayout()
        self.rn_start_btn = QPushButton()
        self.rn_start_btn.setProperty('class', 'primary')
        self.rn_start_btn.clicked.connect(self.on_rn_start)
        ctrl.addWidget(self.rn_start_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self.rn_progress = QProgressBar()
        self.rn_progress.setVisible(False)
        layout.addWidget(self.rn_progress)

        self.rn_log = QTextEdit()
        self.rn_log.setReadOnly(True)
        from PyQt5.QtGui import QFont
        self.rn_log.setFont(QFont("Consolas", 9))
        self.rn_log.setMaximumHeight(160)
        layout.addWidget(self.rn_log)

    def retranslate(self):
        self._retranslate_rename_page()

    def _retranslate_rename_page(self):
        self.rn_settings_group.setTitle(T('rename.page_title'))
        self._rn_label_pattern.setText(T('rename.pattern') + ':')
        self.rn_pattern_input.setPlaceholderText(T('rename.pattern_placeholder'))
        self._rn_label_insert_var.setText(T('app.insert_var') + ':')
        self.hint.setText(T('rename.hint'))
        self._rn_label_start_index.setText(T('app.start_index') + ':')
        self._rn_label_pad_digits.setText(T('app.pad_digits') + ':')
        self._rn_label_date_format.setText(T('app.date_format') + ':')
        self.rn_file_group.setTitle(T('rename.task_title'))
        self.rn_file_table.setHorizontalHeaderLabels([
            T('app.original_name'), T('app.new_name'), T('app.path'),
        ])
        self.rn_start_btn.setText(T('rename.start_btn'))
        self.rn_add_btn.setText(T('app.add_files'))
        self.rn_folder_btn.setText(T('app.add_folder'))
        self.rn_remove_btn.setText(T('app.remove_selected'))
        self.rn_clear_btn.setText(T('app.clear_list'))
        self._rn_update_count()

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

    def on_rn_remove_selected(self):
        for item in self.rn_file_table.selectedItems():
            self.rn_file_table.removeRow(item.row())
        self._rn_update_count()
        self.on_rn_preview()

    def on_rn_clear(self):
        self.rn_file_table.setRowCount(0)
        self._rn_update_count()

    def _rn_update_count(self):
        self.rn_file_count.setText(T("app.file_count", count=self.rn_file_table.rowCount()))

    def _rn_get_paths(self):
        paths = []
        for i in range(self.rn_file_table.rowCount()):
            fp = self.rn_file_table.item(i, 2).text()
            if fp:
                paths.append(fp)
        return paths

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

    def _rn_log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
        self.rn_log.append(f"[{timestamp}] {prefix}{message}")

    def _rn_update_progress(self, current, total):
        self.rn_progress.setMaximum(total)
        self.rn_progress.setValue(current)

    def _rn_finished(self, stats):
        self.rn_start_btn.setEnabled(True)
        self.rn_progress.setVisible(False)
        self._rn_log(f"\n{'='*50}")
        self._rn_log(T("rename.finished"))
        self._rn_log(T("compress.stats_total", count=stats['total']))
        self._rn_log(T("compress.stats_success", count=stats['success']))
        self._rn_log(T("compress.stats_fail", count=stats['fail']))
        QMessageBox.information(self, T("app.done"), T("rename.done_msg", count=stats['success']))
        self.on_rn_clear()
