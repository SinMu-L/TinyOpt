from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap

from i18n import T


class PositionPreviewWidget(QWidget):
    positionChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 280)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: 2px dashed #cbd5e1; border-radius: 8px; background: #f8fafc;")

        self._base_pixmap = None
        self._wm_pixmap = None
        self._wm_x_ratio = 0.85
        self._wm_y_ratio = 0.85
        self._wm_opacity = 0.8
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._img_rect = None

    def set_base_image(self, pixmap):
        self._base_pixmap = pixmap
        self._calc_image_rect()
        self.update()

    def set_watermark(self, pixmap):
        self._wm_pixmap = pixmap
        self.update()

    def set_opacity(self, val):
        self._wm_opacity = val / 100.0
        self.update()

    def set_position_ratio(self, x_ratio, y_ratio):
        self._wm_x_ratio = max(0.0, min(1.0, x_ratio))
        self._wm_y_ratio = max(0.0, min(1.0, y_ratio))
        self.positionChanged.emit(self._wm_x_ratio, self._wm_y_ratio)
        self.update()

    def get_position_ratio(self):
        return (self._wm_x_ratio, self._wm_y_ratio)

    def _calc_image_rect(self):
        if not self._base_pixmap or self._base_pixmap.isNull():
            self._img_rect = None
            return
        w = self.width() - 4
        h = self.height() - 4
        pw = self._base_pixmap.width()
        ph = self._base_pixmap.height()
        scale = min(w / pw, h / ph)
        dw = int(pw * scale)
        dh = int(ph * scale)
        dx = (self.width() - dw) // 2
        dy = (self.height() - dh) // 2
        self._img_rect = QRect(dx, dy, dw, dh)

    def _wm_display_rect(self):
        if self._img_rect is None or not self._wm_pixmap or self._wm_pixmap.isNull():
            return None
        wm_w = self._wm_pixmap.width()
        wm_h = self._wm_pixmap.height()
        avail_w = max(1, self._img_rect.width() - wm_w)
        avail_h = max(1, self._img_rect.height() - wm_h)
        x = self._img_rect.x() + int(self._wm_x_ratio * avail_w)
        y = self._img_rect.y() + int(self._wm_y_ratio * avail_h)
        return QRect(x, y, wm_w, wm_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        if self._base_pixmap and not self._base_pixmap.isNull():
            if self._img_rect is None:
                self._calc_image_rect()
            if self._img_rect:
                scaled = self._base_pixmap.scaled(
                    self._img_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                painter.drawPixmap(self._img_rect.topLeft(), scaled)
        else:
            painter.fillRect(0, 0, w, h, QColor(245, 245, 245))
            painter.setPen(QColor(180, 180, 180))
            f = painter.font()
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(self.rect(), Qt.AlignCenter, T("app.position_preview_hint"))

        if self._wm_pixmap and not self._wm_pixmap.isNull() and self._img_rect:
            wm_rect = self._wm_display_rect()
            if wm_rect:
                painter.setOpacity(self._wm_opacity)
                painter.drawPixmap(wm_rect.topLeft(), self._wm_pixmap)
                painter.setOpacity(1.0)
                pen = QPen(QColor(30, 100, 200), 1, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(wm_rect)

        painter.end()

    def resizeEvent(self, event):
        self._calc_image_rect()
        super().resizeEvent(event)

    def _hit_test_wm(self, pos):
        wm_rect = self._wm_display_rect()
        if wm_rect and wm_rect.contains(pos):
            return True
        return False

    def _pos_to_ratio(self, screen_x, screen_y):
        if self._img_rect is None:
            return (self._wm_x_ratio, self._wm_y_ratio)
        wm_w = self._wm_pixmap.width() if self._wm_pixmap else 1
        wm_h = self._wm_pixmap.height() if self._wm_pixmap else 1
        wm_x = screen_x - self._drag_offset_x
        wm_y = screen_y - self._drag_offset_y
        avail_w = max(1, self._img_rect.width() - wm_w)
        avail_h = max(1, self._img_rect.height() - wm_h)
        rx = (wm_x - self._img_rect.x()) / avail_w
        ry = (wm_y - self._img_rect.y()) / avail_h
        return (max(0.0, min(1.0, rx)), max(0.0, min(1.0, ry)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._hit_test_wm(event.pos()):
                self._dragging = True
                wm_rect = self._wm_display_rect()
                if wm_rect:
                    self._drag_offset_x = event.pos().x() - wm_rect.x()
                    self._drag_offset_y = event.pos().y() - wm_rect.y()
                self.setCursor(Qt.ClosedHandCursor)
            elif self._img_rect and self._img_rect.contains(event.pos()) and self._wm_pixmap \
                    and not self._wm_pixmap.isNull():
                self._dragging = True
                self._drag_offset_x = self._wm_pixmap.width() // 2
                self._drag_offset_y = self._wm_pixmap.height() // 2
                rx, ry = self._pos_to_ratio(event.pos().x(), event.pos().y())
                self._wm_x_ratio = rx
                self._wm_y_ratio = ry
                self.positionChanged.emit(rx, ry)
                self.update()
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            rx, ry = self._pos_to_ratio(event.pos().x(), event.pos().y())
            if abs(rx - self._wm_x_ratio) > 0.001 or abs(ry - self._wm_y_ratio) > 0.001:
                self._wm_x_ratio = rx
                self._wm_y_ratio = ry
                self.positionChanged.emit(rx, ry)
                self.update()
        else:
            if self._hit_test_wm(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            elif self._img_rect and self._img_rect.contains(event.pos()):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            if self._hit_test_wm(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
