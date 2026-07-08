from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox,
)

from i18n import T, on_language_change
from core.config import save_config
from core.utils import format_size


class HistoryPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.retranslate()
        on_language_change(self.retranslate)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            T('history.table_time'), T('history.table_files'),
            T('history.table_success'), T('history.table_fail'),
            T('history.table_original'), T('history.table_compressed'),
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.history_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.history_table, 1)

        btn_bar = QHBoxLayout()
        self.refresh_history_btn = QPushButton()
        self.refresh_history_btn.setProperty('class', 'primary')
        self.refresh_history_btn.clicked.connect(self.refresh_history_table)
        self.clear_history_btn = QPushButton()
        self.clear_history_btn.clicked.connect(self.clear_history)
        btn_bar.addWidget(self.refresh_history_btn)
        btn_bar.addWidget(self.clear_history_btn)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

    def retranslate(self):
        self.history_table.setHorizontalHeaderLabels([
            T('history.table_time'), T('history.table_files'),
            T('history.table_success'), T('history.table_fail'),
            T('history.table_original'), T('history.table_compressed'),
        ])
        self.refresh_history_btn.setText(T('history.refresh_btn'))
        self.clear_history_btn.setText(T('history.clear_btn'))

    def refresh_history_table(self):
        self.history_table.setRowCount(0)
        for record in reversed(self.config.get("history", [])):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(record.get("time", "")))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(record.get("total", 0))))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(record.get("success", 0))))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(record.get("fail", 0))))
            self.history_table.setItem(row, 4, QTableWidgetItem(format_size(record.get("original_size", 0))))
            self.history_table.setItem(row, 5, QTableWidgetItem(format_size(record.get("compressed_size", 0))))

    def clear_history(self):
        reply = QMessageBox.question(
            self, T("history.confirm_clear"), T("app.confirm_clear_history"),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.config["history"] = []
            save_config(self.config)
            self.refresh_history_table()
