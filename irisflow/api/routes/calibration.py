"""Rotas REST para controle de calibração do engine de rastreamento.

Pipeline segue exatamente o CalibrationController do GazeFollower:
  - _prepare_time     = 1.5 s  (espera antes de coletar)
  - _n_frame_need     = 45     (frames por ponto)
  - _wait_time        = 0.5 s  (espera após completar o ponto)
  - _blink_threshold  = 10     (openness mínima para aceitar frame)
  - _drop_last_three  = True   (descarta os 3 últimos frames de cada ponto no fit)
"""

import sys
import threading
import time
from pathlib import Path

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
from irisflow.profiles.profile_store import ProfileStore
from irisflow.core.logger import logger
from irisflow.tracking.filter import HeuristicFilter

router = APIRouter()
_collect_lock = threading.Lock()

# ── Câmera persistente ────────────────────────────────────────────────────────
# Abre uma vez no primeiro uso e mantém aberta durante toda a sessão do processo.
# Evita o LED piscando entre pontos e garante que a câmera já esteja quente
# quando o usuário chega na tela de calibração.

_cap = None          # cv2.VideoCapture singleton
_cap_lock = threading.Lock()


def _get_cap():
    """Retorna o VideoCapture global, abrindo se necessário."""
    global _cap
    with _cap_lock:
        try:
            import cv2
        except ImportError:
            return None
        if _cap is None or not _cap.isOpened():
            _cap = cv2.VideoCapture(0)
            if not _cap.isOpened():
                _cap.release()
                _cap = cv2.VideoCapture(1)
            if not _cap.isOpened():
                _cap = None
        return _cap


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


# ── Constantes (idênticas ao GazeFollower) ────────────────────────────────────

_PREPARE_TIME       = 0.0   # prepare gerenciado pelo frontend (1.5 s antes de chamar este endpoint)
_N_FRAME_NEED       = 45    # frames por ponto de calibração
_WAIT_TIME          = 0.5   # segundos de espera após completar o ponto
_BLINK_THRESHOLD    = 10.0  # openness mínima (área Shoelace) para aceitar frame

# Polígono de abertura de cada olho para cálculo Shoelace
_LEFT_OPEN_IDX  = [33, 246, 161, 160, 159, 158, 157, 173, 133,
                   155, 154, 153, 145, 144, 163, 7, 33]
_RIGHT_OPEN_IDX = [362, 388, 384, 385, 386, 387, 388, 466, 263,
                   249, 380, 373, 374, 380, 381, 382, 362]

# ── Estado da sessão de calibração ────────────────────────────────────────────

_cal_session: dict = {
    "face_images":  [],   # list[torch.Tensor (3,224,224)]
    "left_images":  [],   # list[torch.Tensor (3,112,112)]
    "right_images": [],   # list[torch.Tensor (3,112,112)]
    "rects":        [],   # list[np.ndarray (12,)]
    "targets":      [],   # list[[x_px, y_px]]
    "point_ids":    [],   # list[int] — point_index de cada frame coletado
    "metrics":      None,
    "status":       "idle",
}


def _reset_session() -> None:
    _cal_session["face_images"]  = []
    _cal_session["left_images"]  = []
    _cal_session["right_images"] = []
    _cal_session["rects"]        = []
    _cal_session["targets"]      = []
    _cal_session["point_ids"]    = []
    _cal_session["metrics"]      = None
    _cal_session["status"]       = "idle"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _shoelace(xs: np.ndarray, ys: np.ndarray) -> float:
    return 0.5 * abs(np.dot(xs, np.roll(ys, 1)) - np.dot(ys, np.roll(xs, 1)))


def _eye_openness(lm, indices: list[int], w: int, h: int) -> float:
    xs = np.array([lm[i].x * w for i in indices], dtype=np.float32)
    ys = np.array([lm[i].y * h for i in indices], dtype=np.float32)
    return _shoelace(xs, ys)


def _face_rect_478(lm, w: int, h: int) -> tuple[int, int, int, int]:
    """Bounding box quadrado de todos os 478 landmarks."""
    xs = [landmark.x * w for landmark in lm]
    ys = [landmark.y * h for landmark in lm]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    face_w = x_max - x_min
    face_h = y_max - y_min
    delta = (face_w - face_h) / 4
    if delta > 0:
        y_min -= delta
        y_max += delta
    else:
        x_min += delta
        x_max -= delta
    return (
        max(0, int(x_min)), max(0, int(y_min)),
        min(w, int(x_max)), min(h, int(y_max)),
    )


