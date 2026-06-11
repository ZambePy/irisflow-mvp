"""
evaluate_accuracy.py — benchmark de acurácia do IrisGazeEstimator v2 (multi-fonte).

Fluxo:
  1. Carrega IrisGazeEstimator do arquivo .pkl (feature_version=2)
  2. Exibe 9 pontos de validação (grid 3×3) em janela fullscreen OpenCV
  3. Coleta 10 predições por ponto (face + dois olhos + rect)
  4. Calcula MAE-X, MAE-Y, MAE-total e compara com baseline 22.7px
  5. Salva relatório em models/accuracy_report.json

Rodar a partir da raiz do projeto:
  python training/evaluate_accuracy.py
  python training/evaluate_accuracy.py --model models/outro_modelo.pkl
"""
import cv2
import numpy as np
import json
import math
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

import mediapipe as mp
import torch
from torchvision import transforms


WINDOW = "IrisFlow Benchmark v2"
N_SAMPLES = 10        # frames por ponto de validação
COLLECT_TIMEOUT = 8.0
LOOK_PHASE_S = 1.0
BASELINE_MAE = 22.7   # baseline IrisFlow v1 (single-eye)

_FACE_LM = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
    172,  58, 132,  93, 234, 127, 162,  21,  54, 103,  67, 109,
]
_LEFT_LM  = [33, 133, 160, 144, 158, 153]
_RIGHT_LM = [362, 263, 387, 373, 385, 380]

_NORM = dict(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
_TF_FACE = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(**_NORM),
])
_TF_EYE = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((112, 112)),
    transforms.ToTensor(),
    transforms.Normalize(**_NORM),
])


# ── Utilitários ───────────────────────────────────────────────────────────────

def get_screen_size() -> tuple[int, int]:
    """Retorna (largura, altura) da tela principal."""
    try:
        from screeninfo import get_monitors
        m = get_monitors()[0]
        return m.width, m.height
    except Exception:
        pass
    try:
        import ctypes
        u = ctypes.windll.user32
        return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
    except Exception:
        pass
    return 1920, 1080


def _check_model_compat(model_path: str) -> tuple:
    """
    Inspeciona o pkl sem carregá-lo completamente.
    Returns: ("ok", version), ("v1_incompatible", version),
             ("not_found", None), ("error", exception)
    """
    import pickle
    path = Path(model_path)
    if not path.exists():
        return "not_found", None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        version = data.get("feature_version", 1)
        return ("ok", version) if version == 2 else ("v1_incompatible", version)
    except Exception as exc:
        return "error", exc


