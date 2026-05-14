"""
Eventos internos do IrisFlow.
Desacopla camadas sem criar dependências circulares.
"""
from enum import Enum, auto


class AppEvent(Enum):
    GAZE_UPDATED = auto()
    DWELL_STARTED = auto()
    DWELL_PROGRESS = auto()
    DWELL_COMPLETED = auto()
    DWELL_CANCELLED = auto()
    TRACKING_STARTED = auto()
    TRACKING_STOPPED = auto()
    TRACKING_ERROR = auto()
    BUTTON_ACTIVATED = auto()
    SPEECH_STARTED = auto()
    SPEECH_FINISHED = auto()
    EMERGENCY_TRIGGERED = auto()
    PROFILE_LOADED = auto()
