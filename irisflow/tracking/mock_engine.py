"""
MockGazeEngine — simula o olhar usando a posição do mouse.
Permite desenvolver e testar toda a UI sem webcam.
Usa threading.Thread em vez de QTimer para funcionar tanto no app Qt
quanto no backend FastAPI (sem event loop Qt ativo).
"""

import ctypes
import sys
import threading
import time

from .base import BaseGazeEngine
from .types import GazePoint
from irisflow.core.logger import logger

_POLL_INTERVAL = 0.05  # 20 fps


def _read_cursor() -> tuple[float, float]:
    """Lê posição do cursor normalizada (0.0–1.0) relativa à resolução do ecrã."""
    if sys.platform == "win32":
        class _POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = _POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        screen_w = ctypes.windll.user32.GetSystemMetrics(0) or 1920
        screen_h = ctypes.windll.user32.GetSystemMetrics(1) or 1080
        return float(pt.x) / screen_w, float(pt.y) / screen_h
    # Fallback via Qt
    try:
        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QApplication
        pos = QCursor.pos()
        screen = QApplication.primaryScreen()
        if screen:
            size = screen.size()
            return float(pos.x()) / size.width(), float(pos.y()) / size.height()
        return 0.5, 0.5
    except Exception:
        return 0.5, 0.5


class MockGazeEngine(BaseGazeEngine):
    """
    Motor de simulação: captura a posição do cursor do mouse
    e emite como GazePoint em intervalos regulares (~20 fps).
    """

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("[MockGazeEngine] Iniciado — mouse simula o olhar")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("[MockGazeEngine] Parado")

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "mock"

    def _loop(self) -> None:
        """Thread principal — emite GazePoint a cada POLL_INTERVAL."""
        while self._running:
            x, y = _read_cursor()
            self._emit_gaze(GazePoint(x=x, y=y, confidence=1.0))
            time.sleep(_POLL_INTERVAL)
