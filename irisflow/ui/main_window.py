"""
MainWindow — janela principal do IrisFlow.

Gerencia o fluxo de inicialização:
  - mock: abre HomeScreen diretamente
  - eyetrax: mostra CalibrationScreen primeiro, depois HomeScreen
"""
from PyQt6.QtWidgets import QMainWindow, QStatusBar
from PyQt6.QtCore import QTimer

from irisflow.tracking.service import TrackingService
from irisflow.accessibility.dwell import DwellController
from irisflow.speech.tts import TTSEngine
from irisflow.ui.screens.home import HomeScreen
from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger


class MainWindow(QMainWindow):
    def __init__(
        self,
        tracking: TrackingService,
        dwell: DwellController,
        tts: TTSEngine,
    ) -> None:
        super().__init__()
        self._tracking = tracking
        self._dwell = dwell
        self._tts = tts

        self._setup_window()
        self._start_flow()

    # ── Setup da janela ───────────────────────────────────────────────────

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
        """Decide se precisa calibrar ou vai direto para a Home."""
        engine_name = self._tracking.engine_name

        if engine_name == "mock":
            self._show_home()
            return

        if engine_name == "eyetrax":
            self._show_calibration()
            return

        # Fallback seguro
        self._show_home()

    def _show_calibration(self) -> None:
        """Mostra tela de calibração antes de iniciar tracking real."""
        from irisflow.ui.screens.calibration import CalibrationScreen
        from irisflow.integrations.eyetrax.adapter import EyeTraxAdapter

        # Obter o adapter diretamente do engine interno do tracking service
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

    def _show_home(self) -> None:
        """Exibe a tela principal e inicia o tracking."""
        from irisflow.ui.components.gaze_cursor import GazeCursor

        home = HomeScreen(tts=self._tts)
        self.setCentralWidget(home)
        self._home = home
        self._gaze_cursor = GazeCursor()

        home.overlay_opened.connect(self._on_emergency_overlay_opened)
        home.overlay_closed.connect(self._on_emergency_overlay_closed)

        self._connect_tracking()
        QTimer.singleShot(300, self._register_dwell_regions)

    # ── Tracking e Dwell ─────────────────────────────────────────────────

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
        btn = self._home.get_button(region_id)
        if btn:
            btn.on_dwell_progress(progress)

    def _on_dwell_completed(self, region_id: str) -> None:
        self._dwell.reset()
        btn = self._home.get_button(region_id)
        if btn:
            btn.on_dwell_completed()

    def _on_dwell_cancelled(self, region_id: str) -> None:
        btn = self._home.get_button(region_id)
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
        for region_id, btn in self._home.get_all_buttons().items():
            self._dwell.register_region(region_id, btn.global_rect())
        logger.debug(f"[MainWindow] {len(self._home.get_all_buttons())} regiões registradas")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_home"):
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
