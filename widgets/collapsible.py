from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QSizePolicy


class CollapsibleSection(QFrame):
    """Expandable section for advanced settings (官网「更多设置」模式)."""

    toggled = pyqtSignal(bool)

    def __init__(self, title="", parent=None, expanded=False):
        super().__init__(parent)
        self.setObjectName("collapsibleSection")
        self._title = title
        self._expanded = expanded

        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 8)
        root.setSpacing(0)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("collapsibleToggle")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_btn.clicked.connect(self._on_toggle)
        root.addWidget(self.toggle_btn)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 4, 12, 8)
        self.content_layout.setSpacing(10)
        root.addWidget(self.content)

        self.set_expanded(expanded)
        self.set_title(title)

    def set_title(self, title):
        self._title = title or ""
        self._refresh_toggle_text()

    def title(self):
        return self._title

    def is_expanded(self):
        return self._expanded

    def set_expanded(self, expanded):
        self._expanded = bool(expanded)
        self.content.setVisible(self._expanded)
        self._refresh_toggle_text()

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def _on_toggle(self):
        self.set_expanded(not self._expanded)
        self.toggled.emit(self._expanded)

    def _refresh_toggle_text(self):
        arrow = "▾" if self._expanded else "▸"
        self.toggle_btn.setText(f"{arrow}  {self._title}")
