"""
Configurações específicas do EyeTrax.
Isoladas aqui — o restante do IrisFlow não conhece estes detalhes.
"""
from dataclasses import dataclass


@dataclass
class EyeTraxConfig:
    # Índice da webcam (0 = padrão do sistema)
    camera_index: int = 0

    # Tipo de filtro de suavização: "kalman" | "kalman_ema" | "none"
    gaze_filter: str = "kalman_ema"

    # Força do filtro EMA (0.0–1.0) — só usado com kalman_ema
    ema_alpha: float = 0.2

    # Tipo de calibração: "9p" | "5p" | "lissajous" | "dense"
    calibration_type: str = "dense"

    # Parâmetros da grade densa (usados apenas quando calibration_type == "dense")
    dense_grid_rows: int = 7
    dense_grid_cols: int = 7
    dense_grid_margin: float = 0.10

    # Caminho para salvar/carregar modelo treinado (None = não persistir)
    model_path: str | None = "irisflow_gaze_model.pkl"

    # FPS alvo do loop de captura
    capture_fps: int = 30

    # Deadzone — trava o cursor durante microtremores oculares involuntários
    deadzone_radius: float = 12.0   # distância mínima (px) para considerar movimento real
    deadzone_frames: int = 25       # frames parado antes de liberar o cursor

    # Confiança mínima — frames com blink são descartados automaticamente
    # (EyeTrax já retorna blink=True nesses casos)


# Instância padrão
eyetrax_config = EyeTraxConfig()
