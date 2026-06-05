"""
Profile — dados de um usuário do IrisFlow.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Profile:
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dwell_time_ms: int = 1000
    tracking_engine: str = "mock"
    favorite_phrases: list = field(default_factory=list)
    is_calibrated: bool = False
    calibration_model_path: str | None = None
    calibration_metrics: dict | None = None
    calibrated_at: str | None = None
    created_at: str = field(default_factory=_now_iso)
    last_used_at: str = field(default_factory=_now_iso)
