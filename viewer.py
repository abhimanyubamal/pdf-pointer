import os
import fitz
from PyQt5.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
)
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QPointF, QVariantAnimation, QEasingCurve


class PDFViewer(QGraphicsView):
    def __init__(self, pdf_path, characters):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.doc = fitz.open(pdf_path)
        self.characters = characters
        self.cursor_index = 0
        self.scale = 2

        self.last_page_index = 0

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.svg_path = os.path.join(base_dir, "finger.svg")

        # Fixed physical size: 1 cm × 1 cm
        dpi = self.logicalDpiX()
        self.size_px = int(dpi / 2.54)

        # Render SVG → Pixmap ONCE
        self.finger_pixmap = self._render_svg_to_pixmap(
            self.svg_path,
            self.size_px,
            self.size_px
        )

        self.finger_item = None
        self.finger_anim = None

        self.render_page(0)
        self._scroll_to_page_top()
        self.update_finger(animated=False)

    # --------------------------------------------------
    # Rendering helpers
    # --------------------------------------------------

    def _render_svg_to_pixmap(self, svg_path, width, height):
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    def render_page(self, page_index):
        self.scene.clear()

        page = self.doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.scale, self.scale))

        image = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format_RGB888
        )

        page_item = QGraphicsPixmapItem(QPixmap.fromImage(image))
        page_item.setZValue(0)
        self.scene.addItem(page_item)

        self.finger_item = QGraphicsPixmapItem(self.finger_pixmap)
        self.finger_item.setZValue(1000)
        self.scene.addItem(self.finger_item)

    # --------------------------------------------------
    # Main update
    # --------------------------------------------------

    def update_finger(self, animated=True):
        ch = self.characters[self.cursor_index]
        current_page = ch["page"]

        prev_pos = self.finger_item.pos() if self.finger_item else QPointF(0, 0)

        page_changed = current_page != self.last_page_index
        direction = current_page - self.last_page_index

        if page_changed:
            self.render_page(current_page)

            if direction > 0:
                self._scroll_to_page_top()
            else:
                self._scroll_to_page_bottom()

            self.last_page_index = current_page
            self.finger_item.setPos(prev_pos)

        r = ch["rect"]
        cx = (r.x0 + r.x1) / 2 * self.scale
        glyph_bottom_y = r.y1 * self.scale
        fw = self.finger_pixmap.width()

        target_pos = QPointF(cx - fw / 2, glyph_bottom_y)

        if animated:
            self._animate_to(prev_pos, target_pos)
        else:
            self.finger_item.setPos(target_pos)

        if not page_changed:
            self._ensure_finger_visible_linewise()

    # --------------------------------------------------
    # Animation
    # --------------------------------------------------

    def _animate_to(self, start_pos, target_pos):
        if self.finger_anim:
            self.finger_anim.stop()

        self.finger_anim = QVariantAnimation()
        self.finger_anim.setDuration(150)
        self.finger_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.finger_anim.setStartValue(start_pos)
        self.finger_anim.setEndValue(target_pos)

        self.finger_anim.valueChanged.connect(
            lambda value: self.finger_item.setPos(value)
        )

        self.finger_anim.start()

    # --------------------------------------------------
    # Scrolling helpers
    # --------------------------------------------------

    def _scroll_to_page_top(self):
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().minimum()
        )

    def _scroll_to_page_bottom(self):
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )

    def _ensure_finger_visible_linewise(self):
        viewport_rect = self.mapToScene(
            self.viewport().rect()
        ).boundingRect()

        finger_rect = self.finger_item.sceneBoundingRect()
        margin = 20

        if finger_rect.bottom() > viewport_rect.bottom() - margin:
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() + int(finger_rect.height())
            )

        elif finger_rect.top() < viewport_rect.top() + margin:
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(finger_rect.height())
            )
