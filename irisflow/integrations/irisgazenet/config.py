"""
Configurações específicas do IrisGazeNet.
Isoladas aqui — o restante do IrisFlow não conhece estes detalhes.
"""
from irisflow.core.paths import get_user_data_dir


@dataclass
class IrisGazeNetConfig:
    # Índice da webcam (0 = padrão do sistema)
    camera_index: int = 0

    # Caminho para salvar/carregar modelo treinado
    model_path: str = str(get_user_data_dir() / "models" / "irisflow_base_model.pkl")

    # FPS alvo do loop de captura
    capture_fps: int = 30

    # Deadzone — trava o cursor durante microtremores oculares involuntários
    deadzone_radius: float = 0.0    # desativado no engine ML; suavização EMA faz o amortecimento
    deadzone_frames: int = 0

    # Suavização responsiva do cursor real
    smoothing_alpha: float = 0.55

    # Validação mínima do modelo carregado. Se um eixo não consegue variar ao
    # menos isso nos próprios support vectors, o cursor ficará visualmente parado.
    min_prediction_span_px: float = 24.0

    # Dimensões da tela (usadas como fallback no predict)
    screen_w: int = 1920
    screen_h: int = 1080


# Instância padrão
irisgazenet_config = IrisGazeNetConfig()