def _eye_rect(lm, lm_a: int, lm_b: int, scale: float,
              w: int, h: int) -> tuple[int, int, int, int]:
    x_padding = 20 * scale
    eye_xs = [lm[lm_a].x * w, lm[lm_b].x * w]
    eye_ys = [lm[lm_a].y * h, lm[lm_b].y * h]
    cx = (eye_xs[0] + eye_xs[1]) / 2
    cy = (eye_ys[0] + eye_ys[1]) / 2
    eye_height = abs(eye_xs[0] - eye_xs[1]) * 0.75
    x1 = max(0, int(cx - x_padding))
    x2 = min(w, int(cx + x_padding))
    y1 = max(0, int(cy - eye_height * 0.6))
    y2 = min(h, int(cy + eye_height * 0.4))
    return x1, y1, x2, y2


def _drop_last_three_frames(
    point_ids: list[int],
    face_images: list,
    left_images: list,
    right_images: list,
    rects: list,
    targets: list,
) -> tuple[list, list, list, list, list]:
    """Descarta os 3 últimos frames de cada ponto — igual ao GazeFollower."""
    ids = np.array(point_ids)
    mask = np.ones(len(ids), dtype=bool)
    for uid in np.unique(ids):
        indices = np.where(ids == uid)[0]
        if len(indices) > 3:
            mask[indices[-3:]] = False
        else:
            mask[indices] = False  # descarta tudo se ≤ 3 frames

    keep = np.where(mask)[0]
    return (
        [face_images[i]  for i in keep],
        [left_images[i]  for i in keep],
        [right_images[i] for i in keep],
        [rects[i]        for i in keep],
        [targets[i]      for i in keep],
    )


# ── Modelos de request ────────────────────────────────────────────────────────

class CollectPointBody(BaseModel):
    point_index: int
    expected_x: float
    expected_y: float


class FitCalibrationBody(BaseModel):
    profile_id: str | None = None
    screen_w: int | None = None
    screen_h: int | None = None


def _smooth_preview(points: np.ndarray, limit: int = 5) -> list[list[float]]:
    filt = HeuristicFilter(look_ahead=3)
    smoothed = []
    for x, y in points:
        sx, sy = filt.filter_values(float(x), float(y))
        smoothed.append([float(sx), float(sy)])
        if len(smoothed) >= limit:
            break
    return smoothed


def _log_calibration_diagnostics(diagnostics: dict) -> None:
    logger.info("[IrisGazeNetCalibration] samples=%s", diagnostics.get("n_samples"))
    logger.info(
        "[IrisGazeNetCalibration] unique_target_points=%s",
        diagnostics.get("unique_target_points"),
    )
    logger.info("[IrisGazeNetCalibration] screen_x=%s", diagnostics.get("screen_x"))
    logger.info("[IrisGazeNetCalibration] screen_y=%s", diagnostics.get("screen_y"))
    logger.info("[IrisGazeNetCalibration] features=%s", diagnostics.get("features"))
    logger.info(
        "[IrisGazeNetCalibration] features_scaled=%s",
        diagnostics.get("features_scaled"),
    )
    logger.info(
        "[IrisGazeNetCalibration] first_5_labels=%s",
        diagnostics.get("first_5_labels"),
    )
    logger.info(
        "[IrisGazeNetCalibration] first_5_predictions_before_smoothing=%s",
        diagnostics.get("first_5_predictions_before_smoothing"),
    )
    logger.info(
        "[IrisGazeNetCalibration] first_5_predictions_after_smoothing=%s",
        diagnostics.get("first_5_predictions_after_smoothing"),
    )


@router.post("/open_camera")
async def open_camera() -> dict:
    """Pré-aquece a câmera sem iniciar uma sessão de calibração."""
    try:
        from irisflow.api.main import tracking, _start_tracking_engine
        if tracking:
            if tracking.engine_name != "iris-gaze-net":
                await _start_tracking_engine("irisgazenet")
            tracking.start_calibration_mode()
            return {"ok": True, "camera": 0}
    except Exception as e:
        logger.warning(f"[CalibrationRoute] Falha ao pré-aquecer câmera: {e}")
    return {"ok": False, "camera": None}


@router.post("/new_session")
async def new_session() -> dict:
    """Reseta o estado completo da sessão de calibração."""
    _reset_session()
    try:
        from irisflow.api.main import tracking, _start_tracking_engine
        if tracking:
            if tracking.engine_name != "iris-gaze-net":
                await _start_tracking_engine("irisgazenet")
            tracking.start_calibration_mode()
    except Exception as e:
        logger.error(f"[CalibrationRoute] Erro ao iniciar modo calibração: {e}")
    return {"ok": True}


