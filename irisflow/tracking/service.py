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

    @property
    def status_message(self) -> str | None:
        return getattr(self._engine, "status_message", None)

    @property
    def state(self) -> str:
        return getattr(self._engine, "state", "running" if self.is_running() else "idle")

    @property
    def metrics(self) -> dict | None:
        return getattr(self._engine, "metrics", None)

    def start_collecting_point(self, point_index: int, expected_x: float, expected_y: float) -> None:
        if hasattr(self._engine, "start_collecting_point"):
            self._engine.start_collecting_point(point_index, expected_x, expected_y)

    def wait_for_collection(self, timeout: float = 20.0) -> bool:
        if hasattr(self._engine, "wait_for_collection"):
            return self._engine.wait_for_collection(timeout)
        return False

    def get_collected_data(self) -> list[dict]:
        if hasattr(self._engine, "get_collected_data"):
            return self._engine.get_collected_data()
        return []

    def start_calibration_mode(self) -> None:
        if hasattr(self._engine, "start_calibration_mode"):
            self._engine.start_calibration_mode()

    def _on_gaze(self, point: GazePoint) -> None:
        for cb in self._listeners:
            cb(point)
