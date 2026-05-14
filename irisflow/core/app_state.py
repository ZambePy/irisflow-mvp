"""Estado global do IrisFlow (simples, sem ORM)."""
from dataclasses import dataclass, field


@dataclass
class AppState:
    tracking_active: bool = False
    tracking_engine_name: str = "mock"
    current_screen: str = "home"
    active_profile_id: str = "default"
    emergency_mode: bool = False


# Instância global
app_state = AppState()
