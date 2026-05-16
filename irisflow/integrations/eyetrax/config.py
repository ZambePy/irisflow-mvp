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
    gaze_filter: str = "kalman"

    # Força do filtro EMA (0.0–1.0) — só usado com kalman_ema
    ema_alpha: float = 0.3

    # Tipo de calibração: "9p" | "5p" | "lissajous" | "dense"
    calibration_type: str = "9p"

    # Caminho para salvar/carregar modelo treinado (None = não persistir)
    model_path: str | None = "irisflow_gaze_model.pkl"

    # FPS alvo do loop de captura
    capture_fps: int = 30

    # Confiança mínima — frames com blink são descartados automaticamente
    # (EyeTrax já retorna blink=True nesses casos)


# Instância padrão
eyetrax_config = EyeTraxConfig()
