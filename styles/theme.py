"""Global QSS theme - tech blue (#2563eb)."""

# Design tokens (reference)
# primary:        #2563eb
# primary.hover:  #1d4ed8
# primary.press:  #1e40af
# primary.soft:   #eff6ff
# primary.soft2:  #dbeafe
# bg.app:         #f8fafc
# bg.surface:     #ffffff
# border:         #e5e7eb
# text.primary:   #111827
# text.secondary: #4b5563
# text.muted:     #9ca3af
# danger:         #ef4444

APP_STYLESHEET = """
QMainWindow, QDialog {
    background: #f8fafc;
}

QWidget#contentHost {
    background: #f8fafc;
}

QWidget#sidebarWidget {
    background: #ffffff;
}

QLabel#brandTitle {
    color: #2563eb;
    font-size: 15px;
    font-weight: 700;
}

QLabel#brandSubtitle {
    color: #9ca3af;
    font-size: 11px;
}

QListWidget#sidebar {
    background: #ffffff;
    border: none;
    border-right: 1px solid #e5e7eb;
    font-size: 13px;
    outline: none;
}
QListWidget#sidebar::item {
    padding: 10px 14px 10px 12px;
    border-left: 3px solid transparent;
    border-radius: 0;
    color: #4b5563;
}
QListWidget#sidebar::item:selected {
    background: #eff6ff;
    color: #2563eb;
    border-left: 3px solid #2563eb;
    font-weight: 600;
}
QListWidget#sidebar::item:hover:!selected {
    background: #f9fafb;
    color: #374151;
}

QComboBox#langCombo {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px 10px;
    color: #4b5563;
    font-size: 12px;
}
QComboBox#langCombo::drop-down {
    border: none;
    width: 20px;
}
QComboBox#langCombo QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    color: #4b5563;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: #111827;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #2563eb;
    font-size: 13px;
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

QFrame#readyBar {
    background: #eff6ff;
    border: 1px solid #dbeafe;
    border-radius: 10px;
}

QLabel#readyLabel {
    color: #1d4ed8;
    font-size: 13px;
    font-weight: 600;
}

/* ---- settings panel (right side) ---- */
QFrame#settingsPanel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}
QLabel#settingsPanelTitle {
    color: #111827;
    font-size: 14px;
    font-weight: 700;
}
QLabel#settingsLabel {
    color: #374151;
    font-size: 12px;
    font-weight: 600;
}

QPushButton {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 7px 16px;
    background: #ffffff;
    color: #4b5563;
    font-size: 13px;
}
QPushButton:hover {
    background: #f9fafb;
    border-color: #d1d5db;
}
QPushButton:pressed {
    background: #f3f4f6;
}
QPushButton[class="primary"] {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
    font-weight: 600;
    padding: 9px 20px;
}
QPushButton[class="primary"]:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}
QPushButton[class="primary"]:pressed {
    background: #1e40af;
    border-color: #1e40af;
}
QPushButton[class="primary-lg"] {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
    font-weight: 600;
    font-size: 15px;
    padding: 12px 28px;
    border-radius: 10px;
}
QPushButton[class="primary-lg"]:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}
QPushButton[class="primary-lg"]:pressed {
    background: #1e40af;
    border-color: #1e40af;
}
QPushButton[class="default-lg"] {
    background: #ffffff;
    color: #4b5563;
    border: 1px solid #d1d5db;
    font-size: 14px;
    padding: 10px 24px;
    border-radius: 10px;
}
QPushButton[class="default-lg"]:hover {
    background: #f9fafb;
    border-color: #9ca3af;
}
QPushButton[class="default-lg"]:pressed {
    background: #f3f4f6;
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
QPushButton[class="ghost"] {
    background: transparent;
    border: none;
    color: #2563eb;
    font-weight: 600;
    padding: 6px 8px;
}
QPushButton[class="ghost"]:hover {
    background: #eff6ff;
    border: none;
}
QPushButton:disabled {
    background: #f3f4f6;
    color: #9ca3af;
    border-color: #e5e7eb;
}

QListWidget {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 6px;
    color: #4b5563;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 6px;
}
QListWidget::item:selected {
    background: #dbeafe;
    color: #1e40af;
}
QListWidget::item:hover:!selected {
    background: #f9fafb;
}

QLineEdit {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 7px 10px;
    background: #ffffff;
    color: #111827;
}
QLineEdit:focus {
    border-color: #2563eb;
}

QComboBox {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px 10px;
    background: #ffffff;
    color: #111827;
}
QComboBox:hover {
    border-color: #d1d5db;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    color: #111827;
    selection-background-color: #eff6ff;
    selection-color: #2563eb;
}

QSpinBox {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 4px 8px;
    background: #ffffff;
    color: #111827;
}
QSpinBox:focus {
    border-color: #2563eb;
}

QCheckBox, QRadioButton {
    spacing: 6px;
    color: #4b5563;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background: #e5e7eb;
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
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #ffffff;
    gridline-color: #f3f4f6;
}
QTableWidget::item {
    padding: 6px 8px;
    color: #4b5563;
}
QTableWidget::item:selected {
    background: #eff6ff;
    color: #2563eb;
}
QHeaderView::section {
    background: #f9fafb;
    color: #6b7280;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
}

QSplitter::handle {
    background: #e5e7eb;
    height: 2px;
}
QSplitter::handle:hover {
    background: #2563eb;
}

QTextEdit {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #f9fafb;
    color: #4b5563;
    padding: 8px;
}

QLabel {
    color: #4b5563;
}

QLabel#pageTitle {
    color: #111827;
    font-size: 18px;
    font-weight: 700;
}

QLabel#pageSubtitle {
    color: #6b7280;
    font-size: 13px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #e5e7eb;
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

/* Drop zone */
QFrame#dropZone {
    background: #f9fafb;
    border: 2px dashed #d1d5db;
    border-radius: 12px;
}
QFrame#dropZone[hover="true"] {
    background: #eff6ff;
    border: 2px dashed #2563eb;
}
QLabel#dropZoneIcon {
    color: #9ca3af;
    font-size: 40px;
}
QLabel#dropZoneTitle {
    color: #4b5563;
    font-size: 16px;
    font-weight: 600;
}
QLabel#dropZoneHint {
    color: #9ca3af;
    font-size: 12px;
}

/* Collapsible more-settings */
QFrame#collapsibleSection {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}
QPushButton#collapsibleToggle {
    background: transparent;
    border: none;
    text-align: left;
    color: #2563eb;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 14px;
}
QPushButton#collapsibleToggle:hover {
    background: #eff6ff;
    border: none;
    border-radius: 10px;
}
"""
