from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


class DropZone(QFrame):
    """Large dashed drop area matching website tool empty state."""

    files_dropped = pyqtSignal(list)
    add_files_clicked = pyqtSignal()
    add_folder_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setProperty("hover", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("\U0001f4c1")
        self.icon_label.setObjectName("dropZoneIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)

        self.title_label = QLabel()
        self.title_label.setObjectName("dropZoneTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("dropZoneHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setAlignment(Qt.AlignCenter)
        self.add_files_btn = QPushButton()
        self.add_files_btn.setProperty("class", "primary-lg")
        self.add_folder_btn = QPushButton()
        self.add_folder_btn.setProperty("class", "default-lg")
        self.add_files_btn.clicked.connect(self.add_files_clicked.emit)
        self.add_folder_btn.clicked.connect(self.add_folder_clicked.emit)
        btn_row.addWidget(self.add_files_btn)
        btn_row.addWidget(self.add_folder_btn)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.hint_label)
        layout.addSpacing(6)
        layout.addLayout(btn_row)

    def set_texts(self, title, hint, add_files, add_folder):
        self.title_label.setText(title)
        self.hint_label.setText(hint)
        self.add_files_btn.setText(add_files)
        self.add_folder_btn.setText(add_folder)

    def _set_hover(self, hovering):
        self.setProperty("hover", "true" if hovering else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_hover(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._set_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self._set_hover(False)
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                paths.append(path)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()
