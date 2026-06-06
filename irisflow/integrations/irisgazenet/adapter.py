"""
IrisGazeNetAdapter — encapsula completamente o IrisGazeEstimator.

REGRA: nenhuma classe, tipo ou import de training/ pode vazar
       além deste arquivo. O IrisFlow só conhece GazePoint.

Crop logic segue exatamente o MediaPipeFaceAlignment do GazeFollower:
  - Face: bounding box de todos os 478 landmarks, quadrado via delta
  - Olhos: landmarks 33/133 (esq) e 362/263 (dir) com padding proporcional
  - Openness: área Shoelace do polígono de abertura de cada olho
  - Blink: filtra frames onde qualquer olho tem openness <= 10
  - Filtro: HeuristicFilter(look_ahead=3) — sem Kalman/EMA
"""
from __future__ import annotations

import math
import sys
import threading
import time

import numpy as np

from irisflow.tracking.base import BaseGazeEngine
from irisflow.tracking.types import GazePoint
from irisflow.tracking.filter import HeuristicFilter
from irisflow.core.logger import logger
from irisflow.integrations.irisgazenet.config import IrisGazeNetConfig, irisgazenet_config

# Índices de landmarks para o polígono de abertura de cada olho (Shoelace)
_LEFT_OPEN_IDX  = [33, 246, 161, 160, 159, 158, 157, 173, 133,
                   155, 154, 153, 145, 144, 163, 7, 33]
_RIGHT_OPEN_IDX = [362, 388, 384, 385, 386, 387, 388, 466, 263,
                   249, 380, 373, 374, 380, 381, 382, 362]

_BLINK_THRESHOLD = 10.0


def _import_mediapipe():
    """Import MediaPipe while ignoring optional TensorFlow doc dependencies."""
    tensorflow_module = sys.modules.get("tensorflow")
    sys.modules["tensorflow"] = None
    try:
        import mediapipe as mp
        return mp
    finally:
        if tensorflow_module is None:
            sys.modules.pop("tensorflow", None)
        else:
            sys.modules["tensorflow"] = tensorflow_module


def _shoelace(xs: np.ndarray, ys: np.ndarray) -> float:
    """Área do polígono pelo método de Shoelace."""
    return 0.5 * abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1)))


def _eye_openness(landmarks, indices: list[int], w: int, h: int) -> float:
    xs = np.array([landmarks[i].x * w for i in indices], dtype=np.float32)
    ys = np.array([landmarks[i].y * h for i in indices], dtype=np.float32)
    return _shoelace(xs, ys)


def _face_rect(landmarks, w: int, h: int) -> tuple[int, int, int, int]:
    """Bounding box quadrado de todos os 478 landmarks do FaceMesh."""
    xs = [lm.x * w for lm in landmarks]
    ys = [lm.y * h for lm in landmarks]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    face_w = x_max - x_min
    face_h = y_max - y_min
    delta = (face_w - face_h) / 4
    if delta > 0:          # wider than tall — pad top/bottom
        y_min -= delta
        y_max += delta
    else:                  # taller than wide — pad left/right
        x_min += delta
        x_max -= delta
    x1 = max(0, int(x_min))
    y1 = max(0, int(y_min))
    x2 = min(w, int(x_max))
    y2 = min(h, int(y_max))
    return x1, y1, x2, y2


def _eye_rect(
    landmarks,
    lm_a: int,
    lm_b: int,
    scale: float,
    w: int,
    h: int,
    flip: bool = False,
) -> tuple[int, int, int, int, bool]:
    """
    Crop de um olho com padding proporcional ao GazeFollower.

    Returns (x1, y1, x2, y2, out_of_bounds).
    """
    x_padding = 20 * scale
    eye_xs = [landmarks[lm_a].x * w, landmarks[lm_b].x * w]
    eye_ys = [landmarks[lm_a].y * h, landmarks[lm_b].y * h]
    cx = (eye_xs[0] + eye_xs[1]) / 2
    cy = (eye_ys[0] + eye_ys[1]) / 2
    eye_height = abs(eye_xs[0] - eye_xs[1]) * 0.75
    x1 = cx - x_padding
    x2 = cx + x_padding
    y1 = cy - eye_height * 0.6
    y2 = cy + eye_height * 0.4
    oob = x1 < 0 or y1 < 0 or x2 > w or y2 > h
    x1 = max(0, int(x1));  y1 = max(0, int(y1))
    x2 = min(w, int(x2));  y2 = min(h, int(y2))
    return x1, y1, x2, y2, oob


