"""
TrackingService — gerencia o ciclo de vida do engine de rastreamento
e distribui GazePoints para os consumidores registrados.
"""
from .base import BaseGazeEngine, GazeCallback
from .types import GazePoint
from irisflow.core.logger import logger


class TrackingService:
    """
    Ponto único de acesso ao rastreamento ocular.
    Aceita qualquer BaseGazeEngine — mock ou real.
    """

    def __init__(self, engine: BaseGazeEngine) -> None:
        self._engine = engine
        self._engine.add_gaze_listener(self._on_gaze)
        self._listeners: list[GazeCallback] = []
        logger.info(f"[TrackingService] Engine: {engine.engine_name}")

    def add_listener(self, callback: GazeCallback) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: GazeCallback) -> None:
        self._listeners = [cb for cb in self._listeners if cb is not callback]

    def start(self) -> None:
        self._engine.start()

    def stop(self) -> None:
        self._engine.stop()

    def is_running(self) -> bool:
        return self._engine.is_running()

    @property
    def engine_name(self) -> str:
        return self._engine.engine_name

    def _on_gaze(self, point: GazePoint) -> None:
        for cb in self._listeners:
            cb(point)