def load_estimator(model_path: str):
    """Carrega IrisGazeEstimator v2 com verificação de feature_version."""
    path = Path(model_path)
    status, info = _check_model_compat(model_path)

    if status == "not_found":
        print(f"\n[ERRO] Modelo não encontrado: {path.absolute()}")
        print("       Calibre via:")
        print("         POST /calibration/new_session")
        print("         POST /calibration/collect_point  (repetir por ponto)")
        print("         POST /calibration/fit")
        print()
        print("       Ou valide o pipeline sem câmera:")
        print("         python training/evaluate_accuracy.py --synthetic")
        return None

    if status == "v1_incompatible":
        print(f"\n[AVISO] Modelo incompatível: feature_version={info} (esperado: 2).")
        print("        O modelo antigo usa single-eye (≤1280 features) e não é")
        print("        compatível com o pipeline multi-fonte v2")
        print("        (face + left_eye + right_eye + rect = 2572 features).")
        print()
        print("        Recalibre na ordem:")
        print("          1. POST /calibration/new_session")
        print("          2. POST /calibration/collect_point  (um por ponto de tela)")
        print("          3. POST /calibration/fit")
        print()
        print("        Dica: python training/evaluate_accuracy.py --synthetic")
        print("        valida o pipeline v2 sem câmera real.")
        return None

    if status == "error":
        print(f"[ERRO] Falha ao verificar compatibilidade: {info}")
        return None

    # feature_version == 2 — seguro carregar
    script_dir = str(Path(__file__).parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        from model import IrisGazeEstimator
        estimator = IrisGazeEstimator.load(str(path))
        print(f"[OK] Modelo carregado (v2): {path.absolute()}")
        return estimator
    except Exception as e:
        print(f"[ERRO] Falha ao carregar modelo: {e}")
        return None


def extract_patches(frame: np.ndarray, face_mesh) -> tuple | None:
    """
    Extrai face_t, left_t, right_t, rect de um frame BGR.
    Retorna None se a detecção de face falhar ou os crops forem inválidos.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None

    lm = results.multi_face_landmarks[0].landmark
    h, w = frame.shape[:2]

    # Face
    face_pts = [lm[i] for i in _FACE_LM]
    fxs = [int(p.x * w) for p in face_pts]
    fys = [int(p.y * h) for p in face_pts]
    fx1 = max(0, min(fxs));  fx2 = min(w, max(fxs))
    fy1 = max(0, min(fys));  fy2 = min(h, max(fys))
    if fx2 <= fx1 or fy2 <= fy1:
        return None

    # Left eye
    left_pts = [lm[i] for i in _LEFT_LM]
    lxs = [int(p.x * w) for p in left_pts]
    lys = [int(p.y * h) for p in left_pts]
    lw_e = max(lxs) - min(lxs);  lh_e = max(lys) - min(lys)
    mg_l = max(1, int(max(lw_e, lh_e) * 0.5))
    lx1 = max(0, min(lxs) - mg_l);  lx2 = min(w, max(lxs) + mg_l)
    ly1 = max(0, min(lys) - mg_l);  ly2 = min(h, max(lys) + mg_l)
    if lx2 <= lx1 or ly2 <= ly1:
        return None

    # Right eye
    right_pts = [lm[i] for i in _RIGHT_LM]
    rxs = [int(p.x * w) for p in right_pts]
    rys = [int(p.y * h) for p in right_pts]
    rw_e = max(rxs) - min(rxs);  rh_e = max(rys) - min(rys)
    mg_r = max(1, int(max(rw_e, rh_e) * 0.5))
    rx1 = max(0, min(rxs) - mg_r);  rx2 = min(w, max(rxs) + mg_r)
    ry1 = max(0, min(rys) - mg_r);  ry2 = min(h, max(rys) + mg_r)
    if rx2 <= rx1 or ry2 <= ry1:
        return None

    # Rect normalizado
    fw = fx2 - fx1;    fh = fy2 - fy1
    lw_b = lx2 - lx1;  lh_b = ly2 - ly1
    rw_b = rx2 - rx1;  rh_b = ry2 - ry1
    denom = np.array([w, h, w, h, w, h, w, h, w, h, w, h], dtype=np.float32)
    raw   = np.array(
        [fw, fh, fx1, fy1, lw_b, lh_b, lx1, ly1, rw_b, rh_b, rx1, ry1],
        dtype=np.float32,
    )
    rect = raw / denom

    right_flipped = cv2.flip(frame[ry1:ry2, rx1:rx2], 1)

    face_t  = _TF_FACE(frame[fy1:fy2, fx1:fx2]).unsqueeze(0)  # (1, 3, 224, 224)
    left_t  = _TF_EYE(frame[ly1:ly2, lx1:lx2]).unsqueeze(0)  # (1, 3, 112, 112)
    right_t = _TF_EYE(right_flipped).unsqueeze(0)             # (1, 3, 112, 112)

    return face_t, left_t, right_t, rect


# ── Exibição ──────────────────────────────────────────────────────────────────

def show_target_point(
    canvas: np.ndarray,
    x: int, y: int,
    sw: int, sh: int,
    phase: str,
    progress: float,
    current_pt: int = 0,
    total_pts: int = 9,
) -> None:
    canvas[:] = 0

    bar_w = max(1, int(sw * progress))
    cv2.rectangle(canvas, (0, 0), (bar_w, 10), (0, 200, 0), -1)
    cv2.rectangle(canvas, (0, 0), (sw - 1, 10), (60, 60, 60), 1)

    pulse = math.sin(time.monotonic() * 4) * 0.5 + 0.5
    radius = int(15 + pulse * 10)
    cv2.circle(canvas, (x, y), radius + 10, (0, 60, 0), -1)
    cv2.circle(canvas, (x, y), radius, (0, 230, 0), -1)
    cv2.circle(canvas, (x, y), 5, (255, 255, 255), -1)

    msg = "Olhe para o ponto" if phase == "olhe" else f"Aguarde...  {int(progress * 100)}%"
    tw = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0][0]
    cv2.putText(canvas, msg, (sw // 2 - tw // 2, sh - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

    counter = f"Ponto  {current_pt} / {total_pts}"
    cw = cv2.getTextSize(counter, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 1)[0][0]
    cv2.putText(canvas, counter, (sw // 2 - cw // 2, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (140, 140, 140), 1)


# ── Coleta ────────────────────────────────────────────────────────────────────

def collect_predictions(
    estimator,
    cap,
    face_mesh,
    target_x: int,
    target_y: int,
    window_size: tuple[int, int],
    current_pt: int = 0,
    total_pts: int = 9,
    n_samples: int = N_SAMPLES,
    timeout: float = COLLECT_TIMEOUT,
) -> list[tuple[float, float]]:
    """
    Coleta n_samples predições para um ponto alvo.
    Retorna lista vazia se ESC for pressionado.
    """
    sw, sh = window_size
    canvas = np.zeros((sh, sw, 3), dtype=np.uint8)
    predictions: list[tuple[float, float]] = []

    phase_end = time.monotonic() + LOOK_PHASE_S
    while time.monotonic() < phase_end:
        show_target_point(canvas, target_x, target_y, sw, sh, "olhe", 0.0, current_pt, total_pts)
        cv2.imshow(WINDOW, canvas)
        if cv2.waitKey(16) == 27:
            return []

    start = time.monotonic()
    while len(predictions) < n_samples:
        if time.monotonic() - start > timeout:
            break

        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        patches = extract_patches(frame, face_mesh)
        if patches is None:
            continue

        face_t, left_t, right_t, rect = patches
        try:
            px, py = estimator.predict(face_t, left_t, right_t, rect)
            predictions.append((px, py))
        except Exception:
            continue

        progress = len(predictions) / n_samples
        show_target_point(canvas, target_x, target_y, sw, sh, "coletando", progress, current_pt, total_pts)
        cv2.imshow(WINDOW, canvas)
        if cv2.waitKey(1) == 27:
            return []

    return predictions


# ── Métricas ──────────────────────────────────────────────────────────────────

def calculate_metrics(results: list[dict], screen_size: tuple[int, int]) -> dict:
    sw, sh = screen_size
    all_errors: list[float] = []
    all_ex: list[float] = []
    all_ey: list[float] = []

    for pt in results:
        tx, ty = pt["target"]
        for px, py in pt["predictions"]:
            err = math.hypot(px - tx, py - ty)
            all_errors.append(err)
            all_ex.append(abs(px - tx))
            all_ey.append(abs(py - ty))

    if not all_errors:
        return {}

    mae   = float(np.mean(all_errors))
    std   = float(np.std(all_errors))
    mae_x = float(np.mean(all_ex))
    mae_y = float(np.mean(all_ey))

    cell_w4, cell_h4 = sw / 4, sh / 4
    cell_w3, cell_h3 = sw / 3, sh / 3
    within_4x4 = within_3x3 = 0
    for pt in results:
        tx, ty = pt["target"]
        for px, py in pt["predictions"]:
            if abs(px - tx) <= cell_w4 and abs(py - ty) <= cell_h4:
                within_4x4 += 1
            if abs(px - tx) <= cell_w3 and abs(py - ty) <= cell_h3:
                within_3x3 += 1

    total = len(all_errors)
    maes = [(pt["point_id"], pt["mae_pixels"]) for pt in results]

    return {
        "mae_pixels": round(mae, 1),
        "std_pixels": round(std, 1),
        "mae_x": round(mae_x, 1),
        "mae_y": round(mae_y, 1),
        "accuracy_grid_4x4": round(within_4x4 / total * 100, 1),
        "accuracy_grid_3x3": round(within_3x3 / total * 100, 1),
        "best_point":  min(maes, key=lambda t: t[1])[0],
        "worst_point": max(maes, key=lambda t: t[1])[0],
        "total_samples": total,
    }


def _interpret(mae: float) -> dict:
    if mae < 30:
        return {"rating": "Excelente", "description": "MAE < 30px — precisão alta"}
    if mae < 60:
        return {"rating": "Bom",       "description": "MAE < 60px — adequado para botões IrisFlow (mín 110px altura)"}
    if mae < 100:
        return {"rating": "Aceitável", "description": "MAE < 100px — recalibração recomendada"}
    return      {"rating": "Insuficiente", "description": "MAE ≥ 100px — recalibrar antes de usar"}


# ── Benchmark principal ───────────────────────────────────────────────────────

def run_benchmark(model_path: str = "models/irisflow_base_model.pkl") -> None:
    sw, sh = get_screen_size()
    print(f"[INFO] Janela OpenCV: {sw}×{sh}")
    print(f"[INFO] Baseline de referência: {BASELINE_MAE} px (IrisFlow v1 single-eye)")

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    estimator = load_estimator(model_path)
    if estimator is None:
        cv2.destroyAllWindows()
        return

    cap = None
    for idx in [0, 1]:
        _cap = cv2.VideoCapture(idx)
        if _cap.isOpened():
            cap = _cap
            print(f"[OK] Câmera aberta (índice {idx})")
            break
        _cap.release()

    if cap is None:
        print("[ERRO] Nenhuma câmera disponível.")
        cv2.destroyAllWindows()
        return

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        min_detection_confidence=0.5,
    )

    # Tela de instruções
    canvas = np.zeros((sh, sw, 3), dtype=np.uint8)
    lines = [
        ("Benchmark IrisFlow v2 (multi-fonte)", 1.2, (0, 220, 0)),
        ("", 0.8, (0, 0, 0)),
        ("Você verá 9 pontos na tela.", 0.85, (200, 200, 200)),
        ("Olhe fixamente para cada ponto quando ele aparecer.", 0.85, (200, 200, 200)),
        ("", 0.8, (0, 0, 0)),
        ("Pressione ENTER para começar  ou  ESC para cancelar.", 0.75, (150, 150, 150)),
    ]
    y0 = sh // 2 - len(lines) * 28
    for i, (text, sz, col) in enumerate(lines):
        if not text:
            continue
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, sz, 2)[0][0]
        cv2.putText(canvas, text, (sw // 2 - tw // 2, y0 + i * 56),
                    cv2.FONT_HERSHEY_SIMPLEX, sz, col, 2)
    cv2.imshow(WINDOW, canvas)

    while True:
        key = cv2.waitKey(50)
        if key == 27:
            cap.release()
            face_mesh.close()
            cv2.destroyAllWindows()
            print("[INFO] Cancelado pelo usuário.")
            return
        if key in (13, 10):
            break

    # Grid 3×3 com margem de 10%
    margin_x = int(sw * 0.10)
    margin_y = int(sh * 0.10)
    grid_points = [
        (cx, cy)
        for cy in [margin_y, sh // 2, sh - margin_y]
        for cx in [margin_x, sw // 2, sw - margin_x]
    ]

    results: list[dict] = []
    for i, (tx, ty) in enumerate(grid_points, start=1):
        print(f"[{i}/9] Coletando ponto ({tx}, {ty})...")

        preds = collect_predictions(
            estimator, cap, face_mesh, tx, ty, (sw, sh),
            current_pt=i, total_pts=9,
        )

        if not preds:
            cap.release()
            face_mesh.close()
            cv2.destroyAllWindows()
            print("[INFO] Benchmark interrompido.")
            return

        errors = [math.hypot(px - tx, py - ty) for px, py in preds]
        mae_pt = float(np.mean(errors))
        std_pt = float(np.std(errors))

        results.append({
            "point_id": i,
            "target": [tx, ty],
            "n_samples": len(preds),
            "mae_pixels": round(mae_pt, 1),
            "std_pixels": round(std_pt, 1),
            "predictions": [[round(px, 1), round(py, 1)] for px, py in preds],
        })
        print(f"       MAE: {mae_pt:.1f}px  (±{std_pt:.1f})")

    cap.release()
    face_mesh.close()

    metrics = calculate_metrics(results, (sw, sh))
    interpretation = _interpret(metrics["mae_pixels"])

    # Comparação com baseline
    delta = metrics["mae_pixels"] - BASELINE_MAE
    if delta < 0:
        delta_str = f"↓ {abs(delta):.1f}px melhor que baseline"
    else:
        delta_str = f"↑ {delta:.1f}px pior que baseline"

    # Tela de resultado
    canvas[:] = 0
    result_lines = [
        (f"Benchmark IrisFlow v2",                                              1.2,  (0, 220, 0)),
        (f"MAE: {metrics['mae_pixels']:.1f} px   |   {delta_str}",             0.9,  (255, 255, 255)),
        (f"MAE-X: {metrics['mae_x']:.1f} px   MAE-Y: {metrics['mae_y']:.1f} px", 0.85, (200, 200, 200)),
        (f"Acurácia 4×4: {metrics['accuracy_grid_4x4']}%   Nota: {interpretation['rating']}", 0.85, (0, 200, 255)),
        ("", 0.5, (0, 0, 0)),
        (interpretation["description"], 0.7, (150, 150, 150)),
    ]
    y0 = sh // 2 - len(result_lines) * 34
    for i, (text, sz, col) in enumerate(result_lines):
        if not text:
            continue
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, sz, 2)[0][0]
        cv2.putText(canvas, text, (sw // 2 - tw // 2, y0 + i * 68),
                    cv2.FONT_HERSHEY_SIMPLEX, sz, col, 2)
    cv2.imshow(WINDOW, canvas)
    cv2.waitKey(5000)
    cv2.destroyAllWindows()

    # Salva JSON
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "model_path": model_path,
        "screen_size": [sw, sh],
        "n_samples_per_point": N_SAMPLES,
        "baseline_mae_px": BASELINE_MAE,
        "system": {
            "engine": "IrisGazeEstimator v2 — MobileNetV2+SVR multi-fonte",
            "features": "face(1280) + left_eye(640) + right_eye(640) + rect(12) = 2572",
        },
        "points": results,
        "metrics": metrics,
        "interpretation": interpretation,
        "vs_baseline": {
            "baseline_mae": BASELINE_MAE,
            "current_mae": metrics["mae_pixels"],
            "delta_px": round(delta, 1),
            "improved": delta < 0,
        },
    }

    out_path = Path("models") / "accuracy_report.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resumo no terminal
    print()
    print("═" * 60)
    print("  BENCHMARK CONCLUÍDO — IrisFlow v2 (multi-fonte)")
    print("═" * 60)
    print(f"  MAE geral:         {metrics['mae_pixels']:.1f} px  [{delta_str}]")
    print(f"  Baseline (v1):     {BASELINE_MAE} px  (single-eye)")
    print(f"  Desvio padrão:     {metrics['std_pixels']:.1f} px")
    print(f"  MAE eixo X:        {metrics['mae_x']:.1f} px")
    print(f"  MAE eixo Y:        {metrics['mae_y']:.1f} px")
    print(f"  Acurácia 4×4:      {metrics['accuracy_grid_4x4']}%")
    print(f"  Acurácia 3×3:      {metrics['accuracy_grid_3x3']}%")
    print(f"  Melhor ponto:      #{metrics['best_point']}")
    print(f"  Pior ponto:        #{metrics['worst_point']}")
    print(f"  Total de amostras: {metrics['total_samples']}")
    print(f"  Nota:              {interpretation['rating']}")
    print(f"\n  Relatório salvo em: {out_path.absolute()}")
    print("═" * 60)


# ── Validação sintética (sem câmera) ─────────────────────────────────────────

def run_synthetic(n_samples: int = 50) -> None:
    """
    Valida o pipeline v2 sem câmera usando dados aleatórios.

    Gera n_samples entradas sintéticas (face 224×224, left/right 112×112,
    rect 12 floats), treina SVR e reporta MAE no conjunto de treino.
    """
    script_dir = str(Path(__file__).parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from model import IrisGazeEstimator  # type: ignore

    print(f"[SYNTHETIC] Gerando {n_samples} amostras sintéticas...")
    print("[SYNTHETIC] Carregando extrator MobileNetV2 (sem pesos ImageNet)...")

    rng = np.random.default_rng(42)
    face_imgs  = torch.rand(n_samples, 3, 224, 224)
    left_imgs  = torch.rand(n_samples, 3, 112, 112)
    right_imgs = torch.rand(n_samples, 3, 112, 112)
    rects      = rng.uniform(0.0, 1.0, (n_samples, 12)).astype(np.float32)

    sw, sh = 1920, 1080
    targets = np.column_stack([
        rng.uniform(0, sw, n_samples),
        rng.uniform(0, sh, n_samples),
    ]).astype(np.float32)

    estimator = IrisGazeEstimator(pretrained=False)
    print("[SYNTHETIC] Extraindo features (face + left + right + rect = 2572 dims)...")
    metrics = estimator.calibrate(
        face_imgs, left_imgs, right_imgs, rects, targets,
        screen_w=sw, screen_h=sh,
    )

    x_pred, y_pred = estimator.predict(
        face_imgs[:1], left_imgs[:1], right_imgs[:1], rects[:1],
    )

    sep = "=" * 60
    print()
    print(sep)
    print("  SYNTHETIC BENCHMARK -- IrisFlow v2 (multi-fonte)")
    print(sep)
    print(f"  Amostras sinteticas:   {n_samples}")
    print(f"  Feature vector:        face(1280) + left(640) + right(640) + rect(12) = 2572")
    print(f"  MAE-X (treino):        {metrics['mae_x']:.1f} px")
    print(f"  MAE-Y (treino):        {metrics['mae_y']:.1f} px")
    print(f"  MAE total (treino):    {metrics['mae_total']:.1f} px")
    print(f"  Support vectors X/Y:   {metrics['n_support_vectors_x']} / {metrics['n_support_vectors_y']}")
    print(f"  Predict smoke test:    (x={x_pred:.1f}, y={y_pred:.1f}) px")
    print()
    print("  Pipeline v2 validado sem camera. Sem erros de extracao ou predicao.")
    print("  Para benchmark real: calibre via API e execute sem --synthetic.")
    print(sep)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark de acurácia IrisFlow v2")
    parser.add_argument(
        "--model",
        default="models/irisflow_base_model.pkl",
        help="Caminho do modelo .pkl (padrão: models/irisflow_base_model.pkl)",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help=(
            "Valida o pipeline v2 com dados sintéticos — "
            "sem câmera nem modelo salvo. Útil para CI e smoke-tests."
        ),
    )
    args = parser.parse_args()

    if args.synthetic:
        run_synthetic()
        sys.exit(0)

    # Checagem antecipada: evita abrir janela OpenCV com modelo inválido
    status, info = _check_model_compat(args.model)
    if status == "not_found":
        print(f"\n[AVISO] Nenhum modelo encontrado em: {Path(args.model).absolute()}")
        print("        Executando validação sintética para confirmar que o pipeline v2 está OK...")
        print()
        run_synthetic()
        sys.exit(0)
    elif status == "v1_incompatible":
        print(f"\n[ERRO] Modelo incompatível: feature_version={info} (esperado: 2).")
        print("       O modelo antigo usa single-eye (≤1280 features) e não é compatível")
        print("       com o pipeline multi-fonte v2 (face + left + right + rect = 2572 features).")
        print()
        print("       Recalibre via API na ordem:")
        print("         1. POST /calibration/new_session")
        print("         2. POST /calibration/collect_point  (um por ponto de tela)")
        print("         3. POST /calibration/fit")
        print()
        print("       Dica: python training/evaluate_accuracy.py --synthetic")
        print("       confirma que o pipeline v2 está OK sem precisar de câmera.")
        sys.exit(1)
    elif status == "error":
        print(f"[ERRO] Não foi possível ler {args.model}: {info}")
        sys.exit(1)

    run_benchmark(args.model)
