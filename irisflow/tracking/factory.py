"""
EngineFactory — cria o engine de rastreamento conforme configuração.
Adicione novos engines aqui sem tocar no restante do código.
"""
from .base import BaseGazeEngine
from .mock_engine import MockGazeEngine
from irisflow.core.logger import logger


def create_engine(engine_type: str = "mock") -> BaseGazeEngine:
    """
    Retorna o engine de rastreamento correto.

    Args:
        engine_type: "mock" | "eyetrax"

    Returns:
        Instância de BaseGazeEngine pronta para uso.
    """
    if engine_type == "mock":
        logger.info("[EngineFactory] Criando MockGazeEngine")
        return MockGazeEngine()

    if engine_type == "eyetrax":
        # Importação lazy — EyeTrax só é carregado se necessário
        from irisflow.integrations.eyetrax.adapter import EyeTraxAdapter
        logger.info("[EngineFactory] Criando EyeTraxAdapter")
        return EyeTraxAdapter()

    raise ValueError(
        f"Engine desconhecido: '{engine_type}'. "
        f"Opções válidas: 'mock', 'eyetrax'"
    )
