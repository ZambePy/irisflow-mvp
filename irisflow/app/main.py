"""
IrisFlow — entrypoint principal.

Para rodar:
    python -m irisflow.app.main

O mouse simulará o olhar. Mantenha o cursor sobre um botão
por 1 segundo para ativar (dwell click).
"""
import sys
from PyQt6.QtWidgets import QApplication

from irisflow.app.bootstrap import bootstrap
from irisflow.ui.main_window import MainWindow
from irisflow.ui.theme import APP_STYLESHEET
from irisflow.core.logger import logger


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    app.setApplicationName("IrisFlow")
    app.setOrganizationName("IrisFlow")

    tracking, dwell, tts = bootstrap()

    window = MainWindow(tracking=tracking, dwell=dwell, tts=tts)
    window.show()

    logger.info("[Main] Janela aberta. Use o mouse para simular o olhar.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
