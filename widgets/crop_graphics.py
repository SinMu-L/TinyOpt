from PyQt5.QtWidgets import (
    QWidget, QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QColor, QTransform,
    QBrush, QPolygonF, QPainterPath,
)

from i18n import T


class CropGraphicsScene(QGraphicsScene):
    cropRectChanged = pyqtSignal(QRectF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._crop_rect = QRectF()
        self._ratio = None
        self._min_size = 20
        self._dragging = False
        self._drag_handle = None
        self._drag_start_rect = QRectF()
        self._drag_start_pos = QPointF()
        self._handle_size = 9
        self._image_rect = QRectF()

    HANDLE_NONE = -1
    HANDLE_TL = 0
    HANDLE_TR = 1
    HANDLE_BL = 2
    HANDLE_BR = 3
    HANDLE_TOP = 4
    HANDLE_RIGHT = 5
    HANDLE_BOTTOM = 6
    HANDLE_LEFT = 7

    def setup_crop(self, image_rect, ratio=None):
        self._image_rect = QRectF(0, 0, image_rect.width(), image_rect.height())
        self._ratio = ratio
        self._init_crop_rect()
        self._clamp_crop_rect()
        self.invalidate()

    def set_crop_ratio(self, ratio):
        self._ratio = ratio
        if self._ratio and not self._crop_rect.isEmpty():
            self._apply_ratio_from_center()
        self._clamp_crop_rect()
        self.invalidate()

    def get_crop_rect(self):
        return QRectF(self._crop_rect)

    def _init_crop_rect(self):
        sr = self._image_rect
        cw = min(sr.width() * 0.75, 300)
        if self._ratio:
            rw, rh = self._ratio
            if cw / max(1, sr.height()) > rw / rh:
                cw = int(min(sr.width(), sr.height() * 0.75 * rw / rh))
            ch = cw * rh / rw
        else:
            ch = cw
        cw = max(self._min_size, int(cw))
        ch = max(self._min_size, int(ch))
        self._crop_rect = QRectF(sr.center().x() - cw / 2, sr.center().y() - ch / 2, cw, ch)

    def _apply_ratio_from_center(self):
        rw, rh = self._ratio
        r = self._crop_rect
        c = r.center()
        if r.width() / max(1, r.height()) > rw / rh:
            new_h = r.height()
            new_w = new_h * rw / rh
        else:
            new_w = r.width()
            new_h = new_w * rh / rw
        self._crop_rect = QRectF(c.x() - new_w / 2, c.y() - new_h / 2, new_w, new_h)

    def _clamp_crop_rect(self):
        sr = self._image_rect
        if sr.isEmpty():
            return
        r = self._crop_rect
        if r.width() < self._min_size or r.height() < self._min_size:
            return
        x = max(sr.left(), r.left())
        y = max(sr.top(), r.top())
        self._crop_rect = QRectF(
            min(x, sr.right() - self._min_size),
            min(y, sr.bottom() - self._min_size),
            r.width(), r.height()
        )
        if self._crop_rect.right() > sr.right():
            self._crop_rect.moveRight(sr.right())
        if self._crop_rect.bottom() > sr.bottom():
            self._crop_rect.moveBottom(sr.bottom())

    def _get_handles(self):
        r = self._crop_rect
        hs = self._handle_size
        half = hs / 2.0
        c = r.center()
        return [
            (self.HANDLE_TL, QRectF(r.left() - half, r.top() - half, hs, hs)),
            (self.HANDLE_TR, QRectF(r.right() - half, r.top() - half, hs, hs)),
            (self.HANDLE_BL, QRectF(r.left() - half, r.bottom() - half, hs, hs)),
            (self.HANDLE_BR, QRectF(r.right() - half, r.bottom() - half, hs, hs)),
            (self.HANDLE_TOP, QRectF(c.x() - half, r.top() - half, hs, hs)),
            (self.HANDLE_RIGHT, QRectF(r.right() - half, c.y() - half, hs, hs)),
            (self.HANDLE_BOTTOM, QRectF(c.x() - half, r.bottom() - half, hs, hs)),
            (self.HANDLE_LEFT, QRectF(r.left() - half, c.y() - half, hs, hs)),
        ]

    def _hit_test_handle(self, pos):
        margin = 4
        for htype, hrect in self._get_handles():
            hit = hrect.adjusted(-margin, -margin, margin, margin)
            if hit.contains(pos):
                return htype
        return self.HANDLE_NONE

    def _cursor_for_handle(self, htype):
        if htype in (self.HANDLE_TL, self.HANDLE_BR):
            return Qt.SizeFDiagCursor
        elif htype in (self.HANDLE_TR, self.HANDLE_BL):
            return Qt.SizeBDiagCursor
        elif htype in (self.HANDLE_TOP, self.HANDLE_BOTTOM):
            return Qt.SizeVerCursor
        elif htype in (self.HANDLE_LEFT, self.HANDLE_RIGHT):
            return Qt.SizeHorCursor
        return Qt.OpenHandCursor

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self._image_rect.isEmpty() or self._crop_rect.isEmpty():
            return
        painter.setRenderHint(QPainter.Antialiasing)

        overlay = QPainterPath()
        overlay.addRect(self._image_rect)
        crop_path = QPainterPath()
        crop_path.addRect(self._crop_rect)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.drawPath(overlay.subtracted(crop_path))

        pen = QPen(QColor(37, 99, 235), 2, Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._crop_rect)

        h_pen = QPen(QColor(37, 99, 235), 1.5)
        painter.setPen(h_pen)
        painter.setBrush(QColor(255, 255, 255))
        for _, hrect in self._get_handles():
            painter.drawRect(hrect)

    def mousePressEvent(self, event):
        pos = event.scenePos()
        htype = self._hit_test_handle(pos)
        if htype != self.HANDLE_NONE:
            self._dragging = True
            self._drag_handle = htype
            self._drag_start_rect = QRectF(self._crop_rect)
            self._drag_start_pos = pos
            event.accept()
            return
        if self._crop_rect.contains(pos):
            self._dragging = True
            self._drag_handle = self.HANDLE_NONE
            self._drag_start_rect = QRectF(self._crop_rect)
            self._drag_start_pos = pos
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._dragging:
            pos = event.scenePos()
            htype = self._hit_test_handle(pos)
            if htype != self.HANDLE_NONE:
                self.views()[0].setCursor(self._cursor_for_handle(htype)) if self.views() else None
            elif self._crop_rect.contains(pos):
                self.views()[0].setCursor(Qt.OpenHandCursor) if self.views() else None
            else:
                self.views()[0].setCursor(Qt.ArrowCursor) if self.views() else None
            super().mouseMoveEvent(event)
            return

        pos = event.scenePos()
        delta = pos - self._drag_start_pos
        r = self._drag_start_rect
        new_rect = None

        if self._drag_handle == self.HANDLE_NONE:
            new_rect = r.translated(delta.x(), delta.y())
        elif self._ratio and (event.modifiers() & Qt.ShiftModifier):
            new_rect = self._resize_constrained(r, self._drag_handle, delta)
        else:
            new_rect = self._resize_freeform(r, self._drag_handle, delta)

        if new_rect and new_rect.width() >= self._min_size and new_rect.height() >= self._min_size:
            sr = self._image_rect
            clamped = QRectF(new_rect)
            if clamped.left() < sr.left():
                clamped.moveLeft(sr.left())
            if clamped.right() > sr.right():
                clamped.moveRight(sr.right())
            if clamped.top() < sr.top():
                clamped.moveTop(sr.top())
            if clamped.bottom() > sr.bottom():
                clamped.moveBottom(sr.bottom())
            if clamped != self._crop_rect:
                self._crop_rect = clamped
                self.invalidate()
                self.cropRectChanged.emit(self._crop_rect)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_handle = self.HANDLE_NONE
        event.accept()

    def _resize_freeform(self, r, handle, delta):
        rect = QRectF(r)
        if handle == self.HANDLE_TL:
            rect.setLeft(min(rect.right() - self._min_size, r.left() + delta.x()))
            rect.setTop(min(rect.bottom() - self._min_size, r.top() + delta.y()))
        elif handle == self.HANDLE_TR:
            rect.setRight(max(rect.left() + self._min_size, r.right() + delta.x()))
            rect.setTop(min(rect.bottom() - self._min_size, r.top() + delta.y()))
        elif handle == self.HANDLE_BL:
            rect.setLeft(min(rect.right() - self._min_size, r.left() + delta.x()))
            rect.setBottom(max(rect.top() + self._min_size, r.bottom() + delta.y()))
        elif handle == self.HANDLE_BR:
            rect.setRight(max(rect.left() + self._min_size, r.right() + delta.x()))
            rect.setBottom(max(rect.top() + self._min_size, r.bottom() + delta.y()))
        elif handle == self.HANDLE_TOP:
            rect.setTop(min(rect.bottom() - self._min_size, r.top() + delta.y()))
        elif handle == self.HANDLE_BOTTOM:
            rect.setBottom(max(rect.top() + self._min_size, r.bottom() + delta.y()))
        elif handle == self.HANDLE_LEFT:
            rect.setLeft(min(rect.right() - self._min_size, r.left() + delta.x()))
        elif handle == self.HANDLE_RIGHT:
            rect.setRight(max(rect.left() + self._min_size, r.right() + delta.x()))
        return rect

    def _resize_constrained(self, r, handle, delta):
        rw, rh = self._ratio
        target = rw / rh
        rect = QRectF(r)

        if handle == self.HANDLE_BR:
            new_w = max(self._min_size, r.width() + delta.x())
            new_h = new_w / target
            rect.setRight(r.left() + new_w)
            rect.setBottom(r.top() + new_h)
        elif handle == self.HANDLE_TL:
            new_w = max(self._min_size, r.width() - delta.x())
            new_h = new_w / target
            rect.setLeft(r.right() - new_w)
            rect.setTop(r.bottom() - new_h)
        elif handle == self.HANDLE_TR:
            new_w = max(self._min_size, r.width() + delta.x())
            new_h = new_w / target
            rect.setRight(r.left() + new_w)
            rect.setTop(r.bottom() - new_h)
        elif handle == self.HANDLE_BL:
            new_w = max(self._min_size, r.width() - delta.x())
            new_h = new_w / target
            rect.setLeft(r.right() - new_w)
            rect.setBottom(r.top() + new_h)
        elif handle in (self.HANDLE_TOP, self.HANDLE_BOTTOM):
            if handle == self.HANDLE_TOP:
                new_h = max(self._min_size, r.height() - delta.y())
                rect.setTop(r.bottom() - new_h)
            else:
                new_h = max(self._min_size, r.height() + delta.y())
                rect.setBottom(r.top() + new_h)
            new_w = new_h * target
            c = r.center()
            rect.setLeft(c.x() - new_w / 2)
            rect.setRight(c.x() + new_w / 2)
        elif handle in (self.HANDLE_LEFT, self.HANDLE_RIGHT):
            if handle == self.HANDLE_LEFT:
                new_w = max(self._min_size, r.width() - delta.x())
                rect.setLeft(r.right() - new_w)
            else:
                new_w = max(self._min_size, r.width() + delta.x())
                rect.setRight(r.left() + new_w)
            new_h = new_w / target
            c = r.center()
            rect.setTop(c.y() - new_h / 2)
            rect.setBottom(c.y() + new_h / 2)
        return rect


class CropGraphicsPreview(QWidget):
    cropRectChanged = pyqtSignal(QRectF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(200)
        self.setStyleSheet("border: 2px dashed #cbd5e1; border-radius: 8px; background: #f8fafc;")

        self._scene = CropGraphicsScene(self)
        self._scene.cropRectChanged.connect(self._on_overlay_changed)

        self._view = QGraphicsView(self._scene, self)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setRenderHint(QPainter.SmoothPixmapTransform)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setFrameShape(QFrame.NoFrame)
        self._view.setStyleSheet("border: none; background: transparent;")
        self._view.setGeometry(2, 2, self.width() - 4, self.height() - 4)
        self._view.setMouseTracking(True)

        self._pixmap_item = QGraphicsPixmapItem()
        self._pixmap_item.setTransformationMode(Qt.SmoothTransformation)
        self._scene.addItem(self._pixmap_item)

        self._base_pixmap = None
        self._target_ratio = None
        self._hint = QLabel(T("app.crop_preview_hint"), self)
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setStyleSheet("border: none; color: #aaa; font-size: 14px;")
        self._hint.setGeometry(0, 0, self.width(), self.height())

    def set_base_image(self, pixmap):
        self._base_pixmap = pixmap
        if pixmap and not pixmap.isNull():
            self._hint.hide()
            self._pixmap_item.setPixmap(pixmap)
            self._scene.setSceneRect(self._pixmap_item.boundingRect())
            self._scene.setup_crop(self._pixmap_item.boundingRect(), self._target_ratio)
            self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
        else:
            self._hint.show()
            self._pixmap_item.setPixmap(QPixmap())
            self._scene.setSceneRect(0, 0, self.width() - 4, self.height() - 4)

    def set_target_ratio(self, w, h):
        if w and h:
            self._target_ratio = (w, h)
        else:
            self._target_ratio = None
        self._scene.set_crop_ratio(self._target_ratio)

    def get_crop_pixel_rect(self):
        if not self._base_pixmap or self._base_pixmap.isNull():
            return QRectF()
        crop_scene = self._scene.get_crop_rect()
        scene_rect = self._scene.sceneRect()
        img_w = self._base_pixmap.width()
        img_h = self._base_pixmap.height()
        scale_x = img_w / scene_rect.width()
        scale_y = img_h / scene_rect.height()
        return QRectF(
            (crop_scene.left() - scene_rect.left()) * scale_x,
            (crop_scene.top() - scene_rect.top()) * scale_y,
            crop_scene.width() * scale_x,
            crop_scene.height() * scale_y,
        )

    def _on_overlay_changed(self, rect):
        self.cropRectChanged.emit(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._view.setGeometry(2, 2, self.width() - 4, self.height() - 4)
        self._hint.setGeometry(0, 0, self.width(), self.height())
        if self._base_pixmap and not self._base_pixmap.isNull():
            self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        if self._base_pixmap and not self._base_pixmap.isNull():
            self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
