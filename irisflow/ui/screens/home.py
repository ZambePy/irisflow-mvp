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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.speech.tts import TTSEngine
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger


class HomeScreen(QWidget):
    overlay_opened = pyqtSignal()
    overlay_closed = pyqtSignal()
    navigate_frases = pyqtSignal()
    navigate_teclado = pyqtSignal()

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
        logger.info("[Home] _on_sim chamado — falando Sim")
        self._tts.speak("Sim")

    def _on_nao(self, _: str = "") -> None:
        logger.info("[Home] _on_nao chamado — falando Não")
        self._tts.speak("Não")

    def _on_frases(self, _: str = "") -> None:
        logger.info("[Home] _on_frases chamado — navegando para Frases Rápidas")
        self.navigate_frases.emit()

    def _on_teclado(self, _: str = "") -> None:
        logger.info("[Home] _on_teclado chamado — navegando para Teclado")
        self.navigate_teclado.emit()

    def _on_emergencia(self, _: str = "") -> None:
        logger.info("[Home] _on_emergencia chamado — falando Emergência")
        self._tts.speak("Emergência! Preciso de ajuda!")
        self._show_emergency_overlay()

    def _show_emergency_overlay(self) -> None:
        if self.findChild(QWidget, "emergencyOverlay"):
            return

        overlay = QWidget(self)
        overlay.setObjectName("emergencyOverlay")
        overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        overlay.setStyleSheet(
            f"QWidget#emergencyOverlay {{ background-color: {COLORS['emergency_bg']}; }}"
        )
        overlay.resize(self.size())
        overlay.move(0, 0)
        overlay.raise_()

        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(32)

        title = QLabel("🚨 EMERGÊNCIA 🚨")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_title = QFont()
        font_title.setPointSize(36)
        font_title.setBold(True)
        title.setFont(font_title)
        title.setStyleSheet(f"color: {COLORS['accent_red']};")
        layout.addWidget(title)

        subtitle = QLabel("PRECISO DE AJUDA AGORA!")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_sub = QFont()
        font_sub.setPointSize(24)
        font_sub.setBold(True)
        subtitle.setFont(font_sub)
        subtitle.setStyleSheet("color: white;")
        layout.addWidget(subtitle)

        close_btn = QPushButton("FECHAR")
        close_btn.setFixedHeight(60)
        font_btn = QFont()
        font_btn.setPointSize(16)
        font_btn.setBold(True)
        close_btn.setFont(font_btn)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #333333; color: white;"
            " border-radius: 8px; padding: 8px 32px; }"
            "QPushButton:hover { background-color: #555555; }"
        )
        close_btn.clicked.connect(lambda: self._close_emergency_overlay(overlay))
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        overlay.show()
        self.overlay_opened.emit()

    def _close_emergency_overlay(self, overlay: QWidget) -> None:
        overlay.deleteLater()
        self.overlay_closed.emit()

    # ── Interface pública para MainWindow ─────────────────────────────────

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._buttons
