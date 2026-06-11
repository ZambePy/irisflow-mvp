"""
GazeCursor — widget transparente que exibe a posição do olhar na tela.
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen

_WIDGET_SIZE = 28


class GazeCursor(QWidget):
    """Widget sem borda, sempre no topo, que marca onde o olhar está."""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(_WIDGET_SIZE, _WIDGET_SIZE)
        self.hide()

    def move_to(self, x: float, y: float) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            ratio = screen.devicePixelRatio()
            if x > screen.geometry().width():
                x = x / ratio
                y = y / ratio
        half = _WIDGET_SIZE // 2
        self.move(int(x) - half, int(y) - half)
        if not self.isVisible():
            self.show()
            self.raise_()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        margin = 3
        pen = QPen(QColor("#FF0000"))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(margin),
            int(margin),
            int(self.width() - margin * 2),
            int(self.height() - margin * 2),
        )
