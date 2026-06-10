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
import queue
import sys
import threading
import time

try:
    import psutil
except ImportError:
    psutil = None

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


class PipelineMetrics:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.capture_frames = 0
        self.inference_frames = 0
        self.websocket_frames = 0
        self.dropped_frames = 0
        self.total_latency_ms = 0.0
        self.latency_count = 0
        
        self.last_fps_time = time.monotonic()
        self.fps_capture = 0.0
        self.fps_inference = 0.0
        self.fps_websocket = 0.0
        self.avg_latency_ms = 0.0

    def record_capture(self) -> None:
        with self.lock:
            self.capture_frames += 1

    def record_inference(self, latency_ms: float) -> None:
        with self.lock:
            self.inference_frames += 1
            self.total_latency_ms += latency_ms
            self.latency_count += 1

    def record_websocket(self) -> None:
        with self.lock:
            self.websocket_frames += 1

    def record_drop(self) -> None:
        with self.lock:
            self.dropped_frames += 1

    def update_fps(self) -> None:
        with self.lock:
            now = time.monotonic()
            dt = now - self.last_fps_time
            if dt >= 1.0:
                self.fps_capture = self.capture_frames / dt
                self.fps_inference = self.inference_frames / dt
                self.fps_websocket = self.websocket_frames / dt
                
                self.capture_frames = 0
                self.inference_frames = 0
                self.websocket_frames = 0
                self.last_fps_time = now
                
                if self.latency_count > 0:
                    self.avg_latency_ms = self.total_latency_ms / self.latency_count
                    self.total_latency_ms = 0.0
                    self.latency_count = 0


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
        self._capture_thread: threading.Thread | None = None
        self._inference_thread: threading.Thread | None = None
        self._frame_queue = queue.Queue(maxsize=1)
        self._state = "idle"  # "idle" | "starting" | "running" | "calibrating" | "stopping" | "error"
        self._metrics = PipelineMetrics()
        
        self._estimator = None
        self._model_ready = False
        self._status_message = "IrisGazeNet aguardando inicializacao"

        self._deadzone_x: float = 0.0
        self._deadzone_y: float = 0.0
        self._deadzone_frames: int = 0

        self._heuristic_filter = HeuristicFilter(look_ahead=3)
        self._last_valid_x: float = 0.0
        self._last_valid_y: float = 0.0
        self._smooth_x: float | None = None
        self._smooth_y: float | None = None

        # Estado da calibração
        self._cal_lock = threading.Lock()
        self._cal_active = False
        self._cal_point_index = -1
        self._cal_expected_x = 0.0
        self._cal_expected_y = 0.0
        self._cal_buffer: list[dict] = []
        self._cal_event = threading.Event()

    @property
    def state(self) -> str:
        return self._state

    @property
    def metrics(self) -> dict:
        self._metrics.update_fps()
        with self._metrics.lock:
            return {
                "fps_capture": round(self._metrics.fps_capture, 1),
                "fps_inference": round(self._metrics.fps_inference, 1),
                "fps_websocket": round(self._metrics.fps_websocket, 1),
                "queue_size": self._frame_queue.qsize(),
                "dropped_frames": self._metrics.dropped_frames,
                "avg_latency_ms": round(self._metrics.avg_latency_ms, 1),
                "cpu_usage": round(self.cpu_usage, 1),
            }

    @property
    def cpu_usage(self) -> float:
        if psutil is not None:
            try:
                return psutil.Process().cpu_percent(interval=None)
            except Exception:
                return 0.0
        return 0.0

    def start_collecting_point(self, point_index: int, expected_x: float, expected_y: float) -> None:
        with self._cal_lock:
            self._cal_point_index = point_index
            self._cal_expected_x = expected_x
            self._cal_expected_y = expected_y
            self._cal_buffer.clear()
            self._cal_event.clear()
            self._cal_active = True
            if self._state != "error":
                self._state = "calibrating"
        logger.info(f"[IrisGazeNetAdapter] Começando coleta para ponto {point_index} em ({expected_x}, {expected_y})")

    def wait_for_collection(self, timeout: float = 20.0) -> bool:
        return self._cal_event.wait(timeout=timeout)

    def get_collected_data(self) -> list[dict]:
        with self._cal_lock:
            return list(self._cal_buffer)

    def start_calibration_mode(self) -> None:
        if self._running:
            with self._cal_lock:
                self._cal_active = True
                self._state = "calibrating"
            return

        self._running = True
        self._state = "calibrating"
        self._frame_queue = queue.Queue(maxsize=1)
        
        self._capture_thread = threading.Thread(
            target=self._capture_run,
            name="irisflow-irisgazenet-capture",
            daemon=True
        )
        self._inference_thread = threading.Thread(
            target=self._inference_run,
            name="irisflow-irisgazenet-inference",
            daemon=True
        )
        
        self._capture_thread.start()
        self._inference_thread.start()
        logger.info("[IrisGazeNetAdapter] Started capture/inference threads for calibration")

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
        self._state = "starting"
        self._frame_queue = queue.Queue(maxsize=1)
        
        self._capture_thread = threading.Thread(
            target=self._capture_run,
            name="irisflow-irisgazenet-capture",
            daemon=True,
        )
        self._inference_thread = threading.Thread(
            target=self._inference_run,
            name="irisflow-irisgazenet-inference",
            daemon=True,
        )
        self._capture_thread.start()
        self._inference_thread.start()
        logger.info("[IrisGazeNetAdapter] Rastreamento iniciado")

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._cal_active = False
        self._state = "stopping"
        
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=2.0)
            
        self._capture_thread = None
        self._inference_thread = None
        self._state = "idle"
        logger.info("[IrisGazeNetAdapter] Parado")

    def is_running(self) -> bool:
        return self._running and self._state in ("running", "calibrating")

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

        prediction_mode = getattr(self._estimator, "prediction_mode", "svr")
        if prediction_mode == "calibration_knn":
            logger.info("[IrisGazeNetAdapter] Modelo legado com prediction_mode=calibration_knn aceito")
        else:
            if not hasattr(self._estimator, "pca_pre") or self._estimator.pca_pre is None:
                self._estimator.pca_pre = None

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

    # ── Loop de captura e inferência (Produtor-Consumidor) ──────────────────
 
    def _capture_run(self) -> None:
        import cv2
        logger.info("[IrisGazeNetAdapter] Capture thread started")
        
        cap = cv2.VideoCapture(self._config.camera_index)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            logger.error("[IrisGazeNetAdapter] Nenhuma câmera disponível")
            self._state = "error"
            self._status_message = "Erro: Câmera indisponível"
            self._running = False
            return

        self._state = "calibrating" if self._cal_active else "running"
        self._status_message = "IrisGazeNet pronto e rodando"

        try:
            while self._running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                self._metrics.record_capture()
                self._metrics.update_fps()

                capture_time = time.monotonic()
                item = (frame, capture_time)

                try:
                    self._frame_queue.put_nowait(item)
                except queue.Full:
                    try:
                        self._frame_queue.get_nowait()
                        self._metrics.record_drop()
                    except queue.Empty:
                        pass
                    self._frame_queue.put_nowait(item)
        except Exception as e:
            logger.error(f"[IrisGazeNetAdapter] Erro na captura: {e}")
            self._state = "error"
            self._status_message = f"Erro na câmera: {e}"
        finally:
            cap.release()
            logger.info("[IrisGazeNetAdapter] Capture thread stopped")

    def _inference_run(self) -> None:
        import cv2
        import torch
        from torchvision import transforms
        mp = _import_mediapipe()

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

        # Dimensões usadas na calibração — normaliza coordenadas para 0-1
        # para que o frontend as converta corretamente para viewport pixels.
        screen_w = float(getattr(self._estimator, "screen_w", 0) or self._config.screen_w)
        screen_h = float(getattr(self._estimator, "screen_h", 0) or self._config.screen_h)

        logger.info("[IrisGazeNetAdapter] Inference thread started")

        try:
            while self._running:
                try:
                    frame_data = self._frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                frame, capture_time = frame_data

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                if not results.multi_face_landmarks:
                    if self._state == "running":
                        self._emit_gaze(GazePoint(
                            x=self._last_valid_x / screen_w,
                            y=self._last_valid_y / screen_h,
                            tracking_state="FACE_MISSING",
                        ))
                    continue

                lm = results.multi_face_landmarks[0].landmark
                h, w = frame.shape[:2]

                left_open  = _eye_openness(lm, _LEFT_OPEN_IDX,  w, h)
                right_open = _eye_openness(lm, _RIGHT_OPEN_IDX, w, h)

                is_blink = left_open <= _BLINK_THRESHOLD or right_open <= _BLINK_THRESHOLD
                if is_blink:
                    if self._state == "running":
                        self._emit_gaze(GazePoint(
                            x=self._last_valid_x / screen_w,
                            y=self._last_valid_y / screen_h,
                            left_eye_openness=left_open,
                            right_eye_openness=right_open,
                            blink=True,
                            tracking_state="SUCCESS",
                        ))
                    continue

                fx1, fy1, fx2, fy2 = _face_rect(lm, w, h)
                if fx2 <= fx1 or fy2 <= fy1:
                    continue

                scale = abs(lm[362].x - lm[133].x) * w / 100.0

                lx1, ly1, lx2, ly2, l_oob = _eye_rect(lm, 33,  133, scale, w, h)
                rx1, ry1, rx2, ry2, r_oob = _eye_rect(lm, 362, 263, scale, w, h)

                tracking_state = "OUT_OF_BOUNDARIES" if (l_oob or r_oob) else "SUCCESS"

                if lx2 <= lx1 or ly2 <= ly1 or rx2 <= rx1 or ry2 <= ry1:
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

                # Coleta para calibração
                if self._cal_active:
                    with self._cal_lock:
                        self._cal_buffer.append({
                            "face_crop": transform_face(face_crop),
                            "left_crop": transform_eye(left_crop),
                            "right_crop": transform_eye(right_crop),
                            "rect": rect,
                            "target": [self._cal_expected_x, self._cal_expected_y],
                            "point_index": self._cal_point_index
                        })
                        if len(self._cal_buffer) >= 45:  # _N_FRAME_NEED
                            self._cal_active = False
                            self._cal_event.set()
                    
                    latency = (time.monotonic() - capture_time) * 1000.0
                    self._metrics.record_inference(latency)
                    continue

                # Predição normal (SVR)
                if self._state == "running" and self._model_ready:
                    try:
                        face_t  = transform_face(face_crop).unsqueeze(0)
                        left_t  = transform_eye(left_crop).unsqueeze(0)
                        right_t = transform_eye(right_crop).unsqueeze(0)
                        raw_x, raw_y = self._estimator.predict(face_t, left_t, right_t, rect)
                    except Exception as e:
                        logger.debug(f"[IrisGazeNetAdapter] Erro predict: {e}")
                        continue

                    x, y = self._apply_cursor_smoothing(raw_x, raw_y)
                    self._last_valid_x = x
                    self._last_valid_y = y

                    x_norm = max(0.0, min(1.0, x / screen_w))
                    y_norm = max(0.0, min(1.0, y / screen_h))

                    self._emit_gaze(GazePoint(
                        x=x_norm, y=y_norm,
                        raw_x=raw_x, raw_y=raw_y,
                        confidence=1.0,
                        left_eye_openness=left_open,
                        right_eye_openness=right_open,
                        blink=False,
                        tracking_state=tracking_state,
                    ))

                    latency = (time.monotonic() - capture_time) * 1000.0
                    self._metrics.record_inference(latency)

        except Exception as e:
            logger.error(f"[IrisGazeNetAdapter] Erro no loop de inferência: {e}")
        finally:
            face_mesh.close()
            logger.info("[IrisGazeNetAdapter] Inference thread stopped")

    # ── Deadzone ──────────────────────────────────────────────────────────

    def _apply_deadzone(self, x: float, y: float) -> tuple[float, float]:
        if self._config.deadzone_radius <= 0 or self._config.deadzone_frames <= 0:
            return x, y
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

    def _apply_cursor_smoothing(self, x: float, y: float) -> tuple[float, float]:
        if self._smooth_x is None or self._smooth_y is None:
            self._smooth_x = x
            self._smooth_y = y
            return x, y

        alpha = max(0.05, min(float(self._config.smoothing_alpha), 1.0))
        self._smooth_x = self._smooth_x + alpha * (x - self._smooth_x)
        self._smooth_y = self._smooth_y + alpha * (y - self._smooth_y)
        return self._smooth_x, self._smooth_y
