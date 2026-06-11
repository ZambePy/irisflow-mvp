"""Tipos de eventos WebSocket — protocolo entre frontend e backend IrisFlow."""

from typing import TypedDict


# ── Frontend → Backend ────────────────────────────────────────────────────────

class StartTrackingMsg(TypedDict):
    """Inicia o tracking com o engine especificado."""
    type: str          # "start_tracking"
    engine: str        # "eyetrax" | "irisgazenet" | "mock"


class StopTrackingMsg(TypedDict):
    """Para o tracking ativo."""
    type: str          # "stop_tracking"


class SpeakMsg(TypedDict):
    """Sintetiza texto em voz."""
    type: str          # "speak"
    text: str


class EmergencyMsg(TypedDict):
    """Dispara alerta de emergência."""
    type: str          # "emergency"


class DwellRegion(TypedDict):
    """Região retangular monitorada pelo DwellController."""
    id: str
    x: int
    y: int
    w: int
    h: int


class DwellRegionsMsg(TypedDict):
    """Registra regiões de dwell enviadas pelo frontend."""
    type: str                  # "dwell_regions"
    regions: list[DwellRegion]


# ── Backend → Frontend ────────────────────────────────────────────────────────

class GazeMsg(TypedDict):
    """Ponto de gaze capturado pelo engine de rastreamento."""
    type: str          # "gaze"
    x: float
    y: float
    confidence: float
    timestamp: float


class DwellProgressMsg(TypedDict):
    """Progresso do dwell em uma região (0.0–1.0)."""
    type: str          # "dwell_progress"
    region_id: str
    progress: float


class DwellCompletedMsg(TypedDict):
    """Dwell concluído — ação deve ser executada."""
    type: str          # "dwell_completed"
    region_id: str


class DwellCancelledMsg(TypedDict):
    """Dwell cancelado — olhar saiu da região antes do tempo."""
    type: str          # "dwell_cancelled"
    region_id: str


class TrackingStatusMsg(TypedDict):
    """Estado atual do serviço de tracking."""
    type: str          # "tracking_status"
    running: bool
    engine: str | None


class ErrorMsg(TypedDict):
    """Erro ocorrido no backend."""
    type: str          # "error"
    message: str
