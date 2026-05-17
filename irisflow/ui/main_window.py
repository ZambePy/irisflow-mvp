"""
MainWindow — janela principal do IrisFlow.

Fluxo de inicialização baseado em perfis:
  - Nenhum perfil    → ProfileEditor (primeiro uso)
  - Um perfil        → aplica direto → calibração ou home
  - Múltiplos perfis → ProfileSelectScreen

F10 abre modo cuidador (ProfileEditor) em qualquer tela.
"""
from PyQt6.QtWidgets import QMainWindow, QStatusBar
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeyEvent

from irisflow.tracking.service import TrackingService
from irisflow.accessibility.dwell import DwellController
from irisflow.speech.tts import TTSEngine
from irisflow.profiles.profile_store import ProfileStore
from irisflow.profiles.profile import Profile
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger


class MainWindow(QMainWindow):
    def __init__(
        self,
        tracking: TrackingService,
        dwell: DwellController,
        tts: TTSEngine,
        profile_store: ProfileStore,
    ) -> None:
        super().__init__()
        self._tracking = tracking
        self._dwell = dwell
        self._tts = tts
        self._profile_store = profile_store
        self._active_profile: Profile | None = None

        self._setup_window()
        self._start_flow()

    # ── Setup ─────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("IrisFlow — Comunicação por Olhar")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        status = QStatusBar()
        status.setStyleSheet(
            f"background-color: {COLORS['surface']}; color: {COLORS['text_muted']};"
        )
        self.setStatusBar(status)
        self._update_status("Iniciando...")

    # ── Fluxo de inicialização ────────────────────────────────────────────

    def _start_flow(self) -> None:
        profiles = self._profile_store.get_all()

        if not profiles:
            self._show_profile_editor(profile=None)
            return

        if len(profiles) == 1:
            restarted = self._apply_profile(profiles[0])
            self._profile_store.set_last_used(profiles[0].id)
            if not restarted:
                self._continue_after_profile()
            return

        self._show_profile_select()

    def _continue_after_profile(self) -> None:
        if self._tracking.engine_name == "eyetrax":
            self._show_calibration()
        else:
            self._show_home()

    # ── Telas de perfil ───────────────────────────────────────────────────

    def _show_profile_select(self) -> None:
        from irisflow.ui.screens.profile_select import ProfileSelectScreen

        self._dwell.clear_regions()
        screen = ProfileSelectScreen(store=self._profile_store)
        self._current_screen = screen
        QTimer.singleShot(0, lambda: self.setCentralWidget(screen))

        screen.profile_selected.connect(self._on_profile_selected)
        screen.new_profile_requested.connect(lambda: self._show_profile_editor(profile=None))

        QTimer.singleShot(300, self._register_dwell_regions)
        logger.info("[MainWindow] ProfileSelectScreen exibida")

    def _on_profile_selected(self, profile_id: str) -> None:
        profile = self._profile_store.get(profile_id)
        if profile:
            if not self._apply_profile(profile):
                self._continue_after_profile()

    def _show_profile_editor(self, profile: Profile | None) -> None:
        from irisflow.ui.screens.profile_editor import ProfileEditorScreen

        self._dwell.clear_regions()
        screen = ProfileEditorScreen(store=self._profile_store, profile=profile)
        self._current_screen = screen
        QTimer.singleShot(0, lambda: self.setCentralWidget(screen))

        screen.saved.connect(self._on_profile_editor_saved)
        screen.cancelled.connect(self._on_profile_editor_cancelled)

        QTimer.singleShot(300, self._register_dwell_regions)
        logger.info("[MainWindow] ProfileEditorScreen exibida")

    def _on_profile_editor_saved(self) -> None:
        profiles = self._profile_store.get_all()

        if not profiles:
            self._active_profile = None
            self._show_profile_editor(profile=None)
            return

        # Verifica se perfil ativo ainda existe (pode ter sido excluído)
        active_exists = (
            self._active_profile is not None
            and self._profile_store.get(self._active_profile.id) is not None
        )

        if active_exists:
            # Cuidador editou o perfil ativo — re-aplica e volta ao home
            if not self._apply_profile(self._active_profile):
                self._show_home()
            return

        self._active_profile = None
        if len(profiles) == 1:
            restarted = self._apply_profile(profiles[0])
            self._profile_store.set_last_used(profiles[0].id)
            if not restarted:
                self._continue_after_profile()
        else:
            self._show_profile_select()

    def _on_profile_editor_cancelled(self) -> None:
        if self._active_profile:
            self._show_home()
        else:
            self._show_profile_select()

    def _apply_profile(self, profile: Profile) -> bool:
        from irisflow.core.config import config

        current_engine = self._tracking.engine_name
        self._active_profile = profile
        self._dwell._dwell_time = profile.dwell_time_ms / 1000.0
        config.tracking_engine = profile.tracking_engine
        logger.info(
            f"[MainWindow] Perfil ativo: {profile.name} "
            f"(dwell={profile.dwell_time_ms}ms, engine={profile.tracking_engine})"
        )

        if profile.tracking_engine != current_engine:
            self._restart_tracking(profile.tracking_engine)
            return True

        return False

    def _restart_tracking(self, engine_name: str) -> None:
        from irisflow.tracking.factory import create_engine

        self._tracking.stop()
        engine = create_engine(engine_name)
        self._tracking = TrackingService(engine)

        if hasattr(self, "_gaze_cursor"):
            self._gaze_cursor.hide()
            del self._gaze_cursor

        logger.info(f"[MainWindow] Engine trocado para: {engine_name}")

        if engine_name == "eyetrax":
            self._show_calibration()
        else:
            self._show_home()

    # ── Modo cuidador — F10 ───────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_F10:
            self._open_caregiver_mode()
        super().keyPressEvent(event)

    def _open_caregiver_mode(self) -> None:
        from irisflow.ui.screens.profile_select import ProfileSelectScreen

        current = getattr(self, "_current_screen", None)
        if isinstance(current, ProfileSelectScreen):
            self._show_profile_editor(profile=None)
        else:
            self._show_profile_editor(profile=self._active_profile)

        logger.info("[MainWindow] Modo cuidador aberto (F10)")

    # ── Calibração ────────────────────────────────────────────────────────

    def _show_calibration(self) -> None:
        from irisflow.ui.screens.calibration import CalibrationScreen
        from irisflow.integrations.eyetrax.adapter import EyeTraxAdapter

        adapter = self._tracking._engine
        if not isinstance(adapter, EyeTraxAdapter):
            self._show_home()
            return

        self._update_status("Aguardando calibração...")
        cal_screen = CalibrationScreen(adapter=adapter, parent=self)
        cal_screen.calibration_done.connect(self._on_calibration_done)
        self.setCentralWidget(cal_screen)

    def _on_calibration_done(self, success: bool) -> None:
        if success:
            self._show_home()
        else:
            self._update_status("Calibração falhou — tente novamente")

    # ── Home e navegação ──────────────────────────────────────────────────

    def _show_home(self) -> None:
        from irisflow.ui.components.gaze_cursor import GazeCursor
        from irisflow.ui.screens.home import HomeScreen

        self._dwell.clear_regions()
        home = HomeScreen(tts=self._tts)
        self._current_screen = home
        QTimer.singleShot(0, lambda: self.setCentralWidget(home))

        if not hasattr(self, "_gaze_cursor"):
            self._gaze_cursor = GazeCursor()
            self._connect_tracking()

        home.overlay_opened.connect(self._on_emergency_overlay_opened)
        home.overlay_closed.connect(self._on_emergency_overlay_closed)
        home.navigate_frases.connect(self.show_quick_phrases)
        home.navigate_teclado.connect(self.show_keyboard)

        QTimer.singleShot(300, self._register_dwell_regions)
        logger.info("[MainWindow] HomeScreen exibida")

    def show_quick_phrases(self) -> None:
        from irisflow.ui.screens.quick_phrases import QuickPhrasesScreen
        from irisflow.storage.phrases_store import PhrasesStore

        self._dwell.clear_regions()
        if not hasattr(self, "_phrases_store"):
            self._phrases_store = PhrasesStore()

        screen = QuickPhrasesScreen(
            tts=self._tts,
            store=self._phrases_store,
            profile_store=self._profile_store,
            active_profile=self._active_profile,
        )
        self._current_screen = screen
        QTimer.singleShot(0, lambda: self.setCentralWidget(screen))

        screen.go_home.connect(self._show_home)
        screen.screen_changed.connect(self._on_screen_changed)

        QTimer.singleShot(300, self._register_dwell_regions)
        logger.info("[MainWindow] QuickPhrasesScreen exibida")

    def show_keyboard(self) -> None:
        from irisflow.ui.screens.keyboard import KeyboardScreen

        self._dwell.clear_regions()
        screen = KeyboardScreen(tts=self._tts)
        self._current_screen = screen
        QTimer.singleShot(0, lambda: self.setCentralWidget(screen))

        screen.go_home.connect(self._show_home)

        QTimer.singleShot(300, self._register_dwell_regions)
        logger.info("[MainWindow] KeyboardScreen exibida")

    def _on_screen_changed(self) -> None:
        QTimer.singleShot(300, self._register_dwell_regions)

    # ── Tracking e Dwell ──────────────────────────────────────────────────

    def _connect_tracking(self) -> None:
        self._tracking.add_listener(self._dwell.on_gaze)
        self._tracking.add_listener(self._on_gaze_cursor)

        self._dwell.dwell_progress.connect(self._on_dwell_progress)
        self._dwell.dwell_completed.connect(self._on_dwell_completed)
        self._dwell.dwell_cancelled.connect(self._on_dwell_cancelled)

        self._tracking.start()
        engine = self._tracking.engine_name
        self._update_status(f"✓ Tracking ativo ({engine})")
        logger.info(f"[MainWindow] Tracking iniciado — engine: {engine}")

    def _on_dwell_progress(self, region_id: str, progress: float) -> None:
        screen = getattr(self, "_current_screen", None)
        if screen:
            btn = screen.get_button(region_id)
            if btn:
                btn.on_dwell_progress(progress)

    def _on_dwell_completed(self, region_id: str) -> None:
        self._dwell.reset()
        screen = getattr(self, "_current_screen", None)
        if screen:
            btn = screen.get_button(region_id)
            if btn:
                btn.on_dwell_completed()

    def _on_dwell_cancelled(self, region_id: str) -> None:
        screen = getattr(self, "_current_screen", None)
        if screen:
            btn = screen.get_button(region_id)
            if btn:
                btn.on_dwell_cancelled()

    def _on_gaze_cursor(self, point) -> None:
        if hasattr(self, "_gaze_cursor"):
            self._gaze_cursor.move_to(point.x, point.y)

    def _on_emergency_overlay_opened(self) -> None:
        self._dwell.clear_regions()
        logger.debug("[MainWindow] Overlay emergência aberto — regiões dwell suspensas")

    def _on_emergency_overlay_closed(self) -> None:
        QTimer.singleShot(100, self._register_dwell_regions)
        logger.debug("[MainWindow] Overlay emergência fechado — regiões dwell restauradas")

    def _register_dwell_regions(self) -> None:
        self._dwell.clear_regions()
        screen = getattr(self, "_current_screen", None)
        if screen is None:
            return
        buttons = screen.get_all_buttons()
        for region_id, btn in buttons.items():
            self._dwell.register_region(region_id, btn.global_rect())
        logger.debug(f"[MainWindow] {len(buttons)} regiões registradas")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_current_screen"):
            QTimer.singleShot(100, self._register_dwell_regions)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _update_status(self, text: str) -> None:
        self.statusBar().showMessage(f"  IrisFlow  |  {text}")

    def closeEvent(self, event) -> None:
        self._tracking.stop()
        if hasattr(self, "_gaze_cursor"):
            self._gaze_cursor.hide()
        logger.info("[MainWindow] Encerrado")
        super().closeEvent(event)
