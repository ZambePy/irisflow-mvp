"""
GazeCursor — widget transparente que exibe a posição do olhar na tela.
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor

from irisflow.ui.theme import COLORS

_RADIUS = 10   # raio do círculo (diâmetro ~20px)
_PAD = 4       # margem ao redor do círculo


class GazeCursor(QWidget):
    """Widget sem borda, sempre no topo, que marca onde o olhar está."""

    def __init__(self) -> None:
        size = (_RADIUS + _PAD) * 2
        super().__init__(
            None,
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(size, size)
        self.hide()

    def move_to(self, x: float, y: float) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            ratio = screen.devicePixelRatio()
            if x > screen.geometry().width():
                x = x / ratio
                y = y / ratio
        half = _RADIUS + _PAD
        self.move(int(x) - half, int(y) - half)
        if not self.isVisible():
            self.show()
            self.raise_()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(COLORS["accent_blue"])
        color.setAlphaF(0.7)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(_PAD, _PAD, _RADIUS * 2, _RADIUS * 2)
