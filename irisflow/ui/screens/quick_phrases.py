"""
QuickPhrasesScreen — frases rápidas por contexto.

Nível 1: grade 2×2 de categorias + categoria especial ⭐ Favoritas
Nível 2: frases da categoria selecionada (máx. 6) com botão FAVORITAR

Ao trocar de nível emite screen_changed para o MainWindow
re-registrar as regiões dwell.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.components.gaze_button import GazeButton
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger

_FAVORITES_ID = "__favorites__"

_PHRASE_STYLE = (
    f"QPushButton {{"
    f" background-color: {COLORS['surface']};"
    f" color: {COLORS['text_primary']};"
    f" border: 2px solid {COLORS['accent_blue']};"
    f" border-radius: 12px;"
    f" font-size: 18px; font-weight: bold;"
    f" padding: 10px 16px;"
    f"}}"
)
_FAV_STYLE = (
    f"QPushButton {{"
    f" background-color: {COLORS['surface']};"
    f" color: {COLORS['accent_yellow']};"
    f" border: 2px solid {COLORS['accent_yellow']};"
    f" border-radius: 12px;"
    f" font-size: 22px; font-weight: bold;"
    f" padding: 10px; min-height: 80px;"
    f"}}"
)


class QuickPhrasesScreen(QWidget):
    go_home = pyqtSignal()
    screen_changed = pyqtSignal()

    def __init__(
        self,
        tts,
        store,
        profile_store=None,
        active_profile=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tts = tts
        self._store = store
        self._profile_store = profile_store
        self._active_profile = active_profile
        self._buttons: dict[str, GazeButton] = {}

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(30, 20, 30, 20)
        self._root_layout.setSpacing(16)

        self._title = QLabel("Frases Rápidas")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self._title.setFont(font)
        self._title.setStyleSheet(f"color: {COLORS['accent_blue']}; margin-bottom: 4px;")
        self._root_layout.addWidget(self._title)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(12)
        self._root_layout.addWidget(self._content, 1)

        self._show_level1()

    # ── Troca de nível ───────────────────────────────────────────────────

    def _clear_content(self) -> None:
        self._buttons.clear()
        self._root_layout.removeWidget(self._content)
        self._content.deleteLater()
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(12)
        self._root_layout.addWidget(self._content, 1)

    def _show_level1(self) -> None:
        self._clear_content()
        self._title.setText("Frases Rápidas")

        # Monta lista de categorias: Favoritas (se houver) + categorias regulares
        all_cats = []
        has_favorites = (
            self._active_profile is not None
            and bool(self._active_profile.favorite_phrases)
        )
        if has_favorites:
            all_cats.append({"id": _FAVORITES_ID, "nome": "Favoritas", "icone": "⭐"})
        all_cats.extend(self._store.get_categories())

        grid = QGridLayout()
        grid.setSpacing(12)

        for i, cat in enumerate(all_cats[:4]):
            row, col = divmod(i, 2)
            label = f"{cat['icone']}  {cat['nome']}"
            btn = self._make_button(cat["id"], label)
            cat_id = cat["id"]
            btn.activated.connect(lambda _, cid=cat_id: self._show_level2(cid))
            grid.addWidget(btn, row, col)

        self._content_layout.addLayout(grid)
        self._content_layout.addStretch()

        btn_home = self._make_button("home", "🏠  HOME")
        btn_home.activated.connect(lambda _: self.go_home.emit())
        self._content_layout.addWidget(btn_home)

        self.screen_changed.emit()

    def _show_level2(self, category_id: str) -> None:
        logger.info(f"[QuickPhrases] Categoria selecionada: {category_id}")

        if category_id == _FAVORITES_ID:
            phrases = list(self._active_profile.favorite_phrases) if self._active_profile else []
            cat_name, cat_icon = "Favoritas", "⭐"
            show_fav_btn = False
        else:
            categories = self._store.get_categories()
            cat_info = next((c for c in categories if c["id"] == category_id), None)
            cat_name = cat_info["nome"] if cat_info else category_id
            cat_icon = cat_info.get("icone", "") if cat_info else ""
            phrases = self._store.get_phrases(category_id)[:6]
            show_fav_btn = (
                self._active_profile is not None
                and self._profile_store is not None
            )

        self._clear_content()
        self._title.setText(f"{cat_icon}  {cat_name}")

        for i, phrase in enumerate(phrases):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            phrase_btn = self._make_button(f"phrase_{i}", phrase)
            phrase_btn._btn.setMinimumHeight(80)
            phrase_btn._btn.setStyleSheet(_PHRASE_STYLE)
            text = phrase
            phrase_btn.activated.connect(lambda _, t=text: self._speak_phrase(t))
            row_layout.addWidget(phrase_btn, 1)

            if show_fav_btn:
                fav_btn = self._make_button(f"fav_{i}", "⭐")
                fav_btn._btn.setMinimumHeight(80)
                fav_btn._btn.setFixedWidth(90)
                fav_btn._btn.setStyleSheet(_FAV_STYLE)
                fav_btn.activated.connect(lambda _, t=text: self._add_favorite(t))
                row_layout.addWidget(fav_btn)

            self._content_layout.addLayout(row_layout)

        self._content_layout.addStretch()

        actions = QHBoxLayout()
        actions.setSpacing(12)

        btn_back = self._make_button("voltar", "←  VOLTAR")
        btn_back.activated.connect(lambda _: self._show_level1())
        actions.addWidget(btn_back)

        btn_home = self._make_button("home", "🏠  HOME")
        btn_home.activated.connect(lambda _: self.go_home.emit())
        actions.addWidget(btn_home)

        self._content_layout.addLayout(actions)

        self.screen_changed.emit()

    def _speak_phrase(self, text: str) -> None:
        logger.info(f"[QuickPhrases] Falando: {text}")
        self._tts.speak(text)

    def _add_favorite(self, phrase: str) -> None:
        if not self._active_profile or not self._profile_store:
            return
        if phrase not in self._active_profile.favorite_phrases:
            self._active_profile.favorite_phrases.append(phrase)
            self._profile_store.update(self._active_profile)
            logger.info(f"[QuickPhrases] Frase favoritada: {phrase!r}")

    # ── Helpers ──────────────────────────────────────────────────────────

    def _make_button(self, region_id: str, label: str) -> GazeButton:
        btn = GazeButton(region_id=region_id, label=label, parent=self)
        self._buttons[region_id] = btn
        return btn

    # ── Interface para MainWindow ─────────────────────────────────────────

    def get_button(self, region_id: str) -> GazeButton | None:
        return self._buttons.get(region_id)

    def get_all_buttons(self) -> dict[str, GazeButton]:
        return self._buttons
