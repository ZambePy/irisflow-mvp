"""
Bootstrap — inicializa e conecta todos os serviços do IrisFlow.
Suporta engine 'mock' e 'eyetrax'.
"""
from irisflow.core.config import config
from irisflow.core.logger import logger
from irisflow.tracking.factory import create_engine
from irisflow.tracking.service import TrackingService
from irisflow.accessibility.dwell import DwellController
from irisflow.speech.tts import TTSEngine
from irisflow.profiles.profile_store import ProfileStore


def bootstrap() -> tuple[TrackingService, DwellController, TTSEngine, ProfileStore]:
    """
    Cria e retorna os serviços principais.

    Para engine 'eyetrax': o adapter é criado mas NÃO iniciado aqui.
    O MainWindow é responsável por pedir calibração antes de start().
    """
    logger.info(f"[Bootstrap] Engine: {config.tracking_engine}")

    engine = create_engine(config.tracking_engine)
    tracking = TrackingService(engine)

    dwell = DwellController(
        dwell_time_ms=config.dwell_time_ms,
        radius_px=config.dwell_radius_px,
    )

    tts = TTSEngine(rate=config.tts_rate)

    profile_store = ProfileStore()

    logger.info("[Bootstrap] Serviços prontos")
    return tracking, dwell, tts, profile_store
