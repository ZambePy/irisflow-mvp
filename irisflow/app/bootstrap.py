"""
Bootstrap — inicializa e conecta todos os serviços do IrisFlow.
Separa a criação de objetos do entrypoint main.py.
"""
from irisflow.core.config import config
from irisflow.core.logger import logger
from irisflow.tracking.factory import create_engine
from irisflow.tracking.service import TrackingService
from irisflow.accessibility.dwell import DwellController
from irisflow.speech.tts import TTSEngine


def bootstrap() -> tuple[TrackingService, DwellController, TTSEngine]:
    """
    Cria e retorna os serviços principais.
    A UI recebe esses objetos prontos — sem saber como foram criados.
    """
    logger.info("[Bootstrap] Inicializando IrisFlow...")

    engine = create_engine(config.tracking_engine)
    tracking = TrackingService(engine)

    dwell = DwellController(
        dwell_time_ms=config.dwell_time_ms,
        radius_px=config.dwell_radius_px,
    )

    tts = TTSEngine(rate=config.tts_rate)

    logger.info("[Bootstrap] Pronto.")
    return tracking, dwell, tts
