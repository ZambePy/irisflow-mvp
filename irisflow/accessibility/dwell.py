"""
DwellController — implementa o dwell click assistivo.

Lógica:
1. Recebe GazePoint continuamente.
2. Quando o olhar permanece dentro de uma região por `dwell_time_ms`,
   emite o sinal `dwell_completed` com o ID da região.
3. Se o olhar sai antes do tempo, cancela e reinicia.
4. Emite progresso (0.0–1.0) para feedback visual.
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal, QRect

from irisflow.tracking.types import GazePoint
from irisflow.core.logger import logger


class DwellRegion:
    """Região retangular associada a um ID (ex: nome do botão)."""
    def __init__(self, region_id: str, rect: QRect) -> None:
        self.region_id = region_id
        self.rect = rect

    def contains(self, point: GazePoint) -> bool:
        return self.rect.contains(int(point.x), int(point.y))


class DwellController(QObject):
    """
    Gerencia o dwell click para todas as regiões registradas.
    Conecta-se ao TrackingService e emite sinais Qt.
    """

    # region_id, progresso 0.0–1.0
    dwell_progress = pyqtSignal(str, float)
    # region_id quando atingiu 100%
    dwell_completed = pyqtSignal(str)
    # quando o olhar saiu antes de completar
    dwell_cancelled = pyqtSignal(str)

    def __init__(self, dwell_time_ms: int = 1000, radius_px: int = 60) -> None:
        super().__init__()
        self._dwell_time = dwell_time_ms / 1000.0   # em segundos
        self._radius = radius_px
        self._regions: list[DwellRegion] = []

        self._active_region: str | None = None
        self._dwell_start: float | None = None
        self._last_gaze: GazePoint | None = None

    # ── Gerenciamento de regiões ──────────────────────────────────────────

    def register_region(self, region_id: str, rect: QRect) -> None:
        """Registra uma região clicável."""
        # Remove versão antiga se existir
        self._regions = [r for r in self._regions if r.region_id != region_id]
        self._regions.append(DwellRegion(region_id, rect))

    def unregister_region(self, region_id: str) -> None:
        self._regions = [r for r in self._regions if r.region_id != region_id]

    def clear_regions(self) -> None:
        self._regions.clear()
        self._reset()

    # ── Processamento do olhar ───────────────────────────────────────────

    def on_gaze(self, point: GazePoint) -> None:
        """Chamado a cada novo GazePoint. Conectar ao TrackingService."""
        if not point.is_valid():
            self._reset()
            return

        region = self._find_region(point)

        if region is None:
            # Olhar fora de qualquer região
            if self._active_region:
                self.dwell_cancelled.emit(self._active_region)
            self._reset()
            return

        if region.region_id != self._active_region:
            # Entrou em nova região
            if self._active_region:
                self.dwell_cancelled.emit(self._active_region)
            self._active_region = region.region_id
            self._dwell_start = time.monotonic()

        # Calcular progresso
        elapsed = time.monotonic() - self._dwell_start
        progress = min(elapsed / self._dwell_time, 1.0)
        self.dwell_progress.emit(self._active_region, progress)

        if progress >= 1.0:
            completed = self._active_region
            self._reset()
            self.dwell_completed.emit(completed)

    # ── Helpers ──────────────────────────────────────────────────────────

    def _find_region(self, point: GazePoint) -> DwellRegion | None:
        for region in self._regions:
            if region.contains(point):
                return region
        return None

    def reset(self) -> None:
        """Limpa estado ativo sem remover regiões. Evita dupla ativação após dwell_completed."""
        self._reset()

    def _reset(self) -> None:
        self._active_region = None
        self._dwell_start = None
