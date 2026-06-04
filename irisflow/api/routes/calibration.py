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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/open_camera")
def open_camera() -> dict:
    """Pré-aquece a câmera sem iniciar uma sessão de calibração."""
    cap = _get_cap()
    return {"ok": cap is not None and cap.isOpened(), "camera": 0 if cap and cap.isOpened() else None}


@router.post("/new_session")
def new_session() -> dict:
    """Reseta o estado completo da sessão de calibração."""
    _reset_session()
    return {"ok": True}


@router.post("/collect_point")
def collect_point(req: CollectPointBody) -> dict:
    """
    Coleta _N_FRAME_NEED frames válidos para um ponto de calibração.

    1. Espera _PREPARE_TIME s (usuário posiciona o olhar)
    2. Captura frames filtrando piscadas (Shoelace openness > _BLINK_THRESHOLD)
    3. Espera _WAIT_TIME s após completar
    """
    if not _collect_lock.acquire(blocking=False):
        return {"error": "Coleta já em andamento"}

    try:
        import cv2
        import mediapipe as mp
        import torch
        from torchvision import transforms
    except ImportError as exc:
        _collect_lock.release()
        return {"error": f"Dependência ausente: {exc}"}

    try:
        # Fase 1: espera prepare_time
        time.sleep(_PREPARE_TIME)

        _norm = dict(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        tf_face = transforms.Compose([
            transforms.ToPILImage(), transforms.Resize((224, 224)),
            transforms.ToTensor(), transforms.Normalize(**_norm),
        ])
        tf_eye = transforms.Compose([
            transforms.ToPILImage(), transforms.Resize((112, 112)),
            transforms.ToTensor(), transforms.Normalize(**_norm),
        ])

        cap = _get_cap()
        if cap is None or not cap.isOpened():
            return {"error": "Nenhuma câmera disponível"}

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
        )

        collected = 0
        deadline = time.time() + 20.0  # timeout de 20 s por ponto

        while collected < _N_FRAME_NEED and time.time() < deadline:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)
            if not results.multi_face_landmarks:
                continue

            lm = results.multi_face_landmarks[0].landmark
            h, w = frame.shape[:2]

            # Filtro de piscada
            left_open  = _eye_openness(lm, _LEFT_OPEN_IDX,  w, h)
            right_open = _eye_openness(lm, _RIGHT_OPEN_IDX, w, h)
            if left_open <= _BLINK_THRESHOLD or right_open <= _BLINK_THRESHOLD:
                continue

            # Face crop (478 landmarks, quadrado)
            fx1, fy1, fx2, fy2 = _face_rect_478(lm, w, h)
            if fx2 <= fx1 or fy2 <= fy1:
                continue

            scale = abs(lm[362].x - lm[133].x) * w / 100.0
            lx1, ly1, lx2, ly2 = _eye_rect(lm, 33,  133, scale, w, h)
            rx1, ry1, rx2, ry2 = _eye_rect(lm, 362, 263, scale, w, h)

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

            _cal_session["face_images"].append(tf_face(face_crop))
            _cal_session["left_images"].append(tf_eye(left_crop))
            _cal_session["right_images"].append(tf_eye(right_crop))
            _cal_session["rects"].append(rect)
            _cal_session["targets"].append([req.expected_x, req.expected_y])
            _cal_session["point_ids"].append(req.point_index)
            collected += 1

        face_mesh.close()

        # Fase 3: espera wait_time
        time.sleep(_WAIT_TIME)

        ready = collected >= _N_FRAME_NEED

        return {
            "point_index": req.point_index,
            "collected": collected,
            "needed": _N_FRAME_NEED,
            "ready": ready,
        }

    finally:
        _collect_lock.release()


@router.post("/fit")
def fit_calibration() -> dict:
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

    estimator = IrisGazeEstimator()
    metrics = estimator.calibrate(
        face_images, left_images, right_images, rects, targets,
        screen_w=irisgazenet_config.screen_w,
        screen_h=irisgazenet_config.screen_h,
    )

    model_path = irisgazenet_config.model_path
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    estimator.save(model_path)

    _cal_session["metrics"] = metrics
    _cal_session["status"]  = "calibrated"

    return {
        "mae_x":     round(metrics["mae_x"], 1),
        "mae_y":     round(metrics["mae_y"], 1),
        "mae_total": round(metrics["mae_total"], 1),
        "n_samples": metrics["n_samples"],
        "status":    "calibrated",
    }


@router.get("/result")
def calibration_result() -> dict:
    """Retorna métricas da última calibração executada via /fit."""
    if _cal_session["metrics"] is None:
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
