"""
KeyboardScreen — teclado virtual controlado por dwell.

Layout:
  ┌─────────────────────────────────────────┐
  │  [Display — texto digitado]             │
  │  A  B  C  D  E  F  G                   │
  │  H  I  J  K  L  M  N                   │
  │  O  P  Q  R  S  T  U                   │
  │  V  W  X  Y  Z  Ç                      │
  │  [ESPAÇO ────────] [⌫ APAGAR]           │
  │  [🔊 FALAR] [🗑️ LIMPAR] [🏠 HOME]       │
  └─────────────────────────────────────────┘

O display é somente-leitura — entrada exclusivamente por dwell.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger

_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZÇ")
_COLS = 7
_PLACEHOLDER = "Digite sua mensagem..."

_DISPLAY_BASE = (
    f"background-color: {COLORS['surface']};"
    f" border: 2px solid {COLORS['accent_blue']};"
    f" border-radius: 8px;"
    f" padding: 8px 12px;"
)


class KeyboardScreen(QWidget):
    go_home = pyqtSignal()

    def __init__(self, tts, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tts = tts
        self._text = ""
        self._buttons: dict[str, GazeButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 20, 30, 20)
        root.setSpacing(12)

        # ── Display ────────────────────────────────────────────────────────
        self._display = QLabel(_PLACEHOLDER)
        self._display.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._display.setMinimumHeight(80)
        self._display.setWordWrap(True)
        font_display = QFont()
        font_display.setPointSize(20)
        self._display.setFont(font_display)
        self._display.setStyleSheet(
            _DISPLAY_BASE + f" color: {COLORS['text_muted']};"
        )
        root.addWidget(self._display)

        # ── Letras ─────────────────────────────────────────────────────────
        letter_grid = QGridLayout()
        letter_grid.setSpacing(6)

        font_letter = QFont()
        font_letter.setPointSize(18)
        font_letter.setBold(True)

        for idx, letter in enumerate(_LETTERS):
            row, col = divmod(idx, _COLS)
            btn = self._make_button(f"key_{letter}", letter)
            btn._btn.setMinimumHeight(70)
            btn._btn.setFont(font_letter)
            btn._btn.setStyleSheet(
                f"QPushButton {{"
                f" background-color: {COLORS['surface']};"
                f" color: {COLORS['text_primary']};"
                f" border: 2px solid {COLORS['accent_blue']};"
                f" border-radius: 10px;"
                f" font-size: 22px;"
                f" font-weight: bold;"
                f"}}"
            )
            char = letter
            btn.activated.connect(lambda _, c=char: self._add_char(c))
            letter_grid.addWidget(btn, row, col)

        root.addLayout(letter_grid)

        # ── Linha de ações 1: ESPAÇO + APAGAR ─────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        btn_space = self._make_button("key_space", "ESPAÇO")
        btn_space.activated.connect(lambda _: self._add_char(" "))
        row1.addWidget(btn_space, 2)

        btn_delete = self._make_button("key_delete", "⌫  APAGAR")
        btn_delete.activated.connect(lambda _: self._delete_last())
        row1.addWidget(btn_delete, 1)

        root.addLayout(row1)

        # ── Linha de ações 2: FALAR + LIMPAR + HOME ────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        btn_speak = self._make_button("key_speak", "🔊  FALAR")
        btn_speak._btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {COLORS['surface']};"
            f" color: {COLORS['accent_green']};"
            f" border: 2px solid {COLORS['accent_green']};"
            f" border-radius: 12px;"
            f" font-size: 22px;"
            f" font-weight: bold;"
            f" padding: 12px 20px;"
            f" min-height: 110px;"
            f"}}"
        )
        btn_speak.activated.connect(lambda _: self._speak())
        row2.addWidget(btn_speak, 1)

        btn_clear = self._make_button("key_clear", "🗑️  LIMPAR")
        btn_clear.activated.connect(lambda _: self._clear_text())
        row2.addWidget(btn_clear, 1)

        btn_home = self._make_button("key_home", "🏠  HOME")
        btn_home.activated.connect(lambda _: self.go_home.emit())
        row2.addWidget(btn_home, 1)

        root.addLayout(row2)

    # ── Ações do teclado ──────────────────────────────────────────────────

    def _add_char(self, char: str) -> None:
        self._text += char
        self._update_display()

    def _delete_last(self) -> None:
        if self._text:
            self._text = self._text[:-1]
            self._update_display()

    def _speak(self) -> None:
        if self._text.strip():
            logger.info(f"[Keyboard] Falando: {self._text!r}")
            self._tts.speak(self._text)

    def _clear_text(self) -> None:
        self._text = ""
        self._update_display()

    def _update_display(self) -> None:
        if self._text:
            self._display.setText(self._text)
            self._display.setStyleSheet(
                _DISPLAY_BASE + f" color: {COLORS['text_primary']};"
            )
        else:
            self._display.setText(_PLACEHOLDER)
            self._display.setStyleSheet(
                _DISPLAY_BASE + f" color: {COLORS['text_muted']};"
            )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _make_button(self, region_id: str, label: str) -> GazeButton:
        btn = GazeButton(region_id=region_id, label=label, parent=self)
        self._buttons[region_id] = btn
        return btn

    # ── Interface para MainWindow ─────────────────────────────────────────

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._buttons
