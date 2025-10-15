
import math

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPolygonF, QPainterPath, QPalette
from PyQt5.QtCore import QPoint, QPointF

from krita import Krita, DockWidget, ManagedColor

from mollytime import mollytime
ColorSpace = mollytime.ColorSpace
ColorPoint = mollytime.ColorPoint


mollytime.set_gamma(1.8)


def sRGB_to_OkLAB(r, g, b):
    return mollytime.convert_color((r, g, b), ColorSpace.sRGB, ColorSpace.OkLAB).channels


def OkLAB_to_sRGB(l, a, b):
    return mollytime.convert_color((l, a, b), ColorSpace.OkLAB, ColorSpace.sRGB).channels


def LinearRGB_to_OkLAB(r, g, b):
    return mollytime.convert_color((r, g, b), ColorSpace.LinearRGB, ColorSpace.OkLAB).channels


def OkLAB_to_LinearRGB(l, a, b):
    return mollytime.convert_color((l, a, b), ColorSpace.OkLAB, ColorSpace.LinearRGB).channels


RGB_to_OkLAB = sRGB_to_OkLAB
OkLAB_to_RGB = OkLAB_to_sRGB


class TrichromancyWidget(QWidget):
    def __init__(self, docker, parent=None):
        super(TrichromancyWidget, self).__init__(parent)
        self.docker = docker
        self.bg_fill = QColor.fromRgbF(58 / 255, 58 / 255, 58 / 255, 1)
        self.primaries = [
            RGB_to_OkLAB(0, 0, 53 / 255),
            RGB_to_OkLAB(1, 240 / 255, 0),
            RGB_to_OkLAB(96 / 255, 0, 35 / 255)]
        assert(len(self.primaries[0]) == 3)

        def turn(fraction):
            center_x = 0
            center_y = 0
            radius = .5
            fraction += -0.03
            return [center_x + radius * math.sin(math.pi * 2 * fraction),
                    center_y - radius * math.cos(math.pi * 2 * fraction)]

        self.unscaled = [turn(i/3) for i in range(3)]
        x_parts = [x for (x, y) in self.unscaled]
        y_parts = [y for (x, y) in self.unscaled]
        min_x = min(x_parts)
        min_y = min(y_parts)
        shift_x = abs(max(x_parts) - min_x) / 2
        shift_y = abs(max(y_parts) - min_y) / 2
        for i, (x, y) in enumerate(self.unscaled):
            self.unscaled[i] = [
                (x - min_x) - shift_x,
                (y - min_y) - shift_y]

        self.picking = False

    def redraw(self):
        self.cached_image = QPixmap(self.width(), self.height())
        painter = QPainter(self.cached_image)

        extent = min(self.width(), self.height())
        center_x = self.width() // 2
        center_y = self.height() // 2
        vertices = [[int(x * extent + center_x), int(y * extent + center_y)] for x, y in self.unscaled]

        painter.fillRect(0, 0, self.width(), self.height(), self.bg_fill)

        primary_radius = max(extent // 10, 2)

        for primary, coord in zip(self.primaries, vertices):
            r, g, b = OkLAB_to_RGB(*primary)
            painter.setBrush(QBrush(QColor.fromRgbF(r, g, b, 1)))
            painter.drawEllipse(QPoint(*coord), primary_radius, primary_radius)

        def draw_triangle(verts, color):
            verts = verts + [verts[0]]
            points = [QPointF(x, y) for x, y in verts]
            path = QPainterPath()
            path.addPolygon(QPolygonF(points))
            r, g, b = OkLAB_to_RGB(*color)
            painter.fillPath(path, QBrush(QColor.fromRgbF(r, g, b, 1)))

        def midpoint(a, b):
            return [(a[i] + b[i]) * 0.5 for i in range(len(a))]

        def tessellate(verts, colors, depth=0):
            v_a, v_b, v_c = verts
            v_ab = midpoint(v_a, v_b)
            v_bc = midpoint(v_b, v_c)
            v_ca = midpoint(v_c, v_a)
            c_a, c_b, c_c = colors
            c_ab = midpoint(c_a, c_b)
            c_bc = midpoint(c_b, c_c)
            c_ca = midpoint(c_c, c_a)

            triangles = [
                [[v_a, v_ab, v_ca], [c_a, c_ab, c_ca]],
                [[v_ab, v_b, v_bc], [c_ab, c_b, c_bc]],
                [[v_bc, v_c, v_ca], [c_bc, c_c, c_ca]],
                [[v_ab, v_bc, v_ca], [c_ab, c_bc, c_ca]]]

            if depth > 0:
                for verts, colors in triangles:
                    tessellate(verts, colors, depth - 1)
            else:
                for verts, colors in triangles:
                    r = sum([r for r, g, b in colors]) / 3
                    g = sum([g for r, g, b in colors]) / 3
                    b = sum([b for r, g, b in colors]) / 3
                    draw_triangle(verts, [r, g, b])

        tessellate(vertices, self.primaries, 5)

        painter.end()

    def paintEvent(self, event):
        if self.cached_image is None:
            self.redraw()

        widget_painter = QPainter(self)
        self.rendered_image = self.cached_image.toImage()
        widget_painter.drawImage(0, 0, self.rendered_image)

    def resizeEvent(self, event):
        self.cached_image = None

    def pick(self, event):
        if self.cached_image and self.rendered_image:
            pos = event.pos()
            x = min(max(pos.x(), 0), self.width())
            y = min(max(pos.y(), 0), self.height())
            point = QPoint(x, y)
            color = self.rendered_image.pixelColor(QPoint(x, y))
            if self.docker.canvas() and self.docker.canvas().view():
                color = ManagedColor.fromQColor(color, self.docker.canvas())
                self.docker.canvas().view().setForeGroundColor(color)

    def set_primary(self, primary_index, r, g, b):
        self.primaries[primary_index] = RGB_to_OkLAB(r, g, b)
        self.cached_image = None
        self.update()

    def mousePressEvent(self, event):
        self.pick(event)
        self.picking = True

    def mouseMoveEvent(self, event):
        if self.picking:
            self.pick(event)

    def mouseReleaseEvent(self, event):
        self.pick(event)
        self.picking = False


class SwatchButton(QWidget):
    def __init__(self, primary_index, docker, parent=None):
        super(SwatchButton, self).__init__(parent)
        self.setMinimumWidth(32)
        self.setMinimumHeight(32)
        self.setMaximumWidth(64)
        self.setMaximumHeight(64)

        initial_color = docker.mixer_widget.primaries[primary_index]
        r, g, b = OkLAB_to_RGB(*initial_color)
        self.button_color = QColor.fromRgbF(r, g, b, 1)

        self.primary_index = primary_index
        self.docker = docker
        self.swatch_image = None

    def redraw(self):
        self.swatch_image = QPixmap(self.width(), self.height())
        painter = QPainter(self.swatch_image)
        painter.fillRect(0, 0, self.width(), self.height(), self.button_color)
        painter.end()

    def update_color(self):
        managed_color = self.docker.canvas().view().foregroundColor()
        self.button_color = managed_color.colorForCanvas(self.docker.canvas())
        self.swatch_image = None
        self.redraw()
        self.update()
        r, g, b, a = self.button_color.getRgbF()
        self.docker.mixer_widget.set_primary(self.primary_index, r, g, b)

    def paintEvent(self, event):
        if self.swatch_image is None:
            self.redraw()

        widget_painter = QPainter(self)
        self.rendered_image = self.swatch_image.toImage()
        widget_painter.drawImage(0, 0, self.rendered_image)

    def mouseReleaseEvent(self, event):
        self.update_color()


class TrichromancyDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trichromancy")
        self.widget = QWidget()
        self.widget.minimumWidth = 100
        self.widget.minimumHeight = 100
        self.top_layout = QVBoxLayout()
        self.swatch_layout = QHBoxLayout()

        self.mixer_widget = TrichromancyWidget(self)
        self.top_layout.addWidget(self.mixer_widget)

        self.primary_buttons = []
        for primary_index in [2, 0, 1]:
            button = SwatchButton(primary_index, self)
            self.primary_buttons.append(button)
            self.swatch_layout.addWidget(button)
        self.top_layout.addLayout(self.swatch_layout)

        self.widget.setLayout(self.top_layout)
        self.setWidget(self.widget)
        self.mixer_widget.show()

    def canvasChanged(self, canvas):
        pass

