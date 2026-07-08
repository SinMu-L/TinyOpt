from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QSpinBox,
    QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QVBoxLayout, QLabel,
)
from PyQt5.QtCore import Qt

from i18n import T
from core.utils import format_size


class AddKeyDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, key_data=None):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.setMinimumWidth(450)
        self.key_data = key_data

        layout = QFormLayout(self)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        if key_data:
            self.key_input.setText(key_data["key"])
        layout.addRow(T("add_key_dialog.api_key") + ":", self.key_input)

        self.remark_input = QLineEdit()
        if key_data:
            self.remark_input.setText(key_data.get("remark", ""))
        layout.addRow(T("add_key_dialog.remark") + ":", self.remark_input)

        self.limit_input = QSpinBox()
        self.limit_input.setRange(1, 10000)
        self.limit_input.setValue(key_data.get("monthly_limit", 500) if key_data else 500)
        layout.addRow(T("add_key_dialog.monthly_limit") + ":", self.limit_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(T("add_key_dialog.title_edit" if self.edit_mode else "add_key_dialog.title_add"))
        self.key_input.setPlaceholderText(T("add_key_dialog.api_key_placeholder"))
        self.remark_input.setPlaceholderText(T("add_key_dialog.remark_placeholder"))
        self.limit_input.setSuffix(T("add_key_dialog.times_month"))

    def validate_and_accept(self):
        if not self.key_input.text().strip():
            QMessageBox.warning(self, T("app.warning"), T("add_key_dialog.warning_empty"))
            return
        if len(self.key_input.text().strip()) < 10:
            QMessageBox.warning(self, T("app.warning"), T("add_key_dialog.warning_invalid"))
            return
        self.accept()

    def get_data(self):
        return {
            "key": self.key_input.text().strip(),
            "remark": self.remark_input.text().strip(),
            "monthly_limit": self.limit_input.value(),
        }


class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("dialog_history.title"))
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            T("dialog_history.col_time"), T("dialog_history.col_files"),
            T("dialog_history.col_success"), T("dialog_history.col_fail"),
            T("dialog_history.col_original"), T("dialog_history.col_compressed"),
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)

        for record in reversed(history):
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(record.get("time", "")))
            table.setItem(row, 1, QTableWidgetItem(str(record.get("total", 0))))
            table.setItem(row, 2, QTableWidgetItem(str(record.get("success", 0))))
            table.setItem(row, 3, QTableWidgetItem(str(record.get("fail", 0))))
            table.setItem(row, 4, QTableWidgetItem(format_size(record.get("original_size", 0))))
            table.setItem(row, 5, QTableWidgetItem(format_size(record.get("compressed_size", 0))))

        layout.addWidget(table)
        close_btn = QPushButton(T("dialog_history.close"))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
