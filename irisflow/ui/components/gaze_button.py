"""
GazeButton — botão assistivo com feedback visual de dwell click.

Combina QPushButton + QProgressBar em um widget único.
Registra-se automaticamente no DwellController ao ser exibido.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer
from PyQt6.QtGui import QFont

from irisflow.ui.theme import COLORS


class GazeButton(QWidget):
    """
    Botão assistivo para eye tracking.

    Sinais:
        activated(region_id): emitido quando o dwell completa.
    """

    activated = pyqtSignal(str)

    def __init__(
        self,
        region_id: str,
        label: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.region_id = region_id
        self._progress_value = 0
        self._is_dwelling = False

        self._build_ui(label)

    def _build_ui(self, label: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Botão principal
        self._btn = QPushButton(label)
        self._btn.setMinimumHeight(110)
        self._btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn.clicked.connect(lambda: self.activated.emit(self.region_id))
        layout.addWidget(self._btn)

        # Barra de progresso dwell
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

    def set_object_name(self, name: str) -> None:
        """Permite aplicar estilos via QSS por objectName."""
        self._btn.setObjectName(name)
        self._btn.style().unpolish(self._btn)
        self._btn.style().polish(self._btn)

    # ── Interface para o DwellController ─────────────────────────────────

    def on_dwell_progress(self, progress: float) -> None:
        """Atualiza a barra de progresso (0.0–1.0)."""
        value = int(progress * 100)
        self._progress.setValue(value)
        self._set_dwelling_style(progress > 0)

    def on_dwell_cancelled(self) -> None:
        self._progress.setValue(0)
        self._set_dwelling_style(False)

    def on_dwell_completed(self) -> None:
        self._progress.setValue(100)
        # Flash visual de confirmação
        QTimer.singleShot(200, lambda: self._progress.setValue(0))
        self.activated.emit(self.region_id)

    def global_rect(self) -> QRect:
        """Retorna a QRect em coordenadas globais de tela."""
        top_left = self.mapToGlobal(self.rect().topLeft())
        return QRect(top_left.x(), top_left.y(), self.width(), self.height())

    # ── Helpers ──────────────────────────────────────────────────────────

    def _set_dwelling_style(self, active: bool) -> None:
        color = COLORS["accent_blue"] if active else COLORS["surface"]
        self._progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )
