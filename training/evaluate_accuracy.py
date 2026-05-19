"""
evaluate_accuracy.py — benchmark de acurácia do sistema de gaze estimation.

Fluxo:
  1. Carrega modelo calibrado (irisflow_gaze_model.pkl)
  2. Exibe 9 pontos de validação (grid 3×3) em janela fullscreen OpenCV
  3. Coleta 30 predições por ponto
  4. Calcula MAE, desvio padrão e acurácia por grid
  5. Salva relatório em models/accuracy_report.json

Rodar a partir da raiz do projeto:
  python training/evaluate_accuracy.py
"""
import cv2
import numpy as np
import json
import time
import math
from pathlib import Path
from datetime import datetime


WINDOW = "IrisFlow Benchmark"
N_SAMPLES = 30
COLLECT_TIMEOUT = 3.0
LOOK_PHASE_S = 1.0


# ── Detecção de tamanho de tela ───────────────────────────────────────────────

def get_screen_size() -> tuple[int, int]:
    """Retorna (largura, altura) da tela principal."""
    try:
        from eyetrax.calibration.common import get_screen_size as _eyetrax_gs
        return _eyetrax_gs()
    except Exception:
        pass
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


# ── Carregamento do modelo ────────────────────────────────────────────────────

def load_estimator(model_path: str):
    """
    Carrega GazeEstimator com modelo salvo.
    Retorna None se modelo não existir, com mensagem clara.
    """
    from eyetrax import GazeEstimator

    path = Path(model_path)
    if not path.exists():
        print(f"\n[ERRO] Modelo não encontrado: {path.absolute()}")
        print("       Calibre o sistema antes de rodar o benchmark:")
        print("       python -m irisflow.app.main")
        return None

    try:
        estimator = GazeEstimator()
        estimator.load_model(str(path))
        print(f"[OK] Modelo carregado: {path.absolute()}")
        return estimator
    except Exception as e:
        print(f"[ERRO] Falha ao carregar modelo: {e}")
        return None


# ── Helpers de exibição ───────────────────────────────────────────────────────

