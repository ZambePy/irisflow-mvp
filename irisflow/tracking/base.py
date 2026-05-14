"""
BaseGazeEngine — contrato que todo motor de rastreamento deve implementar.
A UI e a AccessibilityLayer só conhecem esta interface.
"""
from abc import ABC, abstractmethod
from typing import Callable
from .types import GazePoint


GazeCallback = Callable[[GazePoint], None]


class BaseGazeEngine(ABC):
    """Interface abstrata para motores de eye tracking."""

    def __init__(self) -> None:
        self._callbacks: list[GazeCallback] = []

    def add_gaze_listener(self, callback: GazeCallback) -> None:
        """Registra um callback que recebe GazePoint a cada frame."""
        self._callbacks.append(callback)

    def remove_gaze_listener(self, callback: GazeCallback) -> None:
        self._callbacks = [cb for cb in self._callbacks if cb is not callback]

    def _emit_gaze(self, point: GazePoint) -> None:
        """Notifica todos os listeners registrados."""
        for cb in self._callbacks:
            cb(point)

    @abstractmethod
    def start(self) -> None:
        """Inicia o rastreamento."""

    @abstractmethod
    def stop(self) -> None:
        """Para o rastreamento e libera recursos."""

    @abstractmethod
    def is_running(self) -> bool:
        """Retorna True se o motor está ativo."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Nome identificador do motor."""
