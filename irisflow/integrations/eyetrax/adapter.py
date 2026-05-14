"""
EyeTraxAdapter — isola completamente o EyeTrax do restante do IrisFlow.

TODO (Fase 2): implementar integração real com EyeTrax.
Por enquanto é um stub que levanta NotImplementedError claro.
"""
from irisflow.tracking.base import BaseGazeEngine
from irisflow.core.logger import logger


class EyeTraxAdapter(BaseGazeEngine):
    """
    Adapter entre o IrisFlow e a biblioteca EyeTrax.
    Converte dados do EyeTrax em GazePoint do IrisFlow.
    Nenhuma classe do EyeTrax deve vazar além deste arquivo.
    """

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        # TODO Fase 2: inicializar EyeTrax aqui
        # from eyetrax import EyeTracker
        # self._tracker = EyeTracker()

    def start(self) -> None:
        raise NotImplementedError(
            "EyeTraxAdapter não implementado ainda. "
            "Use tracking_engine='mock' para desenvolvimento."
        )

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "eyetrax"
