import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox,
    QTextEdit, QProgressBar, QLineEdit, QCheckBox, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from i18n import T
from core.utils import format_size
from core.workers.website_worker import WebsiteWorker


class WebsitePage(QWidget):
    log_message = pyqtSignal(str, bool)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.worker = None
        self._url_to_row = {}
        self._image_count = 0
        self._total_size = 0
        self.setup_ui()
        self.retranslate()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.settings_group = QGroupBox()
        settings_layout = QVBoxLayout(self.settings_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel(T("website.url_label")))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(T("website.url_placeholder"))
        row1.addWidget(self.url_input, 1)
        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(T("app.output_dir_placeholder"))
        self.browse_btn = QPushButton(T("app.browse"))
        self.browse_btn.clicked.connect(self._browse_output_dir)
        self.save_to_local_checkbox = QCheckBox(T("website.save_to_local"))
        self.save_to_local_checkbox.toggled.connect(self._on_save_toggled)
        row2.addWidget(QLabel(T("app.output_dir")))
        row2.addWidget(self.output_dir_input, 1)
        row2.addWidget(self.browse_btn)
        row2.addWidget(self.save_to_local_checkbox)
        settings_layout.addLayout(row2)

        self.output_dir_input.setEnabled(False)
        self.browse_btn.setEnabled(False)

        layout.addWidget(self.settings_group)

        splitter = QSplitter(Qt.Vertical)

        self.results_group = QGroupBox()
        results_layout = QVBoxLayout(self.results_group)

        self.summary_label = QLabel("")
        results_layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            T("website.col_url"),
            T("website.col_size"),
            T("website.col_status"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        results_layout.addWidget(self.table, 1)

        splitter.addWidget(self.results_group)

        self.log_group = QGroupBox()
        log_layout = QVBoxLayout(self.log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_text)
        splitter.addWidget(self.log_group)
        splitter.setSizes([380, 160])

        layout.addWidget(splitter, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        ctrl = QHBoxLayout()
        self.start_btn = QPushButton(T("website.start_btn"))
        self.start_btn.setProperty("class", "primary")
        self.start_btn.clicked.connect(self._start_analysis)
        self.cancel_btn = QPushButton(T("website.cancel_btn"))
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.clicked.connect(self._cancel_analysis)
        ctrl.addWidget(self.start_btn)
        ctrl.addWidget(self.cancel_btn)
        ctrl.addStretch()
        layout.addLayout(ctrl)

    def retranslate(self):
        self.settings_group.setTitle(T("website.page_title"))
        self.results_group.setTitle(T("website.results_title"))
        self.log_group.setTitle(T("website.log_title"))
        self.url_input.setPlaceholderText(T("website.url_placeholder"))
        self.output_dir_input.setPlaceholderText(T("app.output_dir_placeholder"))
        self.save_to_local_checkbox.setText(T("website.save_to_local"))
        self.browse_btn.setText(T("app.browse"))
        self.start_btn.setText(T("website.start_btn"))
        self.cancel_btn.setText(T("website.cancel_btn"))
        self.table.setHorizontalHeaderLabels([
            T("website.col_url"),
            T("website.col_size"),
            T("website.col_status"),
        ])

    def _browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, T("website.select_output_dir"),
        )
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def _on_save_toggled(self, checked):
        self.output_dir_input.setEnabled(checked)
        self.browse_btn.setEnabled(checked)

    def _clear_results(self):
        self.table.setRowCount(0)
        self._url_to_row.clear()
        self._image_count = 0
        self._total_size = 0
        self.summary_label.setText("")

    def _update_summary(self):
        self.summary_label.setText(
            T("website.summary_count", count=self._image_count) + "  |  "
            + T("website.summary_size", size=format_size(self._total_size))
        )

    def _on_image_info(self, url, size_bytes):
        row = self.table.rowCount()
        self.table.insertRow(row)

        url_item = QTableWidgetItem(url)
        url_item.setToolTip(url)
        self.table.setItem(row, 0, url_item)

        if size_bytes > 0:
            size_text = format_size(size_bytes)
            self._total_size += size_bytes
            status = T("website.status_analyzed")
        else:
            size_text = T("website.status_unknown")
            status = T("website.status_unknown")
        self.table.setItem(row, 1, QTableWidgetItem(size_text))
        self.table.setItem(row, 2, QTableWidgetItem(status))

        self._url_to_row[url] = row
        self._image_count = self.table.rowCount()
        self._update_summary()

    def _on_image_downloaded(self, url, success):
        if url in self._url_to_row:
            row = self._url_to_row[url]
            if success:
                self.table.setItem(row, 2, QTableWidgetItem(T("website.status_downloaded")))
            else:
                self.table.setItem(row, 2, QTableWidgetItem(T("website.status_download_failed")))

    def _start_analysis(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, T("app.warning"), T("website.enter_url"))
            return

        self._clear_results()
        self.log_text.clear()

        save_to_local = self.save_to_local_checkbox.isChecked()
        output_dir = self.output_dir_input.text().strip() if save_to_local else ""

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = WebsiteWorker(url, save_to_local, output_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.image_info.connect(self._on_image_info)
        self.worker.image_downloaded.connect(self._on_image_downloaded)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _cancel_analysis(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log(T("website.worker_cancelled"))

    def _on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_log(self, message, is_error=False):
        self.log(message, is_error)

    def log(self, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "\U0001f534 " if is_error else ""
        self.log_text.append(f"[{timestamp}] {prefix}{message}")
        self.log_message.emit(message, is_error)

    def _on_finished(self, stats):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.log("\n" + "=" * 50)
        self.log(T("website.finished"))
        self.log(T("website.stats_total_images", count=stats.get("total_images", 0)))
        self.log(T("website.stats_total_size",
                   size=format_size(stats.get("total_size", 0))))
        if stats.get("downloaded", 0) > 0:
            self.log(T("website.stats_downloaded", count=stats["downloaded"]))
        self.log("=" * 50)

        if stats.get("total_images", 0) > 0:
            QMessageBox.information(
                self, T("website.finished"),
                T("website.analysis_done",
                  count=stats["total_images"],
                  downloaded=stats.get("downloaded", 0)),
            )
