"""
ProfileEditorScreen — criação e edição de perfil (modo cuidador via F10).
QLineEdit para nome (cuidador digita com teclado físico).
QPushButton para seletores (clique de mouse pelo cuidador).
GazeButton para ações de navegação (SALVAR / CANCELAR / EXCLUIR).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.ui.theme import COLORS
from irisflow.profiles.profile import Profile
from irisflow.profiles.profile_store import ProfileStore
from irisflow.core.logger import logger

_DWELL_OPTIONS = [
    ("Lento (1500ms)", 1500),
    ("Normal (1000ms)", 1000),
    ("Rápido (700ms)", 700),
]
_ENGINE_OPTIONS = [
    ("Webcam (EyeTrax)", "eyetrax"),
    ("Simulação (Mock)", "mock"),
]


class ProfileEditorScreen(QWidget):
    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(
        self,
        store: ProfileStore,
        profile: Profile | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._profile = profile
        self._dwell_ms: int = profile.dwell_time_ms if profile else 1000
        self._engine: str = profile.tracking_engine if profile else "eyetrax"
        self._dwell_btns: list[tuple[int, QPushButton]] = []
        self._engine_btns: list[tuple[str, QPushButton]] = []
        self._gaze_buttons: dict[str, GazeButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(80, 40, 80, 40)
        root.setSpacing(18)

        # ── Título ───────────────────────────────────────────────────────
        title_text = "Editar Perfil" if self._profile else "Novo Perfil"
        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_title = QFont()
        font_title.setPointSize(24)
        font_title.setBold(True)
        title.setFont(font_title)
        title.setStyleSheet(f"color: {COLORS['accent_blue']}; margin-bottom: 6px;")
        root.addWidget(title)

        # ── Nome ─────────────────────────────────────────────────────────
        lbl_name = QLabel("Nome do paciente:")
        lbl_name.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px;")
        root.addWidget(lbl_name)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Digite o nome...")
        if self._profile:
            self._name_input.setText(self._profile.name)
        self._name_input.setMinimumHeight(60)
        self._name_input.setStyleSheet(
            f"QLineEdit {{"
            f" background-color: {COLORS['surface']};"
            f" color: {COLORS['text_primary']};"
            f" border: 2px solid {COLORS['accent_blue']};"
            f" border-radius: 10px;"
            f" font-size: 22px;"
            f" padding: 8px 16px;"
            f"}}"
        )
        root.addWidget(self._name_input)

        # ── Dwell time ───────────────────────────────────────────────────
        lbl_dwell = QLabel("Velocidade de ativação:")
        lbl_dwell.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px;")
        root.addWidget(lbl_dwell)

        dwell_row = QHBoxLayout()
        dwell_row.setSpacing(12)
        for label, ms in _DWELL_OPTIONS:
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda _, m=ms: self._select_dwell(m))
            dwell_row.addWidget(btn)
            self._dwell_btns.append((ms, btn))
        root.addLayout(dwell_row)
        self._refresh_dwell_styles()

        # ── Engine ───────────────────────────────────────────────────────
        lbl_engine = QLabel("Modo de rastreamento:")
        lbl_engine.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px;")
        root.addWidget(lbl_engine)

        engine_row = QHBoxLayout()
        engine_row.setSpacing(12)
        for label, key in _ENGINE_OPTIONS:
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda _, k=key: self._select_engine(k))
            engine_row.addWidget(btn)
            self._engine_btns.append((key, btn))
        root.addLayout(engine_row)
        self._refresh_engine_styles()

        root.addStretch()

        # ── Ações: SALVAR | CANCELAR ──────────────────────────────────────
        actions = QHBoxLayout()
        actions.setSpacing(16)

        btn_save = self._make_gaze_button("save", "✓  SALVAR")
        btn_save._btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {COLORS['surface']};"
            f" color: {COLORS['accent_green']};"
            f" border: 2px solid {COLORS['accent_green']};"
            f" border-radius: 12px;"
            f" font-size: 26px; font-weight: bold;"
            f" padding: 12px 20px; min-height: 110px;"
            f"}}"
        )
        btn_save.activated.connect(lambda _: self._save())
        btn_save._btn.clicked.connect(self._save)
        actions.addWidget(btn_save)

        btn_cancel = self._make_gaze_button("cancel", "✗  CANCELAR")
        btn_cancel.activated.connect(lambda _: self.cancelled.emit())
        btn_cancel._btn.clicked.connect(self.cancelled.emit)
        actions.addWidget(btn_cancel)

        root.addLayout(actions)

        # ── Excluir (apenas em edição) ────────────────────────────────────
        if self._profile:
            btn_delete = self._make_gaze_button("delete", "🗑  EXCLUIR PERFIL")
            btn_delete._btn.setStyleSheet(
                f"QPushButton {{"
                f" background-color: {COLORS['surface']};"
                f" color: {COLORS['accent_red']};"
                f" border: 2px solid {COLORS['accent_red']};"
                f" border-radius: 12px;"
                f" font-size: 26px; font-weight: bold;"
                f" padding: 12px 20px; min-height: 110px;"
                f"}}"
            )
            btn_delete.activated.connect(lambda _: self._delete())
            btn_delete._btn.clicked.connect(self._delete)
            root.addWidget(btn_delete)

    # ── Seletores ────────────────────────────────────────────────────────

    def _select_dwell(self, ms: int) -> None:
        self._dwell_ms = ms
        self._refresh_dwell_styles()

    def _select_engine(self, key: str) -> None:
        self._engine = key
        self._refresh_engine_styles()

    def _refresh_dwell_styles(self) -> None:
        for ms, btn in self._dwell_btns:
            self._apply_selector_style(btn, selected=(ms == self._dwell_ms))

    def _refresh_engine_styles(self) -> None:
        for key, btn in self._engine_btns:
            self._apply_selector_style(btn, selected=(key == self._engine))

    @staticmethod
    def _apply_selector_style(btn: QPushButton, selected: bool) -> None:
        color = COLORS["accent_blue"] if selected else COLORS["text_muted"]
        bg = COLORS["surface_hover"] if selected else COLORS["surface"]
        border = COLORS["accent_blue"] if selected else COLORS["surface"]
        btn.setStyleSheet(
            f"QPushButton {{"
            f" background-color: {bg}; color: {color};"
            f" border: 2px solid {border};"
            f" border-radius: 10px;"
            f" font-size: 18px; font-weight: bold; min-height: 60px;"
            f"}}"
        )

    # ── Ações ────────────────────────────────────────────────────────────

    def _save(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            self._name_input.setFocus()
            return

        if self._profile is None:
            self._store.create(
                name=name,
                dwell_time_ms=self._dwell_ms,
                tracking_engine=self._engine,
            )
        else:
            self._profile.name = name
            self._profile.dwell_time_ms = self._dwell_ms
            self._profile.tracking_engine = self._engine
            self._store.update(self._profile)

        logger.info(f"[ProfileEditor] Salvo: {name}")
        self.saved.emit()

    def _delete(self) -> None:
        if self._profile:
            self._store.delete(self._profile.id)
        self.saved.emit()

    # ── Interface para MainWindow ─────────────────────────────────────────

    def _make_gaze_button(self, region_id: str, label: str) -> GazeButton:
        btn = GazeButton(region_id=region_id, label=label, parent=self)
        self._gaze_buttons[region_id] = btn
        return btn

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._gaze_buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._gaze_buttons