class IrisGazeNetAdapter(BaseGazeEngine):
    """
    Adapter entre o IrisFlow e o IrisGazeEstimator v2 (multi-fonte).

    Implementa BaseGazeEngine — interface idêntica ao EyeTraxAdapter.
    O restante do IrisFlow (UI, DwellController) não conhece nenhum
    detalhe interno deste adapter.
    """

    def __init__(self, config: IrisGazeNetConfig | None = None) -> None:
        super().__init__()
        self._config = config or irisgazenet_config
        self._running = False
        self._thread: threading.Thread | None = None
        self._estimator = None
        self._model_ready = False
        self._status_message = "IrisGazeNet aguardando inicializacao"

        self._deadzone_x: float = 0.0
        self._deadzone_y: float = 0.0
        self._deadzone_frames: int = 0

        self._heuristic_filter = HeuristicFilter(look_ahead=3)
        self._last_valid_x: float = 0.0
        self._last_valid_y: float = 0.0

    # ── Interface pública ─────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            logger.warning("[IrisGazeNetAdapter] já está rodando")
            return
        if not self._model_ready:
            self.load_model()
        if not self._model_ready:
            raise RuntimeError(self._status_message)
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="irisflow-irisgazenet-capture",
            daemon=True,
        )
        self._thread.start()
        logger.info("[IrisGazeNetAdapter] Rastreamento iniciado")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("[IrisGazeNetAdapter] Parado")

    def is_running(self) -> bool:
        return self._running

    @property
    def engine_name(self) -> str:
        return "iris-gaze-net"

    @property
    def model_ready(self) -> bool:
        return self._model_ready

    @property
    def status_message(self) -> str:
        return self._status_message

    # ── Carregamento de modelo ────────────────────────────────────────────

    def load_model(self, path: str | None = None) -> bool:
        import sys
        from pathlib import Path

        training_path = Path(__file__).parent.parent.parent.parent / "training"
        if str(training_path) not in sys.path:
            sys.path.insert(0, str(training_path))

        model_path = path or self._config.model_path
        if not model_path or not Path(model_path).exists():
            self._status_message = (
                "IrisGazeNet requer calibracao: modelo nao encontrado. "
                "Execute a calibracao antes de iniciar este engine."
            )
            logger.warning(f"[IrisGazeNetAdapter] Modelo não encontrado: {model_path}")
            return False

        try:
            from model import IrisGazeEstimator
            self._estimator = IrisGazeEstimator.load(str(model_path))
            self._validate_loaded_model()
            self._model_ready = True
            self._status_message = "IrisGazeNet pronto"
            logger.info(f"[IrisGazeNetAdapter] Modelo carregado: {model_path}")
            return True
        except Exception as e:
            self._estimator = None
            self._model_ready = False
            self._status_message = f"IrisGazeNet nao pode iniciar: {e}"
            logger.error(f"[IrisGazeNetAdapter] Erro ao carregar modelo: {e}")
            return False

    def _validate_loaded_model(self) -> None:
        if self._estimator is None:
            raise RuntimeError("modelo nao foi carregado")

        if not getattr(self._estimator, "is_calibrated", False):
            raise RuntimeError(
                "modelo nao calibrado. Execute a calibracao antes de iniciar o IrisGazeNet."
            )

        missing = [
            name
            for name in ("scaler", "svr_x", "svr_y")
            if getattr(self._estimator, name, None) is None
        ]
        if missing:
            raise RuntimeError(
                "modelo incompleto: faltam " + ", ".join(missing) + ". Recalibre o IrisGazeNet."
            )

        spans = self._support_vector_prediction_spans()
        if spans is None:
            return

        span_x, span_y = spans
        logger.info(
            "[IrisGazeNetAdapter] Validacao do modelo: "
            f"span_x={span_x:.1f}px span_y={span_y:.1f}px"
        )
        if (
            span_x < self._config.min_prediction_span_px
            or span_y < self._config.min_prediction_span_px
        ):
            raise RuntimeError(
                "modelo calibrado nao varia coordenadas suficientes "
                f"(span_x={span_x:.1f}px, span_y={span_y:.1f}px). "
                "Recalibre o IrisGazeNet; este modelo produziria cursor estatico."
            )

        diagnostics = getattr(self._estimator, "training_diagnostics", {}) or {}
        validation_span = diagnostics.get("validation_prediction_span")
        if not validation_span:
            raise RuntimeError(
                "modelo legado sem validacao de calibracao salva. "
                "Recalibre o IrisGazeNet para gerar um modelo validado."
            )
        validation_span_x = float(validation_span.get("x", 0.0))
        validation_span_y = float(validation_span.get("y", 0.0))
        logger.info(
            "[IrisGazeNetAdapter] Validacao salva: "
            f"span_x={validation_span_x:.1f}px span_y={validation_span_y:.1f}px"
        )
        if (
            validation_span_x < self._config.min_prediction_span_px
            or validation_span_y < self._config.min_prediction_span_px
        ):
            raise RuntimeError(
                "modelo salvo falhou validacao de calibracao "
                f"(span_x={validation_span_x:.1f}px, span_y={validation_span_y:.1f}px). "
                "Recalibre o IrisGazeNet."
            )

    def _support_vector_prediction_spans(self) -> tuple[float, float] | None:
        try:
            svr_x = self._estimator.svr_x
            svr_y = self._estimator.svr_y
            support_vectors = getattr(svr_x, "support_vectors_", None)
            if support_vectors is None or len(support_vectors) == 0:
                return None
            pred_x = svr_x.predict(support_vectors)
            pred_y = svr_y.predict(support_vectors)
            return float(np.ptp(pred_x)), float(np.ptp(pred_y))
        except Exception as exc:
            logger.warning(f"[IrisGazeNetAdapter] Nao foi possivel validar variacao do modelo: {exc}")
            return None

    # ── Calibração ────────────────────────────────────────────────────────

    def calibrate(
        self,
        face_images,
        left_images,
        right_images,
        rects,
        targets_np,
        screen_w: int,
        screen_h: int,
    ) -> dict:
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
            face_images=face_images,
            left_images=left_images,
            right_images=right_images,
            rects=rects,
            targets=targets_np,
            screen_w=screen_w,
            screen_h=screen_h,
        )
        features = self._estimator.extractor.extract_numpy(
            face_images, left_images, right_images, rects
        )
        validation_preds = self._estimator.predict_from_features(features, clamp=True)
        diagnostics = {
            **metrics.get("diagnostics", {}),
            "validation_prediction_span": {
                "x": float(np.ptp(validation_preds[:, 0])),
                "y": float(np.ptp(validation_preds[:, 1])),
            },
            "accepted_min_prediction_span_px": self._config.min_prediction_span_px,
        }
        self._estimator.training_diagnostics = diagnostics
        self._validate_loaded_model()
        self._model_ready = True
        self._status_message = "IrisGazeNet calibrado e pronto"

        if self._config.model_path:
            try:
                self._estimator.save(self._config.model_path)
                logger.info(
                    f"[IrisGazeNetAdapter] Modelo salvo: {self._config.model_path}"
                )
            except Exception as e:
                logger.warning(f"[IrisGazeNetAdapter] Não foi possível salvar: {e}")

        return metrics

    # ── Loop de captura ───────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        if not self._model_ready:
            logger.error(f"[IrisGazeNetAdapter] Capture loop sem modelo pronto: {self._status_message}")
            self._running = False
            return

        import cv2
        import torch
        mp = _import_mediapipe()
        from torchvision import transforms

        # Tenta reusar o VideoCapture da calibração; se indisponível, abre próprio.
        own_cap = False
        try:
            from irisflow.api.routes.calibration import _get_cap as _cal_get_cap
            cap = _cal_get_cap()
            if cap is None or not cap.isOpened():
                cap = None
        except Exception:
            cap = None

        if cap is None:
            cap = cv2.VideoCapture(self._config.camera_index)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                logger.error("[IrisGazeNetAdapter] Nenhuma câmera disponível")
                self._running = False
                return
            own_cap = True

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
        )

        _norm = dict(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        transform_face = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(**_norm),
        ])
        transform_eye = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((112, 112)),
            transforms.ToTensor(),
            transforms.Normalize(**_norm),
        ])

        interval = 1.0 / self._config.capture_fps

        logger.info("[IrisGazeNetAdapter] Câmera aberta — rastreamento ativo")
        frame_count = 0
        face_count = 0
        predict_count = 0
        static_prediction_frames = 0
        last_raw: tuple[float, float] | None = None
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    logger.warning("[IrisGazeNetAdapter] Frame inválido")
                    time.sleep(interval)
                    continue
                frame_count += 1
                if frame_count == 1 or frame_count % 60 == 0:
                    logger.debug(f"[IrisGazeNetAdapter] Frame recebido #{frame_count}")

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                if not results.multi_face_landmarks:
                    self._emit_gaze(GazePoint(
                        x=self._last_valid_x, y=self._last_valid_y,
                        tracking_state="FACE_MISSING",
                    ))
                    time.sleep(interval)
                    continue
                face_count += 1
                if face_count == 1 or face_count % 60 == 0:
                    logger.debug(f"[IrisGazeNetAdapter] Face/olhos detectados #{face_count}")

                lm = results.multi_face_landmarks[0].landmark
                h, w = frame.shape[:2]

                left_open  = _eye_openness(lm, _LEFT_OPEN_IDX,  w, h)
                right_open = _eye_openness(lm, _RIGHT_OPEN_IDX, w, h)

                is_blink = left_open <= _BLINK_THRESHOLD or right_open <= _BLINK_THRESHOLD
                if is_blink:
                    self._emit_gaze(GazePoint(
                        x=self._last_valid_x, y=self._last_valid_y,
                        left_eye_openness=left_open,
                        right_eye_openness=right_open,
                        blink=True,
                        tracking_state="SUCCESS",
                    ))
                    time.sleep(interval)
                    continue

                fx1, fy1, fx2, fy2 = _face_rect(lm, w, h)
                if fx2 <= fx1 or fy2 <= fy1:
                    time.sleep(interval)
                    continue

                scale = abs(lm[362].x - lm[133].x) * w / 100.0

                lx1, ly1, lx2, ly2, l_oob = _eye_rect(lm, 33,  133, scale, w, h)
                rx1, ry1, rx2, ry2, r_oob = _eye_rect(lm, 362, 263, scale, w, h)

                tracking_state = "OUT_OF_BOUNDARIES" if (l_oob or r_oob) else "SUCCESS"

                if lx2 <= lx1 or ly2 <= ly1 or rx2 <= rx1 or ry2 <= ry1:
                    time.sleep(interval)
                    continue

                face_crop  = frame[fy1:fy2, fx1:fx2]
                left_crop  = frame[ly1:ly2, lx1:lx2]
                right_crop = cv2.flip(frame[ry1:ry2, rx1:rx2], 1)

                fw = fx2 - fx1;  fh = fy2 - fy1
                lw = lx2 - lx1;  lh = ly2 - ly1
                rw = rx2 - rx1;  rh = ry2 - ry1
                denom = np.array([w, h, w, h, w, h, w, h, w, h, w, h], dtype=np.float32)
                rect = np.array(
                    [fw, fh, fx1, fy1, lw, lh, lx1, ly1, rw, rh, rx1, ry1],
                    dtype=np.float32,
                ) / denom

                try:
                    face_t  = transform_face(face_crop).unsqueeze(0)
                    left_t  = transform_eye(left_crop).unsqueeze(0)
                    right_t = transform_eye(right_crop).unsqueeze(0)
                    raw_x, raw_y = self._estimator.predict(face_t, left_t, right_t, rect)
                except Exception as e:
                    logger.debug(f"[IrisGazeNetAdapter] Erro predict: {e}")
                    time.sleep(interval)
                    continue
                predict_count += 1
                if last_raw is not None and math.hypot(raw_x - last_raw[0], raw_y - last_raw[1]) < 0.01:
                    static_prediction_frames += 1
                else:
                    static_prediction_frames = 0
                last_raw = (raw_x, raw_y)

                if static_prediction_frames == 90:
                    self._status_message = (
                        "IrisGazeNet esta retornando predicoes estaticas; recalibre o modelo."
                    )
                    logger.warning(f"[IrisGazeNetAdapter] {self._status_message}")

                x, y = self._apply_deadzone(raw_x, raw_y)
                x, y = self._heuristic_filter.filter_values(x, y)

                self._last_valid_x = x
                self._last_valid_y = y

                self._emit_gaze(GazePoint(
                    x=x, y=y,
                    raw_x=raw_x, raw_y=raw_y,
                    confidence=1.0,
                    left_eye_openness=left_open,
                    right_eye_openness=right_open,
                    blink=False,
                    tracking_state=tracking_state,
                ))
                if predict_count == 1 or predict_count % 60 == 0:
                    logger.debug(
                        "[IrisGazeNetAdapter] Predicao/emissao "
                        f"#{predict_count}: raw=({raw_x:.1f},{raw_y:.1f}) "
                        f"filtrado=({x:.1f},{y:.1f}) state={tracking_state}"
                    )

                time.sleep(interval)

        except Exception as e:
            logger.error(f"[IrisGazeNetAdapter] Erro no loop: {e}")
        finally:
            if own_cap:
                cap.release()
            face_mesh.close()
            logger.debug("[IrisGazeNetAdapter] Câmera liberada")

    # ── Deadzone ──────────────────────────────────────────────────────────

    def _apply_deadzone(self, x: float, y: float) -> tuple[float, float]:
        dist = math.hypot(x - self._deadzone_x, y - self._deadzone_y)
        if dist < self._config.deadzone_radius:
            self._deadzone_frames += 1
            if self._deadzone_frames < self._config.deadzone_frames:
                return self._deadzone_x, self._deadzone_y
            return x, y
        self._deadzone_frames = 0
        self._deadzone_x = x
        self._deadzone_y = y
        return x, y
