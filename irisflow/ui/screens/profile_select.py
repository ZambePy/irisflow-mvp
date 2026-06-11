"""
ProfileSelectScreen — seleção de perfil ao abrir o app.
Máximo 4 perfis visíveis (MVP).
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.ui.theme import COLORS
from irisflow.profiles.profile_store import ProfileStore
from irisflow.core.logger import logger


class ProfileSelectScreen(QWidget):
    profile_selected = pyqtSignal(str)       # profile_id
    new_profile_requested = pyqtSignal()

    def __init__(self, store: ProfileStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self._buttons: dict[str, GazeButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(80, 50, 80, 50)
        root.setSpacing(20)

        title = QLabel("Quem está usando?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['accent_blue']}; margin-bottom: 12px;")
        root.addWidget(title)

        for profile in self._store.get_all()[:4]:
            btn = self._make_button(f"profile_{profile.id}", profile.name)
            pid = profile.id
            btn.activated.connect(lambda _, p=pid: self._on_selected(p))
            root.addWidget(btn)

        btn_new = self._make_button("new_profile", "＋  NOVO PERFIL")
        btn_new._btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {COLORS['surface']};"
            f" color: {COLORS['accent_green']};"
            f" border: 2px solid {COLORS['accent_green']};"
            f" border-radius: 12px;"
            f" font-size: 26px;"
            f" font-weight: bold;"
            f" padding: 12px 20px;"
            f" min-height: 110px;"
            f"}}"
        )
        btn_new.activated.connect(lambda _: self.new_profile_requested.emit())
        root.addWidget(btn_new)

        root.addStretch()

    def _on_selected(self, profile_id: str) -> None:
        self._store.set_last_used(profile_id)
        logger.info(f"[ProfileSelect] Perfil selecionado: {profile_id}")
        self.profile_selected.emit(profile_id)

    def _make_button(self, region_id: str, label: str) -> GazeButton:
        btn = GazeButton(region_id=region_id, label=label, parent=self)
        self._buttons[region_id] = btn
        return btn

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._buttons
