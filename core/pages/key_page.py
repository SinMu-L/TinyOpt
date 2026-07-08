from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from i18n import T, on_language_change
from core.config import save_config
from widgets.dialogs import AddKeyDialog


class KeyPage(QWidget):
    log_message = pyqtSignal(str, bool)
    keys_changed = pyqtSignal()

    def __init__(self, config, key_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.key_manager = key_manager
        self.setup_ui()
        self.retranslate()
        on_language_change(self.retranslate)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.key_table = QTableWidget()
        self.key_table.setColumnCount(4)
        self.key_table.setHorizontalHeaderLabels([
            T('key.table_remark'), T('key.table_key'),
            T('key.table_usage'), T('key.table_status'),
        ])
        self.key_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.key_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.key_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.key_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.key_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.key_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.key_table.verticalHeader().setVisible(False)
        self.key_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.key_table, 1)

        btn_layout = QHBoxLayout()
        self.add_key_btn = QPushButton()
        self.add_key_btn.setProperty('class', 'primary')
        self.add_key_btn.clicked.connect(self.add_key_dialog)
        self.edit_key_btn = QPushButton()
        self.edit_key_btn.clicked.connect(self.edit_key_dialog)
        self.remove_key_btn = QPushButton()
        self.remove_key_btn.clicked.connect(self.remove_key)
        self.toggle_key_btn = QPushButton()
        self.toggle_key_btn.clicked.connect(self.toggle_key)
        self.refresh_quota_btn = QPushButton()
        self.refresh_quota_btn.clicked.connect(self.refresh_quota)

        btn_layout.addWidget(self.add_key_btn)
        btn_layout.addWidget(self.edit_key_btn)
        btn_layout.addWidget(self.remove_key_btn)
        btn_layout.addWidget(self.toggle_key_btn)
        btn_layout.addWidget(self.refresh_quota_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.key_status_label = QLabel("")
        layout.addWidget(self.key_status_label)

    def retranslate(self):
        self.key_table.setHorizontalHeaderLabels([
            T('key.table_remark'), T('key.table_key'),
            T('key.table_usage'), T('key.table_status'),
        ])
        self.add_key_btn.setText(T('key.add_btn'))
        self.edit_key_btn.setText(T('key.edit_btn'))
        self.remove_key_btn.setText(T('key.remove_btn'))
        self.toggle_key_btn.setText(T('key.toggle_btn'))
        self.refresh_quota_btn.setText(T('key.refresh_btn'))
        self.update_key_status()

    def add_key_dialog(self):
        dialog = AddKeyDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            existing_keys = [k["key"] for k in self.key_manager.keys]
            if data["key"] in existing_keys:
                QMessageBox.warning(self, T("app.warning"), T("app.key_exists"))
                return
            self.key_manager.add_key(data["key"], data["remark"], data["monthly_limit"])
            self.refresh_key_table()
            self.key_manager.save(self.config)
            self.keys_changed.emit()
            self.log_message.emit(T("key.added", remark=data['remark'] or data['key'][:8]), False)

    def edit_key_dialog(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, T("app.warning"), T("app.select_key_first"))
            return
        key_data = self.key_manager.keys[row]
        dialog = AddKeyDialog(self, edit_mode=True, key_data=key_data)
        if dialog.exec_():
            data = dialog.get_data()
            if data["key"] != key_data["key"] and any(
                k["key"] == data["key"] for k in self.key_manager.keys
            ):
                QMessageBox.warning(self, T("app.warning"), T("app.key_exists"))
                return
            key_data["key"] = data["key"]
            key_data["remark"] = data["remark"]
            key_data["monthly_limit"] = data["monthly_limit"]
            self.refresh_key_table()
            self.key_manager.save(self.config)
            self.keys_changed.emit()
            self.log_message.emit(T("key.updated", remark=data['remark'] or data['key'][:8]), False)

    def remove_key(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, T("app.warning"), T("app.select_key_first"))
            return
        key = self.key_manager.keys[row]
        remark = key.get("remark") or key["key"][:8]
        reply = QMessageBox.question(
            self, T("app.confirm"), T("key.confirm_delete", remark=remark),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.key_manager.remove_key(row)
            self.refresh_key_table()
            self.key_manager.save(self.config)
            self.keys_changed.emit()
            self.log_message.emit(T("key.deleted", remark=remark), False)

    def toggle_key(self):
        row = self.key_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, T("app.warning"), T("app.select_key_first"))
            return
        self.key_manager.toggle_key(row)
        self.refresh_key_table()
        self.key_manager.save(self.config)
        self.keys_changed.emit()
        key = self.key_manager.keys[row]
        status = T("key.enabled_status") if key["enabled"] else T("key.disabled_status")
        remark = key.get("remark") or key["key"][:8]
        self.log_message.emit(T("key.toggled", status=status, remark=remark), False)

    def refresh_quota(self):
        if not self.key_manager.keys:
            QMessageBox.warning(self, T("app.warning"), T("key.no_keys"))
            return
        self.refresh_quota_btn.setEnabled(False)
        self.refresh_quota_btn.setText(T("key.refreshing"))
        QApplication.processEvents()

        self.key_manager.refresh_all_usage()
        self.refresh_key_table()
        self.key_manager.save(self.config)
        self.keys_changed.emit()

        self.refresh_quota_btn.setText(T("key.refresh_btn"))
        self.refresh_quota_btn.setEnabled(True)
        self.log_message.emit(T("key.refresh_done"), False)

    def refresh_key_table(self):
        self.key_table.setRowCount(0)
        for k in self.key_manager.keys:
            row = self.key_table.rowCount()
            self.key_table.insertRow(row)

            remark = k.get("remark", "") or k["key"][:8] + "..."
            self.key_table.setItem(row, 0, QTableWidgetItem(remark))

            masked = k["key"][:6] + "*" * (len(k["key"]) - 8) + k["key"][-2:]
            key_item = QTableWidgetItem(masked)
            key_item.setToolTip(k["key"])
            self.key_table.setItem(row, 1, key_item)

            usage_text = T("app.key_usage", usage=k['monthly_usage'], limit=k['monthly_limit'])
            usage_item = QTableWidgetItem(usage_text)
            remaining = k["monthly_limit"] - k["monthly_usage"]
            if remaining <= 0:
                usage_item.setForeground(QBrush(QColor("#f44336")))
            elif remaining < 100:
                usage_item.setForeground(QBrush(QColor("#FF9800")))
            else:
                usage_item.setForeground(QBrush(QColor("#4CAF50")))
            self.key_table.setItem(row, 2, usage_item)

            status = T("app.key_status_enabled") if k["enabled"] else T("app.key_status_disabled")
            status_item = QTableWidgetItem(status)
            if not k["enabled"]:
                status_item.setForeground(QBrush(QColor("#f44336")))
            self.key_table.setItem(row, 3, status_item)

        self.update_key_status()

    def update_key_status(self):
        total = len(self.key_manager.keys)
        enabled = sum(1 for k in self.key_manager.keys if k["enabled"])
        available = len(self.key_manager.get_available_keys())
        remaining_total = sum(
            k["monthly_limit"] - k["monthly_usage"]
            for k in self.key_manager.keys
            if k["enabled"]
        )
        limit_total = sum(
            k["monthly_limit"]
            for k in self.key_manager.keys
            if k["enabled"]
        )
        self.key_status_label.setText(T("app.key_remaining", total=total, enabled=enabled, available=available, remaining=remaining_total, limit_total=limit_total))
