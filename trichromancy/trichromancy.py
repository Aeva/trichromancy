
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPolygon
from PyQt5.QtCore import QPoint

from krita import Krita, DockWidget, ManagedColor


class TrichromancyWidget(QWidget):
    def __init__(self, parent=None):
        super(TrichromancyWidget, self).__init__(parent)
        self.cached_image = None
        self.bg_color = QColor.fromRgbF(0, 0, 0, 1)

    def redraw(self):
        self.cached_image = QPixmap(self.width(), self.height())
        painter = QPainter(self.cached_image)

        painter.fillRect(0, 0, self.width(), self.height(), self.bg_color)

        # todo!

        painter.end()

    def paintEvent(self, event):
        if self.cached_image is None:
            self.redraw()

        widget_painter = QPainter(self)
        self.rendered_image = self.cached_image.toImage()
        widget_painter.drawImage(0, 0, self.rendered_image)

    def resizeEvent(self, event):
        self.cached_image = None


class TrichromancyDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trichromancy")
        self.widget = QWidget()
        self.widget.minimumWidth = 100
        self.widget.minimumHeight = 100
        self.top_layout = QVBoxLayout()

        self.mixer_widget = TrichromancyWidget()
        self.top_layout.addWidget(self.mixer_widget)

        self.widget.setLayout(self.top_layout)
        self.setWidget(self.widget)
        self.mixer_widget.show()

    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

