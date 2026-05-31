"""
Tipos próprios do IrisFlow para rastreamento ocular.
Nenhuma classe de terceiros deve vazar para fora de integrations/.
"""
from dataclasses import dataclass, field
import time


@dataclass(frozen=True)
class GazePoint:
    """Ponto de olhar tipado pelo IrisFlow."""
    x: float                              # pixels na tela (filtrado)
    y: float                              # pixels na tela (filtrado)
    confidence: float = 1.0              # 0.0–1.0
    timestamp: float = field(default_factory=time.monotonic)
    raw_x: float = 0.0                   # predição SVR antes do filtro
    raw_y: float = 0.0                   # predição SVR antes do filtro
    left_eye_openness: float = 0.0       # área do polígono do olho esquerdo (Shoelace, px²)
    right_eye_openness: float = 0.0      # área do polígono do olho direito  (Shoelace, px²)
    blink: bool = False                  # True quando piscar detectado
    tracking_state: str = "SUCCESS"      # "SUCCESS" | "FACE_MISSING" | "OUT_OF_BOUNDARIES"

    def is_valid(self) -> bool:
        """Retorna True se o ponto tem confiança mínima aceitável."""
        return self.confidence >= 0.4

    def distance_to(self, other: "GazePoint") -> float:
        """Distância euclidiana até outro ponto."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"GazePoint(x={self.x:.0f}, y={self.y:.0f}, conf={self.confidence:.2f})"