def show_target_point(
    canvas: np.ndarray,
    x: int,
    y: int,
    sw: int,
    sh: int,
    phase: str,
    progress: float,
    current_pt: int = 0,
    total_pts: int = 9,
) -> None:
    """Desenha ponto alvo, barra de progresso e texto instrucional no canvas."""
    canvas[:] = 0

    # Barra de progresso no topo
    bar_w = max(1, int(sw * progress))
    cv2.rectangle(canvas, (0, 0), (bar_w, 10), (0, 200, 0), -1)
    cv2.rectangle(canvas, (0, 0), (sw - 1, 10), (60, 60, 60), 1)

    # Círculo pulsante (raio 15–25px)
    pulse = math.sin(time.monotonic() * 4) * 0.5 + 0.5
    radius = int(15 + pulse * 10)
    cv2.circle(canvas, (x, y), radius + 10, (0, 60, 0), -1)   # glow
    cv2.circle(canvas, (x, y), radius, (0, 230, 0), -1)        # círculo
    cv2.circle(canvas, (x, y), 5, (255, 255, 255), -1)         # centro

    # Texto instrucional
    msg = "Olhe para o ponto" if phase == "olhe" else f"Aguarde...  {int(progress * 100)}%"
    tw = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0][0]
    cv2.putText(canvas, msg, (sw // 2 - tw // 2, sh - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

    # Contador de pontos
    counter = f"Ponto  {current_pt} / {total_pts}"
    cw = cv2.getTextSize(counter, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 1)[0][0]
    cv2.putText(canvas, counter, (sw // 2 - cw // 2, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (140, 140, 140), 1)


# ── Coleta de predições ───────────────────────────────────────────────────────

def collect_predictions(
    estimator,
    cap,
    target_x: int,
    target_y: int,
    window_size: tuple[int, int],
    current_pt: int = 0,
    total_pts: int = 9,
    n_samples: int = N_SAMPLES,
    timeout: float = COLLECT_TIMEOUT,
) -> list[tuple[float, float]]:
    """
    Coleta n_samples predições válidas (sem blink, sem None).
    Exibe ponto alvo na janela OpenCV durante coleta.
    Retorna lista de (x_pred, y_pred) em pixels da janela OpenCV.
    Retorna lista vazia se ESC for pressionado.
    """
    sw, sh = window_size
    canvas = np.zeros((sh, sw, 3), dtype=np.uint8)
    predictions: list[tuple[float, float]] = []

    # Fase 1 — "olhe": exibe ponto por 1 segundo sem coletar
    phase_end = time.monotonic() + LOOK_PHASE_S
    while time.monotonic() < phase_end:
        show_target_point(canvas, target_x, target_y, sw, sh, "olhe", 0.0, current_pt, total_pts)
        cv2.imshow(WINDOW, canvas)
        if cv2.waitKey(16) == 27:
            return []

    # Fase 2 — coleta de amostras
    start = time.monotonic()
    while len(predictions) < n_samples:
        if time.monotonic() - start > timeout:
            break

        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        try:
            features, blink = estimator.extract_features(frame)
            if blink or features is None:
                continue

            coords = estimator.predict([features])[0]
            px, py = float(coords[0]), float(coords[1])

            # EyeTrax retorna coordenadas relativas à janela OpenCV de calibração.
            # Se vier normalizado [0,1], escala para pixels da janela; caso
            # contrário, usa diretamente — ambos referenciam a mesma janela.
            if 0.0 <= px <= 1.0 and 0.0 <= py <= 1.0:
                px, py = px * sw, py * sh

            predictions.append((px, py))
        except Exception:
            continue

        progress = len(predictions) / n_samples
        show_target_point(canvas, target_x, target_y, sw, sh, "coletando", progress, current_pt, total_pts)
        cv2.imshow(WINDOW, canvas)
        if cv2.waitKey(1) == 27:
            return []

    return predictions


# ── Cálculo de métricas ───────────────────────────────────────────────────────

def calculate_metrics(results: list[dict], screen_size: tuple[int, int]) -> dict:
    """
    Calcula métricas agregadas sobre todos os pontos do benchmark:
    - mae_pixels, std_pixels, mae_x, mae_y
    - accuracy_grid_4x4, accuracy_grid_3x3
    - best_point, worst_point, total_samples
    """
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

    mae = float(np.mean(all_errors))
    std = float(np.std(all_errors))
    mae_x = float(np.mean(all_ex))
    mae_y = float(np.mean(all_ey))

    # Acurácia: predição cai dentro de 1 célula do grid ao redor do alvo
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
    acc_4x4 = round(within_4x4 / total * 100, 1)
    acc_3x3 = round(within_3x3 / total * 100, 1)

    maes = [(pt["point_id"], pt["mae_pixels"]) for pt in results]
    best = min(maes, key=lambda t: t[1])[0]
    worst = max(maes, key=lambda t: t[1])[0]

    return {
        "mae_pixels": round(mae, 1),
        "std_pixels": round(std, 1),
        "mae_x": round(mae_x, 1),
        "mae_y": round(mae_y, 1),
        "accuracy_grid_4x4": acc_4x4,
        "accuracy_grid_3x3": acc_3x3,
        "best_point": best,
        "worst_point": worst,
        "total_samples": total,
    }


def _interpret(mae: float) -> dict:
    if mae < 30:
        return {
            "rating": "Excelente",
            "description": "MAE < 30px — precisão alta",
        }
    if mae < 60:
        return {
            "rating": "Bom",
            "description": "MAE < 60px — adequado para botões IrisFlow (mín 110px altura)",
        }
    if mae < 100:
        return {
            "rating": "Aceitável",
            "description": "MAE < 100px — recalibração recomendada",
        }
    return {
        "rating": "Insuficiente",
        "description": "MAE ≥ 100px — recalibrar antes de usar",
    }


# ── Benchmark principal ───────────────────────────────────────────────────────

def run_benchmark(model_path: str = "irisflow_gaze_model.pkl") -> None:
    # sw/sh = dimensões da janela OpenCV fullscreen — mesmo referencial do EyeTrax.
    # Todos os alvos e predições são expressos neste sistema de coordenadas.
    sw, sh = get_screen_size()
    print(f"[INFO] Janela OpenCV: {sw}×{sh}")

    # Janela fullscreen criada antes de qualquer cálculo de coordenadas
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    estimator = load_estimator(model_path)
    if estimator is None:
        cv2.destroyAllWindows()
        return

    # Abre câmera (índice 0, fallback 1)
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

    # Tela de instruções
    canvas = np.zeros((sh, sw, 3), dtype=np.uint8)
    lines = [
        ("Benchmark de Acurácia IrisFlow", 1.3, (0, 220, 0)),
        ("", 0.8, (0, 0, 0)),
        ("Você verá 9 pontos na tela.", 0.85, (200, 200, 200)),
        ("Olhe para cada ponto quando ele aparecer.", 0.85, (200, 200, 200)),
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
            cv2.destroyAllWindows()
            print("[INFO] Cancelado pelo usuário.")
            return
        if key in (13, 10):  # ENTER
            break

    # Grid 3×3 com margem de 10% das bordas
    margin_x = int(sw * 0.10)
    margin_y = int(sh * 0.10)
    cols_px = [margin_x, sw // 2, sw - margin_x]
    rows_px = [margin_y, sh // 2, sh - margin_y]
    grid_points = [(cx, cy) for cy in rows_px for cx in cols_px]

    # Coleta por ponto
    results: list[dict] = []
    for i, (tx, ty) in enumerate(grid_points, start=1):
        print(f"[{i}/9] Coletando ponto ({tx}, {ty})...")

        preds = collect_predictions(
            estimator, cap, tx, ty, (sw, sh),
            current_pt=i, total_pts=9,
        )

        if not preds:
            cap.release()
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

    # Métricas globais
    metrics = calculate_metrics(results, (sw, sh))
    interpretation = _interpret(metrics["mae_pixels"])

    # Tela de resultado (exibida por 5 segundos)
    canvas[:] = 0
    result_lines = [
        (f"Resultado do Benchmark", 1.2, (0, 220, 0)),
        (f"MAE: {metrics['mae_pixels']:.1f} px   |   Acurácia 4×4: {metrics['accuracy_grid_4x4']}%", 0.95, (255, 255, 255)),
        (f"Nota: {interpretation['rating']}", 0.95, (0, 200, 255)),
        ("", 0.5, (0, 0, 0)),
        (interpretation["description"], 0.75, (150, 150, 150)),
    ]
    y0 = sh // 2 - len(result_lines) * 32
    for i, (text, sz, col) in enumerate(result_lines):
        if not text:
            continue
        tw = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, sz, 2)[0][0]
        cv2.putText(canvas, text, (sw // 2 - tw // 2, y0 + i * 65),
                    cv2.FONT_HERSHEY_SIMPLEX, sz, col, 2)

    cv2.imshow(WINDOW, canvas)
    cv2.waitKey(5000)
    cv2.destroyAllWindows()

    # Salva JSON
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "model_path": model_path,
        "screen_size": [sw, sh],
        "system": {
            "engine": "EyeTrax 0.4 + Ridge Regression",
            "filter": "Kalman EMA alpha=0.2 + Deadzone 12px",
        },
        "points": results,
        "metrics": metrics,
        "interpretation": interpretation,
    }

    out_path = Path("models") / "accuracy_report.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resumo no terminal
    print()
    print("═" * 52)
    print("  BENCHMARK CONCLUÍDO")
    print("═" * 52)
    print(f"  MAE geral:         {metrics['mae_pixels']:.1f} px")
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
    print("═" * 52)


if __name__ == "__main__":
    run_benchmark()
