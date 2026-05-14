"""
HomeScreen — tela inicial do IrisFlow.

Layout:
  ┌─────────────────────────────────────┐
  │         IrisFlow                    │
  │  ┌──────────┐  ┌──────────┐        │
  │  │   SIM ✓  │  │  NÃO ✗  │        │
  │  └──────────┘  └──────────┘        │
  │  ┌──────────┐  ┌──────────┐        │
  │  │  FRASES  │  │ TECLADO  │        │
  │  └──────────┘  └──────────┘        │
  │  ┌───────────────────────────────┐  │
  │  │       🚨 EMERGÊNCIA           │  │
  │  └───────────────────────────────┘  │
  └─────────────────────────────────────┘
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.speech.tts import TTSEngine
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger


class HomeScreen(QWidget):
    def __init__(self, tts: TTSEngine, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tts = tts
        self._buttons: dict[str, GazeButton] = {}
        self._build_ui()
        self._connect_buttons()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 20)
        root.setSpacing(16)

        # ── Cabeçalho ──────────────────────────────────────────────────
        header = QLabel("IrisFlow")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        header.setFont(font)
        header.setStyleSheet(f"color: {COLORS['accent_blue']}; margin-bottom: 4px;")
        root.addWidget(header)

        subtitle = QLabel("Comunicação por Olhar  •  modo: simulação de mouse")
        subtitle.setObjectName("statusLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        # ── Linha 1: SIM | NÃO ─────────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        btn_sim = self._make_button("sim", "✓  SIM")
        btn_sim.set_object_name("btnSim")
        row1.addWidget(btn_sim)

        btn_nao = self._make_button("nao", "✗  NÃO")
        btn_nao.set_object_name("btnNao")
        row1.addWidget(btn_nao)

        root.addLayout(row1)

        # ── Linha 2: FRASES | TECLADO ───────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        btn_frases = self._make_button("frases", "💬  FRASES RÁPIDAS")
        row2.addWidget(btn_frases)

        btn_teclado = self._make_button("teclado", "⌨  TECLADO")
        row2.addWidget(btn_teclado)

        root.addLayout(row2)

        # ── Emergência ──────────────────────────────────────────────────
        btn_emergencia = self._make_button("emergencia", "🚨  EMERGÊNCIA  🚨")
        btn_emergencia.set_object_name("btnEmergencia")
        root.addWidget(btn_emergencia)

        # Espaçador
        root.addStretch()

    def _make_button(self, region_id: str, label: str) -> GazeButton:
        btn = GazeButton(region_id=region_id, label=label, parent=self)
        self._buttons[region_id] = btn
        return btn

    def _connect_buttons(self) -> None:
        self._buttons["sim"].activated.connect(self._on_sim)
        self._buttons["nao"].activated.connect(self._on_nao)
        self._buttons["frases"].activated.connect(self._on_frases)
        self._buttons["teclado"].activated.connect(self._on_teclado)
        self._buttons["emergencia"].activated.connect(self._on_emergencia)

    # ── Handlers ─────────────────────────────────────────────────────────

    def _on_sim(self, _: str = "") -> None:
        logger.info("[Home] SIM ativado")
        self._tts.speak("Sim")

    def _on_nao(self, _: str = "") -> None:
        logger.info("[Home] NÃO ativado")
        self._tts.speak("Não")

    def _on_frases(self, _: str = "") -> None:
        logger.info("[Home] FRASES ativado")
        self._tts.speak("Frases rápidas")
        # TODO Fase 3: navegar para QuickPhrasesScreen

    def _on_teclado(self, _: str = "") -> None:
        logger.info("[Home] TECLADO ativado")
        self._tts.speak("Teclado")
        # TODO Fase 3: navegar para KeyboardScreen

    def _on_emergencia(self, _: str = "") -> None:
        logger.info("[Home] EMERGÊNCIA ativado")
        self._tts.speak("Emergência! Preciso de ajuda!")
        msg = QMessageBox(self)
        msg.setWindowTitle("🚨 EMERGÊNCIA")
        msg.setText("PRECISO DE AJUDA AGORA!")
        msg.setStyleSheet(
            f"QMessageBox {{ background-color: {COLORS['emergency_bg']}; }}"
            f"QLabel {{ color: {COLORS['accent_red']}; font-size: 24px; font-weight: bold; }}"
        )
        msg.exec()

    # ── Interface pública para MainWindow ─────────────────────────────────

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._buttons
