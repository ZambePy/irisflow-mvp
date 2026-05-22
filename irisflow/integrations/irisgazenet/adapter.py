"""
IrisGazeNetAdapter — encapsula completamente o IrisGazeEstimator.

REGRA: nenhuma classe, tipo ou import de training/ pode vazar
       além deste arquivo. O IrisFlow só conhece GazePoint.

Fluxo de operação:
  1. load_model() → carrega IrisGazeEstimator do disco via sys.path lazy
  2. start() → inicia thread de captura
  3. Thread: cv2.VideoCapture → MediaPipe → crop olho esquerdo → transform → predict
  4. (x, y) → _apply_deadzone → GazePoint → _emit_gaze → DwellController
  5. stop() → sinaliza thread para encerrar → libera câmera
"""
from __future__ import annotations

import math
import threading
import time

from irisflow.tracking.base import BaseGazeEngine
from irisflow.tracking.types import GazePoint
from irisflow.core.logger import logger
from irisflow.integrations.irisgazenet.config import IrisGazeNetConfig, irisgazenet_config


class IrisGazeNetAdapter(BaseGazeEngine):
    """
    Adapter entre o IrisFlow e o IrisGazeEstimator.

    Implementa BaseGazeEngine — interface idêntica ao EyeTraxAdapter.
    O restante do IrisFlow (UI, DwellController) não conhece nenhum
    detalhe interno deste adapter.

    Uso:
        adapter = IrisGazeNetAdapter()
        adapter.load_model()     # carrega SVR calibrado do disco
        adapter.start()          # inicia loop de captura em background
        adapter.stop()           # encerra limpo
    """

    def __init__(self, config: IrisGazeNetConfig | None = None) -> None:
        super().__init__()
        self._config = config or irisgazenet_config
        self._running = False
        self._thread: threading.Thread | None = None
        self._estimator = None      # IrisGazeEstimator — carregado lazy
        self._model_ready = False

        # Estado da deadzone — mantido entre frames
        self._deadzone_x: float = 0.0
        self._deadzone_y: float = 0.0
        self._deadzone_frames: int = 0

    # ── Interface pública ─────────────────────────────────────────────────

    def start(self) -> None:
        """
        Inicia rastreamento em thread de background.
        Tenta carregar modelo automaticamente se ainda não pronto.
        """
        if self._running:
            logger.warning("[IrisGazeNetAdapter] já está rodando")
            return

        if not self._model_ready:
            self.load_model()

        if not self._model_ready:
            raise RuntimeError(
                "IrisGazeNetAdapter: modelo não carregado. "
                "Certifique-se de que model_path existe e é válido, "
                "ou chame calibrate() antes de start()."
            )

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="irisflow-irisgazenet-capture",
            daemon=True,
        )
        self._thread.start()
        logger.info("[IrisGazeNetAdapter] Rastreamento iniciado")

    def stop(self) -> None:
        """Para o loop de captura e libera recursos."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("[IrisGazeNetAdapter] Parado")

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "irisgazenet"

    @property
    def model_ready(self) -> bool:
        return self._model_ready

    # ── Carregamento de modelo ────────────────────────────────────────────

    def load_model(self, path: str | None = None) -> bool:
        """
        Carrega IrisGazeEstimator salvo do disco.

        Importa training/model.py via sys.path de forma lazy —
        training/ nunca é importado no topo deste arquivo.

        Args:
            path: caminho do arquivo .pkl; usa config.model_path se None.

        Returns:
            True se carregado com sucesso.
        """
        import sys
        from pathlib import Path

        training_path = Path(__file__).parent.parent.parent.parent / "training"
        if str(training_path) not in sys.path:
            sys.path.insert(0, str(training_path))

        model_path = path or self._config.model_path
        if not model_path or not Path(model_path).exists():
            logger.warning(f"[IrisGazeNetAdapter] Modelo não encontrado: {model_path}")
            return False

        try:
            from model import IrisGazeEstimator
            self._estimator = IrisGazeEstimator.load(str(model_path))
            self._model_ready = True
            logger.info(f"[IrisGazeNetAdapter] Modelo carregado: {model_path}")
            return True
        except Exception as e:
            logger.error(f"[IrisGazeNetAdapter] Erro ao carregar modelo: {e}")
            return False

    # ── Calibração ────────────────────────────────────────────────────────

    def calibrate(
        self,
        images_tensor: torch.Tensor,
        targets_np: np.ndarray,
        screen_w: int,
        screen_h: int,
    ) -> dict:
        """
        Calibra o estimador com dados do paciente.
        Chamado pela CalibrationScreen após coletar amostras.

        Args:
            images_tensor: tensor (N, 3, 224, 224) — frames de calibração
            targets_np:    array (N, 2) — coordenadas reais em pixels (x, y)
            screen_w:      largura da tela em pixels
            screen_h:      altura da tela em pixels

        Returns:
            dict com mae_x, mae_y, mae_total, n_samples, n_support_vectors_x/y
        """
        import sys
        from pathlib import Path

        training_path = Path(__file__).parent.parent.parent.parent / "training"
        if str(training_path) not in sys.path:
            sys.path.insert(0, str(training_path))

        if self._estimator is None:
            try:
                from model import IrisGazeEstimator
                self._estimator = IrisGazeEstimator()
            except Exception as e:
                raise RuntimeError(
                    f"IrisGazeNetAdapter: não foi possível criar IrisGazeEstimator: {e}"
                ) from e

        metrics = self._estimator.calibrate(
            images=images_tensor,
            targets=targets_np,
            screen_w=screen_w,
            screen_h=screen_h,
        )
        self._model_ready = True

        if self._config.model_path:
            try:
                self._estimator.save(self._config.model_path)
                logger.info(
                    f"[IrisGazeNetAdapter] Modelo salvo após calibração: "
                    f"{self._config.model_path}"
                )
            except Exception as e:
                logger.warning(
                    f"[IrisGazeNetAdapter] Não foi possível salvar modelo: {e}"
                )

        return metrics

    # ── Loop de captura ───────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        """Loop de captura — roda em thread daemon, nunca bloqueia a UI."""
        import cv2
        import torch
        import numpy as np
        import mediapipe as mp
        from torchvision import transforms

        cap = cv2.VideoCapture(self._config.camera_index)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            logger.error("[IrisGazeNetAdapter] Nenhuma câmera disponível")
            self._running = False
            return

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
        )

        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        interval = 1.0 / self._config.capture_fps

        logger.debug("[IrisGazeNetAdapter] Loop de captura iniciado")
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("[IrisGazeNetAdapter] Frame inválido")
                    time.sleep(interval)
                    continue

                # 1. Detectar face com MediaPipe
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                if not results.multi_face_landmarks:
                    time.sleep(interval)
                    continue

                # 2. Extrair crop do olho esquerdo via landmarks
                landmarks = results.multi_face_landmarks[0].landmark
                h, w = frame.shape[:2]
                # Landmarks do olho esquerdo: 33, 133, 160, 144, 158, 153
                eye_lm = [landmarks[i] for i in [33, 133, 160, 144, 158, 153]]
                xs = [int(lm.x * w) for lm in eye_lm]
                ys = [int(lm.y * h) for lm in eye_lm]
                x1 = max(0, min(xs) - 20)
                x2 = min(w, max(xs) + 20)
                y1 = max(0, min(ys) - 15)
                y2 = min(h, max(ys) + 15)
                if x2 <= x1 or y2 <= y1:
                    time.sleep(interval)
                    continue
                eye_crop = frame[y1:y2, x1:x2]

                # 3. Pré-processar e predizer
                try:
                    img_tensor = transform(eye_crop).unsqueeze(0)   # (1, 3, 224, 224)
                    x, y = self._estimator.predict(img_tensor)
                except Exception as e:
                    logger.debug(f"[IrisGazeNetAdapter] Erro predict: {e}")
                    time.sleep(interval)
                    continue

                # 4. Aplicar deadzone
                x, y = self._apply_deadzone(x, y)

                # 5. Emitir GazePoint
                self._emit_gaze(GazePoint(x=x, y=y, confidence=1.0))

                time.sleep(interval)

        except Exception as e:
            logger.error(f"[IrisGazeNetAdapter] Erro no loop: {e}")
        finally:
            cap.release()
            face_mesh.close()
            logger.debug("[IrisGazeNetAdapter] Câmera liberada")

    # ── Deadzone ──────────────────────────────────────────────────────────

    def _apply_deadzone(self, x: float, y: float) -> tuple[float, float]:
        """
        Suprime microtremores oculares involuntários.

        Trava o cursor enquanto o movimento for menor que deadzone_radius
        por menos de deadzone_frames frames consecutivos. Libera após
        fixação prolongada ou ao detectar movimento real.
        """
        dist = math.hypot(x - self._deadzone_x, y - self._deadzone_y)
        if dist < self._config.deadzone_radius:
            self._deadzone_frames += 1
            if self._deadzone_frames < self._config.deadzone_frames:
                return self._deadzone_x, self._deadzone_y
            # Fixação prolongada: libera o cursor na posição atual
            return x, y
        # Movimento real: reset e deixa passar
        self._deadzone_frames = 0
        self._deadzone_x = x
        self._deadzone_y = y
        return x, y
