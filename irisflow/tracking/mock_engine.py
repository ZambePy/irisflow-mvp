"""
MockGazeEngine — simula o olhar usando a posição do mouse.
Permite desenvolver e testar toda a UI sem webcam.
"""
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor

from .base import BaseGazeEngine
from .types import GazePoint
from irisflow.core.logger import logger


class MockGazeEngine(BaseGazeEngine):
    """
    Motor de simulação: captura a posição do cursor do mouse
    e emite como GazePoint em intervalos regulares.
    """

    POLL_INTERVAL_MS = 50  # ~20 fps, leve

    def __init__(self) -> None:
        super().__init__()
        self._timer = QTimer()
        self._timer.timeout.connect(self._poll_mouse)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._timer.start(self.POLL_INTERVAL_MS)
        logger.info("[MockGazeEngine] Iniciado — mouse simula o olhar")

    def stop(self) -> None:
        if not self._running:
            return
        self._timer.stop()
        self._running = False
        logger.info("[MockGazeEngine] Parado")

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "mock"

    def _poll_mouse(self) -> None:
        """Lê a posição global do mouse e emite como GazePoint."""
        pos = QCursor.pos()
        point = GazePoint(x=float(pos.x()), y=float(pos.y()), confidence=1.0)
        self._emit_gaze(point)