@router.post("/collect_point")
async def collect_point(req: CollectPointBody) -> dict:
    """
    Coleta _N_FRAME_NEED frames válidos para um ponto de calibração.
    Delega a coleta ao TrackingService em segundo plano.
    """
    import asyncio
    if not _collect_lock.acquire(blocking=False):
        return {"error": "Coleta já em andamento"}

    try:
        from irisflow.api.main import tracking
        if not tracking or tracking.engine_name != "iris-gaze-net":
            return {"error": "Engine IrisGazeNet não ativo"}

        # Inicia a coleta no background
        tracking.start_collecting_point(req.point_index, req.expected_x, req.expected_y)
        
        # Aguarda a coleta finalizar sem bloquear o event loop
        success = await asyncio.to_thread(tracking.wait_for_collection, 20.0)
        if not success:
            return {"error": "Timeout coletando frames. Verifique o enquadramento do rosto."}
            
        # Coleta os frames salvos
        collected_data = tracking.get_collected_data()
        
        for item in collected_data:
            _cal_session["face_images"].append(item["face_crop"])
            _cal_session["left_images"].append(item["left_crop"])
            _cal_session["right_images"].append(item["right_crop"])
            _cal_session["rects"].append(item["rect"])
            _cal_session["targets"].append(item["target"])
            _cal_session["point_ids"].append(item["point_index"])
            
        return {
            "point_index": req.point_index,
            "collected": len(collected_data),
            "needed": _N_FRAME_NEED,
            "ready": len(collected_data) >= _N_FRAME_NEED,
        }
    finally:
        _collect_lock.release()


@router.post("/fit")
def fit_calibration(body: FitCalibrationBody | None = None) -> dict:
    """
    Treina SVR com os frames coletados, descartando os 3 últimos de cada ponto.
    """
    if not _cal_session["targets"]:
        return {"error": "Nenhum dado coletado. Use POST /calibration/collect_point primeiro."}

    try:
        import torch
    except ImportError as exc:
        return {"error": f"Dependência ausente: {exc}"}

    training_path = Path(__file__).parent.parent.parent.parent / "training"
    if str(training_path) not in sys.path:
        sys.path.insert(0, str(training_path))

    try:
        from model import IrisGazeEstimator
    except ImportError as exc:
        return {"error": f"Não foi possível importar IrisGazeEstimator: {exc}"}

    try:
        # Drop dos 3 últimos frames de cada ponto
        fi, li, ri, rects_l, tgts_l = _drop_last_three_frames(
            _cal_session["point_ids"],
            _cal_session["face_images"],
            _cal_session["left_images"],
            _cal_session["right_images"],
            _cal_session["rects"],
            _cal_session["targets"],
        )

        if not tgts_l:
            return {"error": "Frames insuficientes após drop dos últimos 3 por ponto."}

        face_images  = torch.stack(fi)
        left_images  = torch.stack(li)
        right_images = torch.stack(ri)
        rects        = np.array(rects_l, dtype=np.float32)
        targets      = np.array(tgts_l,  dtype=np.float32)
    except Exception as exc:
        return {"error": f"Erro ao montar tensors: {exc}"}

    from irisflow.integrations.irisgazenet.config import irisgazenet_config

    screen_w = body.screen_w if body and body.screen_w else irisgazenet_config.screen_w
    screen_h = body.screen_h if body and body.screen_h else irisgazenet_config.screen_h

    try:
        estimator = IrisGazeEstimator()
        metrics = estimator.calibrate(
            face_images, left_images, right_images, rects, targets,
            screen_w=screen_w,
            screen_h=screen_h,
            prediction_mode="svr",
            svr_C=1.0,
            svr_kernel="rbf",
            svr_epsilon=0.05,
        )

        features = estimator.extractor.extract_numpy(
            face_images, left_images, right_images, rects
        )
        validation_preds = estimator.predict_from_features(features, clamp=True)
        validation_span_x = float(np.ptp(validation_preds[:, 0]))
        validation_span_y = float(np.ptp(validation_preds[:, 1]))
        diagnostics = {
            **metrics.get("diagnostics", {}),
            "first_5_predictions_after_smoothing": _smooth_preview(validation_preds),
            "validation_prediction_span": {
                "x": validation_span_x,
                "y": validation_span_y,
            },
            "accepted_min_prediction_span_px": irisgazenet_config.min_prediction_span_px,
        }
        estimator.training_diagnostics = diagnostics
        metrics["diagnostics"] = diagnostics
        metrics["validation_prediction_span_x"] = validation_span_x
        metrics["validation_prediction_span_y"] = validation_span_y
        _log_calibration_diagnostics(diagnostics)

        min_span = irisgazenet_config.min_prediction_span_px
        target_span_x = float(np.ptp(targets[:, 0]))
        target_span_y = float(np.ptp(targets[:, 1]))
        if target_span_x < min_span or target_span_y < min_span:
            return {
                "error": (
                    "Calibracao invalida: os pontos alvo nao variam o suficiente "
                    f"(target_span_x={target_span_x:.1f}px, target_span_y={target_span_y:.1f}px)."
                ),
                "diagnostics": diagnostics,
            }
        if validation_span_x < min_span or validation_span_y < min_span:
            return {
                "error": (
                    "Calibracao gerou modelo estatico em entradas de calibracao "
                    f"(span_x={validation_span_x:.1f}px, span_y={validation_span_y:.1f}px). "
                    "Refaca a calibracao olhando para todos os pontos."
                ),
                "diagnostics": diagnostics,
            }

        model_path = irisgazenet_config.model_path
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        estimator.save(model_path)
    except Exception as exc:
        return {"error": f"Erro ao treinar/salvar calibração: {exc}"}

    _cal_session["metrics"] = {
        **metrics,
        "model_path": str(model_path),
        "screen_w": screen_w,
        "screen_h": screen_h,
        "diagnostics": metrics.get("diagnostics"),
    }
    _cal_session["status"]  = "calibrated"

    accuracy = round(max(0.0, 1.0 - metrics["mae_total"] / 200.0), 3)

    if body and body.profile_id:
        ProfileStore().mark_calibrated(
            profile_id=body.profile_id,
            model_path=str(model_path),
            metrics={
                **metrics,
                "accuracy": accuracy,
                "screen_w": screen_w,
                "screen_h": screen_h,
            },
        )

    # Stop calibration mode in TrackingService
    try:
        from irisflow.api.main import tracking
        if tracking:
            tracking.stop()
    except Exception as e:
        logger.error(f"[CalibrationRoute] Erro ao parar calibração: {e}")

    return {
        "mae_x":     round(metrics["mae_x"], 1),
        "mae_y":     round(metrics["mae_y"], 1),
        "mae_total": round(metrics["mae_total"], 1),
        "n_samples": metrics["n_samples"],
        "model_path": str(model_path),
        "screen_w": screen_w,
        "screen_h": screen_h,
        "prediction_span_x": round(metrics["prediction_span_x"], 1),
        "prediction_span_y": round(metrics["prediction_span_y"], 1),
        "validation_prediction_span_x": round(metrics["validation_prediction_span_x"], 1),
        "validation_prediction_span_y": round(metrics["validation_prediction_span_y"], 1),
        "svr_kernel": metrics["svr_kernel"],
        "diagnostics": metrics.get("diagnostics"),
        "accuracy":  accuracy,
        "status":    "calibrated",
    }


