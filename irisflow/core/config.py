"""
Configuração central do IrisFlow.
Valores padrão que podem ser sobrescritos por perfil de usuário.
"""
from dataclasses import dataclass, field


@dataclass
class IrisFlowConfig:
    # Opções: "mock" | "eyetrax" | "irisgazenet"
    tracking_engine: str = "eyetrax"

    # Dwell click
    dwell_time_ms: int = 1000       # tempo para ativar (ms)
    dwell_radius_px: int = 60       # raio de tolerância de movimento

    # UI
    button_min_height: int = 120    # altura mínima dos botões (px)
    font_size_large: int = 28       # tamanho da fonte principal
    font_size_medium: int = 20

    # TTS
    tts_lang: str = "pt"
    tts_rate: int = 160             # palavras por minuto

    # Perfil ativo
    active_profile: str = "default"


# Instância global de configuração
config = IrisFlowConfig()
