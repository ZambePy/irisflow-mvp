"""
MainWindow — janela principal do IrisFlow.

Responsabilidades:
- Criar e exibir a tela inicial (HomeScreen)
- Conectar TrackingService → DwellController → GazeButtons
- Atualizar o status bar com estado do tracking
"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QStatusBar
from PyQt6.QtCore import Qt, QRect, QTimer

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
        self._setup_home_screen()
        self._connect_tracking()

        # Registrar regiões após a janela ser exibida
        QTimer.singleShot(300, self._register_dwell_regions)

    # ── Setup ─────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("IrisFlow — Comunicação por Olhar")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        status = QStatusBar()
        status.setStyleSheet(f"background-color: {COLORS['surface']}; color: {COLORS['text_muted']};")
        self.setStatusBar(status)
        self._update_status("Iniciando...")

    def _setup_home_screen(self) -> None:
        self._home = HomeScreen(tts=self._tts)
        self.setCentralWidget(self._home)

    def _connect_tracking(self) -> None:
        # GazePoint → DwellController
        self._tracking.add_listener(self._dwell.on_gaze)

        # DwellController → GazeButtons
        self._dwell.dwell_progress.connect(self._on_dwell_progress)
        self._dwell.dwell_completed.connect(self._on_dwell_completed)
        self._dwell.dwell_cancelled.connect(self._on_dwell_cancelled)

        # Iniciar tracking
        self._tracking.start()
        engine = self._tracking.engine_name
        self._update_status(f"✓ Tracking ativo ({engine})")
        logger.info(f"[MainWindow] Tracking iniciado com engine '{engine}'")

    # ── Dwell callbacks ───────────────────────────────────────────────────

    def _on_dwell_progress(self, region_id: str, progress: float) -> None:
        btn = self._home.get_button(region_id)
        if btn:
            btn.on_dwell_progress(progress)

    def _on_dwell_completed(self, region_id: str) -> None:
        btn = self._home.get_button(region_id)
        if btn:
            btn.on_dwell_completed()

    def _on_dwell_cancelled(self, region_id: str) -> None:
        btn = self._home.get_button(region_id)
        if btn:
            btn.on_dwell_cancelled()

    # ── Registro de regiões ───────────────────────────────────────────────

    def _register_dwell_regions(self) -> None:
        """Registra as regiões dos botões no DwellController."""
        self._dwell.clear_regions()
        for region_id, btn in self._home.get_all_buttons().items():
            rect = btn.global_rect()
            self._dwell.register_region(region_id, rect)
        logger.debug(f"[MainWindow] {len(self._home.get_all_buttons())} regiões registradas")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Re-registrar regiões quando a janela muda de tamanho
        QTimer.singleShot(100, self._register_dwell_regions)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _update_status(self, text: str) -> None:
        self.statusBar().showMessage(f"  IrisFlow  |  {text}")

    def closeEvent(self, event) -> None:
        self._tracking.stop()
        logger.info("[MainWindow] Encerrado")
        super().closeEvent(event)