@router.get("/result")
def calibration_result() -> dict:
    """Retorna métricas da última calibração executada via /fit."""
    if _cal_session["metrics"] is None:
        profile = ProfileStore().get_last_used()
        if profile and profile.is_calibrated and profile.calibration_model_path:
            model_path = Path(profile.calibration_model_path)
            if model_path.exists():
                metrics = profile.calibration_metrics or {}
                return {
                    "status": "calibrated",
                    "accuracy": metrics.get("accuracy"),
                    "mae_x": round(metrics["mae_x"], 1) if "mae_x" in metrics else None,
                    "mae_y": round(metrics["mae_y"], 1) if "mae_y" in metrics else None,
                    "mae_total": round(metrics["mae_total"], 1) if "mae_total" in metrics else None,
                    "n_samples": metrics.get("n_samples"),
                    "model_path": str(model_path),
                    "screen_w": metrics.get("screen_w"),
                    "screen_h": metrics.get("screen_h"),
                    "calibrated_at": profile.calibrated_at,
                    "profile_id": profile.id,
                }
        return {"status": "not_calibrated"}

    m = _cal_session["metrics"]
    accuracy = round(max(0.0, 1.0 - m["mae_total"] / 200.0), 3)
    return {
        "status":    _cal_session["status"],
        "accuracy":  accuracy,
        "mae_x":     round(m["mae_x"], 1),
        "mae_y":     round(m["mae_y"], 1),
        "mae_total": round(m["mae_total"], 1),
        "n_samples": m["n_samples"],
        "model_path": m.get("model_path"),
        "screen_w": m.get("screen_w"),
        "screen_h": m.get("screen_h"),
        "n_support_vectors_x": m.get("n_support_vectors_x"),
        "n_support_vectors_y": m.get("n_support_vectors_y"),
    }


# ── Endpoints legados (mantidos para compatibilidade) ─────────────────────────

@router.get("/status")
def calibration_status() -> dict:
    return {
        "status":   _cal_session["status"],
        "n_frames": len(_cal_session["targets"]),
    }


@router.post("/start")
def start_calibration(engine: str = "irisgazenet") -> dict:
    return {"ok": True, "message": "Use /new_session + /collect_point + /fit"}
