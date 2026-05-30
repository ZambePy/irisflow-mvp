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
        engine_type: "mock" | "irisgazenet"

    Returns:
        Instância de BaseGazeEngine pronta para uso.
    """
    if engine_type == "mock":
        logger.info("[EngineFactory] Criando MockGazeEngine")
        return MockGazeEngine()

    if engine_type == "eyetrax":
        raise ValueError(
            "O motor 'eyetrax' foi removido do IrisFlow. "
            "Use 'mock' para desenvolvimento ou 'irisgazenet' para produção."
        )

    if engine_type == "irisgazenet":
        from irisflow.integrations.irisgazenet.adapter import IrisGazeNetAdapter
        logger.info("[EngineFactory] Criando IrisGazeNetAdapter")
        return IrisGazeNetAdapter()

    raise ValueError(
        f"Engine desconhecido: '{engine_type}'. "
        f"Opções válidas: 'mock', 'irisgazenet'"
    )
