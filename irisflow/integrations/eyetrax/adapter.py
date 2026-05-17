"""
EyeTraxAdapter — encapsula completamente a biblioteca EyeTrax.

REGRA: nenhuma classe, tipo ou import do EyeTrax pode vazar
       além deste arquivo. O IrisFlow só conhece GazePoint.

Fluxo de operação:
  1. start() → inicia thread de captura
  2. Thread: cv2.VideoCapture → frame → estimator.extract_features()
  3. Se não blink e features válidas → estimator.predict() → (x, y)
  4. Converte (x, y) → GazePoint → _emit_gaze() → DwellController
  5. stop() → sinaliza thread para encerrar → libera câmera
"""
import threading
import time
from pathlib import Path

from irisflow.tracking.base import BaseGazeEngine
from irisflow.tracking.types import GazePoint
from irisflow.core.logger import logger
from irisflow.integrations.eyetrax.config import EyeTraxConfig, eyetrax_config


class EyeTraxAdapter(BaseGazeEngine):
    """
    Adapter entre o IrisFlow e a biblioteca EyeTrax (v0.4+).

    Uso:
        adapter = EyeTraxAdapter()
        adapter.calibrate()      # abre janela OpenCV de calibração
        adapter.start()          # inicia loop de captura em background
        adapter.stop()           # encerra limpo
    """

    def __init__(self, config: EyeTraxConfig | None = None) -> None:
        super().__init__()
        self._config = config or eyetrax_config
        self._running = False
        self._thread: threading.Thread | None = None
        self._estimator = None
        self._kalman = None
        self._model_ready = False

    # ── Interface pública ─────────────────────────────────────────────────

    def start(self) -> None:
        """
        Inicia rastreamento em thread de background.
        Requer modelo calibrado ou salvo em model_path.
        """
        if self._running:
            logger.warning("[EyeTraxAdapter] já está rodando")
            return

        self._init_estimator()

        if not self._model_ready:
            raise RuntimeError(
                "EyeTraxAdapter: modelo não calibrado. "
                "Chame calibrate() antes de start(), "
                "ou verifique se model_path existe."
            )

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="irisflow-eyetrax-capture",
            daemon=True,
        )
        self._thread.start()
        logger.info("[EyeTraxAdapter] Rastreamento iniciado")

    def stop(self) -> None:
        """Para o loop de captura e libera recursos."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._release_estimator()
        logger.info("[EyeTraxAdapter] Parado")

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "eyetrax"

    @property
    def model_ready(self) -> bool:
        return self._model_ready

    # ── Calibração ────────────────────────────────────────────────────────

    def calibrate(self) -> bool:
        """
        Executa calibração interativa (bloqueante — abre janela OpenCV).
        Chame ANTES de start(). Salva modelo em model_path se configurado.

        Returns:
            True se a calibração foi bem-sucedida.
        """
        from eyetrax import (
            GazeEstimator,
            run_9_point_calibration,
            run_5_point_calibration,
            run_lissajous_calibration,
        )

        logger.info(
            f"[EyeTraxAdapter] Calibração iniciada "
            f"(tipo={self._config.calibration_type}, "
            f"câmera={self._config.camera_index})"
        )

        self._estimator = GazeEstimator()

        cal_map = {
            "9p":        run_9_point_calibration,
            "5p":        run_5_point_calibration,
            "lissajous": run_lissajous_calibration,
        }
        if self._config.calibration_type == "dense":
            logger.warning("[EyeTraxAdapter] Dense calibration não disponível, usando 9p")
        cal_fn = cal_map.get(self._config.calibration_type, run_9_point_calibration)

        try:
            cal_fn(self._estimator, camera_index=self._config.camera_index)
        except Exception as e:
            logger.error(f"[EyeTraxAdapter] Erro na calibração: {e}")
            return False

        # Verify the model was actually trained by attempting a test prediction.
        # The attribute check `estimator.model.model is None` doesn't cover all
        # EyeTrax model types; a predict() call that raises means untrained.
        try:
            inner = getattr(self._estimator.model, "model", self._estimator.model)
            n_features = getattr(inner, "n_features_in_", 18)
            self._estimator.predict([[0] * n_features])
        except Exception:
            logger.error("[EyeTraxAdapter] Calibração incompleta — modelo não treinado")
            return False

        self._model_ready = True
        logger.info("[EyeTraxAdapter] Calibração concluída com sucesso")

        if self._config.model_path:
            self._save_model()

        self._init_filter()
        return True

    def load_model(self, path: str | None = None) -> bool:
        """
        Carrega modelo salvo — pula a calibração.

        Returns:
            True se carregado com sucesso.
        """
        from eyetrax import GazeEstimator

        model_path = path or self._config.model_path
        if not model_path or not Path(model_path).exists():
            logger.warning(f"[EyeTraxAdapter] Modelo não encontrado: {model_path}")
            return False

        try:
            self._estimator = GazeEstimator()
            self._estimator.load_model(model_path)
            self._model_ready = True
            self._init_filter()
            logger.info(f"[EyeTraxAdapter] Modelo carregado: {model_path}")
            return True
        except Exception as e:
            logger.error(f"[EyeTraxAdapter] Erro ao carregar modelo: {e}")
            return False

    # ── Loop de captura ───────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        """Loop de captura — roda em thread daemon, nunca bloqueia a UI."""
        import cv2

        cap = self._open_camera()
        if cap is None:
            self._running = False
            return

        interval = 1.0 / self._config.capture_fps
        last_frame_time = time.monotonic()

        logger.debug("[EyeTraxAdapter] Loop de captura iniciado")
        try:
            while self._running:
                # Throttle para o FPS alvo
                now = time.monotonic()
                wait = interval - (now - last_frame_time)
                if wait > 0:
                    time.sleep(wait)
                last_frame_time = time.monotonic()

                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("[EyeTraxAdapter] Frame inválido")
                    continue

                self._process_frame(frame)

        except Exception as e:
            logger.error(f"[EyeTraxAdapter] Erro no loop: {e}")
        finally:
            cap.release()
            logger.debug("[EyeTraxAdapter] Câmera liberada")

    def _process_frame(self, frame) -> None:
        """Extrai features, prediz gaze e emite GazePoint."""
        try:
            features, blink = self._estimator.extract_features(frame)

            if blink or features is None:
                return  # ignorar blinks e frames sem rosto

            coords = self._estimator.predict([features])[0]
            x, y = self._apply_filter(float(coords[0]), float(coords[1]))

            x, y = self._to_screen_pixels(x, y)

            self._emit_gaze(GazePoint(x=x, y=y, confidence=1.0))

        except Exception as e:
            logger.debug(f"[EyeTraxAdapter] Erro ao processar frame: {e}")

    # ── Filtro Kalman ────────────────────────────────────────────────────

    def _init_filter(self) -> None:
        if self._config.gaze_filter in ("kalman", "kalman_ema"):
            from eyetrax import make_kalman
            self._kalman = make_kalman()
            logger.debug("[EyeTraxAdapter] Filtro Kalman inicializado")

    def _apply_filter(self, x: float, y: float) -> tuple[float, float]:
        import numpy as np

        if self._kalman is None:
            return x, y

        self._kalman.predict()
        corrected = self._kalman.correct(np.array([[x], [y]], dtype=np.float32))
        kx, ky = float(corrected[0]), float(corrected[1])

        if self._config.gaze_filter == "kalman_ema":
            a = self._config.ema_alpha
            kx = a * x + (1 - a) * kx
            ky = a * y + (1 - a) * ky

        return kx, ky

    # ── Helpers ───────────────────────────────────────────────────────────

    def _screen_size(self) -> tuple[int, int]:
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            g = screen.geometry()
            return g.width(), g.height()
        return 1920, 1080

    def _to_screen_pixels(self, x: float, y: float) -> tuple[float, float]:
        """Converte para pixels de tela se o EyeTrax retornar valores normalizados (0–1)."""
        # Coordenadas normalizadas ficam em [0, 1]; pixels de tela excedem 1
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
            sw, sh = self._screen_size()
            logger.debug(f"[EyeTraxAdapter] coordenadas normalizadas detectadas — escalando para {sw}x{sh}")
            return x * sw, y * sh
        return x, y

    def _init_estimator(self) -> None:
        """Tenta carregar modelo automaticamente se ainda não pronto."""
        if self._model_ready:
            return
        if self._config.model_path:
            self.load_model()

    def _open_camera(self):
        import cv2
        for idx in [self._config.camera_index, 1, 0]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                if idx != self._config.camera_index:
                    logger.warning(f"[EyeTraxAdapter] Usando câmera {idx} como fallback")
                return cap
            cap.release()
        logger.error("[EyeTraxAdapter] Nenhuma câmera disponível")
        return None

    def _save_model(self) -> None:
        try:
            self._estimator.save_model(self._config.model_path)
            logger.info(f"[EyeTraxAdapter] Modelo salvo: {self._config.model_path}")
        except Exception as e:
            logger.warning(f"[EyeTraxAdapter] Não foi possível salvar modelo: {e}")

    def _release_estimator(self) -> None:
        if self._estimator:
            try:
                self._estimator.close()
            except Exception:
                pass
            self._estimator = None
        self._model_ready = False
