"""
CalibrationScreen — tela de calibração do IrisFlow para EyeTrax.

Fluxo:
  1. Explica o que vai acontecer
  2. Botão "Iniciar Calibração" → esconde janela Qt, chama adapter.calibrate()
     diretamente na thread principal (cv2.imshow exige main thread)
  3. EyeTrax abre janela OpenCV própria (bloqueante)
  4. Ao concluir, reexibe janela Qt e emite calibration_done → MainWindow
"""
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from irisflow.ui.theme import COLORS
from irisflow.core.logger import logger


class CalibrationScreen(QWidget):
    """
    Tela de calibração — aparece quando engine='eyetrax' e
    não há modelo salvo.
    """

    calibration_done = pyqtSignal(bool)   # True = pode iniciar tracking

    def __init__(self, adapter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._adapter = adapter
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        title = QLabel("Calibração do Olhar")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(22)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet(f"color: {COLORS['accent_blue']};")
        layout.addWidget(title)

        # Instruções
        instructions = QLabel(
            "A calibração coleta amostras do seu olhar em 9 pontos da tela.\n\n"
            "• Sente-se confortavelmente em frente à webcam\n"
            "• Mantenha a cabeça razoavelmente estável\n"
            "• Olhe para cada ponto verde que aparecer\n"
            "• O processo leva cerca de 30 segundos\n\n"
            "Uma janela separada será aberta para a calibração."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: 16px; line-height: 1.6;"
        )
        layout.addWidget(instructions)

        # Botão iniciar
        self._btn_start = QPushButton("▶  Iniciar Calibração")
        self._btn_start.setMinimumHeight(80)
        self._btn_start.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {COLORS['surface']};"
            f"  border: 2px solid {COLORS['accent_green']};"
            f"  color: {COLORS['accent_green']};"
            f"  font-size: 20px; font-weight: bold;"
            f"  border-radius: 12px;"
            f"}}"
        )
        self._btn_start.clicked.connect(self._start_calibration)
        layout.addWidget(self._btn_start)

        # Status / progresso
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        layout.addWidget(self._status_label)

        # Botão pular (só se houver modelo salvo)
        self._btn_skip = QPushButton("Usar calibração anterior")
        self._btn_skip.setMinimumHeight(50)
        self._btn_skip.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  border: 1px solid {COLORS['text_muted']};"
            f"  color: {COLORS['text_muted']};"
            f"  font-size: 14px; border-radius: 8px;"
            f"}}"
        )
        self._btn_skip.clicked.connect(self._try_load_model)
        self._btn_skip.setVisible(self._adapter._config.model_path is not None)
        layout.addWidget(self._btn_skip)

    # ── Ações ─────────────────────────────────────────────────────────────

    def _start_calibration(self) -> None:
        self._btn_start.setEnabled(False)
        self._btn_skip.setEnabled(False)
        self._status_label.setText("Preparando calibração...")
        # Flush UI updates before hiding so the button state is rendered
        QApplication.processEvents()

        win = self.window()
        win.hide()

        try:
            success = self._adapter.calibrate()
        except Exception as e:
            logger.error(f"[CalibrationScreen] Erro inesperado na calibração: {e}")
            success = False
        finally:
            win.show()
            win.raise_()
            win.activateWindow()
            QApplication.processEvents()

        self._on_calibration_finished(success)

    def _on_calibration_finished(self, success: bool) -> None:
        if success:
            self._status_label.setText("✓ Calibração concluída!")
            self._status_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px;")
            logger.info("[CalibrationScreen] Calibração concluída — emitindo sinal")
        else:
            self._status_label.setText("✗ Calibração falhou. Tente novamente.")
            self._status_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 14px;")
            self._btn_start.setEnabled(True)
            self._btn_skip.setEnabled(True)

        self.calibration_done.emit(success)

    def _try_load_model(self) -> None:
        success = self._adapter.load_model()
        if success:
            self._status_label.setText("✓ Modelo anterior carregado!")
            self._status_label.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px;")
        else:
            self._status_label.setText("Nenhum modelo salvo encontrado. Faça a calibração.")
            self._status_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 14px;")

        self.calibration_done.emit(success)
