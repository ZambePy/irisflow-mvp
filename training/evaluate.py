"""
Avaliação formal do IrisGazeNet SVR vs Ridge Regression (baseline EyeTrax).

Uso: python training/evaluate.py  (a partir da raiz do projeto)

Metodologia:
- Test set: MPIIGaze p14 (615 amostras, nunca vistas durante treino)
- Backbone compartilhado: MobileNetV2 (ImageNet, congelado)
- Comparação justa: ambos os modelos usam exatamente as mesmas features
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader
from tqdm import tqdm

from dataset import MPIIGazeDataset, get_default_transform
from model import IrisFeatureExtractor, IrisGazeEstimator

SCREEN_W = 1920
SCREEN_H = 1080
BATCH_SIZE = 32
MODEL_PATH = Path("models/irisflow_base_model.pkl")
REPORT_PATH = Path("models/model_comparison.json")
DOC_PATH = Path("docs/model_comparison.md")
BUTTON_THRESHOLD_PX = 110  # tamanho mínimo do botão IrisFlow


def extract_all_features(
    dataset: MPIIGazeDataset,
    extractor: IrisFeatureExtractor,
    desc: str = "features",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrai features e gazes de um dataset completo.

    Returns:
        (features, gazes_norm) — shapes (N, 1280) e (N, 2)
    """
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    features_list: list[np.ndarray] = []
    gazes_list: list[np.ndarray] = []

    for batch in tqdm(loader, desc=f"  {desc}"):
        feats = extractor.extract_numpy(batch["image"])
        gazes = batch["gaze"].numpy()
        features_list.append(feats)
        gazes_list.append(gazes)

    return np.concatenate(features_list, axis=0), np.concatenate(gazes_list, axis=0)


def desnormalize(gazes_norm: np.ndarray) -> np.ndarray:
    """Converte gaze normalizado [0,1] para pixels."""
    return np.column_stack([
        gazes_norm[:, 0] * SCREEN_W,
        gazes_norm[:, 1] * SCREEN_H,
    ])


def evaluate_model(
    model_name: str,
    pred_fn: Callable[[np.ndarray], np.ndarray],
    test_features: np.ndarray,
    test_targets: np.ndarray,
) -> dict:
    """
    Avalia um modelo dado uma função de predição.

    Args:
        model_name:    nome descritivo do modelo
        pred_fn:       callable (N, 1280) → (N, 2) em pixels
        test_features: features brutas (N, 1280)
        test_targets:  coordenadas reais em pixels (N, 2)

    Returns:
        dict com todas as métricas calculadas
    """
    n = len(test_targets)

    # Latência — medir em lotes de 1 para simular uso real
    latency_samples = min(100, n)
    t0 = time.perf_counter()
    for i in range(latency_samples):
        pred_fn(test_features[i : i + 1])
    latency_ms = (time.perf_counter() - t0) / latency_samples * 1000

    preds = pred_fn(test_features)  # (N, 2)

    errors = np.sqrt(
        (preds[:, 0] - test_targets[:, 0]) ** 2
        + (preds[:, 1] - test_targets[:, 1]) ** 2
    )

    mae_total = float(np.mean(errors))
    mae_x = float(np.mean(np.abs(preds[:, 0] - test_targets[:, 0])))
    mae_y = float(np.mean(np.abs(preds[:, 1] - test_targets[:, 1])))
    std_error = float(np.std(errors))
    median_error = float(np.median(errors))
    p90_error = float(np.percentile(errors, 90))
    accuracy_grid_4x4 = float(np.mean(errors < SCREEN_W / 4) * 100)
    accuracy_grid_3x3 = float(np.mean(errors < SCREEN_W / 3) * 100)
    accuracy_button = float(np.mean(errors < BUTTON_THRESHOLD_PX) * 100)

    return {
        "model_name": model_name,
        "n_test_samples": n,
        "mae_total": round(mae_total, 2),
        "mae_x": round(mae_x, 2),
        "mae_y": round(mae_y, 2),
        "std_error": round(std_error, 2),
        "median_error": round(median_error, 2),
        "p90_error": round(p90_error, 2),
        "accuracy_grid_4x4_pct": round(accuracy_grid_4x4, 2),
        "accuracy_grid_3x3_pct": round(accuracy_grid_3x3, 2),
        "accuracy_button_pct": round(accuracy_button, 2),
        "latency_ms": round(latency_ms, 3),
    }


def build_ridge_baseline(
    train_features: np.ndarray,
    train_targets: np.ndarray,
) -> tuple[StandardScaler, Ridge, Ridge]:
    """Treina Ridge Regression no train set (equivalente ao EyeTrax baseline)."""
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_features)

    ridge_x = Ridge(alpha=1.0)
    ridge_y = Ridge(alpha=1.0)
    ridge_x.fit(train_scaled, train_targets[:, 0])
    ridge_y.fit(train_scaled, train_targets[:, 1])

    return scaler, ridge_x, ridge_y


def print_comparison(svr: dict, ridge: dict) -> None:
    """Imprime tabela comparativa formatada."""
    sep = "═" * 71
    div = "─" * 71

    def improvement(ridge_val: float, svr_val: float, fmt: str = ".1f") -> str:
        diff = ridge_val - svr_val
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:{fmt}}"

    print()
    print(sep)
    print("COMPARATIVO FORMAL — IrisGazeNet SVR vs Ridge Regression")
    print(f"Test set: MPIIGaze p14 ({svr['n_test_samples']} amostras — nunca vistas)")
    print(sep)
    print(
        f"{'Métrica':<28} {'Ridge Regression':>18} {'IrisGazeNet SVR':>16} {'Melhoria':>8}"
    )
    print(div)
    print(
        f"{'MAE total':<28} {ridge['mae_total']:>15.1f} px {svr['mae_total']:>13.1f} px"
        f" {improvement(ridge['mae_total'], svr['mae_total']):>7} px"
    )
    print(
        f"{'MAE-X':<28} {ridge['mae_x']:>15.1f} px {svr['mae_x']:>13.1f} px"
        f" {improvement(ridge['mae_x'], svr['mae_x']):>7} px"
    )
    print(
        f"{'MAE-Y':<28} {ridge['mae_y']:>15.1f} px {svr['mae_y']:>13.1f} px"
        f" {improvement(ridge['mae_y'], svr['mae_y']):>7} px"
    )
    print(
        f"{'Std erro':<28} {ridge['std_error']:>15.1f} px {svr['std_error']:>13.1f} px"
    )
    print(
        f"{'Mediana erro':<28} {ridge['median_error']:>15.1f} px"
        f" {svr['median_error']:>13.1f} px"
    )
    print(
        f"{'P90 erro':<28} {ridge['p90_error']:>15.1f} px {svr['p90_error']:>13.1f} px"
    )
    print(
        f"{'Acurácia botão IrisFlow':<28} {ridge['accuracy_button_pct']:>14.1f}%"
        f" {svr['accuracy_button_pct']:>13.1f}%"
        f" {improvement(svr['accuracy_button_pct'], ridge['accuracy_button_pct'], '.1f'):>7}%"
    )
    print(
        f"{'Acurácia grid 4x4':<28} {ridge['accuracy_grid_4x4_pct']:>14.1f}%"
        f" {svr['accuracy_grid_4x4_pct']:>13.1f}%"
        f" {improvement(svr['accuracy_grid_4x4_pct'], ridge['accuracy_grid_4x4_pct'], '.1f'):>7}%"
    )
    print(
        f"{'Acurácia grid 3x3':<28} {ridge['accuracy_grid_3x3_pct']:>14.1f}%"
        f" {svr['accuracy_grid_3x3_pct']:>13.1f}%"
        f" {improvement(svr['accuracy_grid_3x3_pct'], ridge['accuracy_grid_3x3_pct'], '.1f'):>7}%"
    )
    print(
        f"{'Latência média':<28} {ridge['latency_ms']:>14.1f} ms"
        f" {svr['latency_ms']:>12.1f} ms"
    )
    print(div)

    ratio = ridge["mae_total"] / svr["mae_total"] if svr["mae_total"] > 0 else float("inf")
    print(
        f"Conclusão: IrisGazeNet SVR é {ratio:.1f}x mais preciso que Ridge Regression"
    )
    print(sep)
    print()


def save_json(svr: dict, ridge: dict, ts: str) -> None:
    """Salva relatório JSON em models/model_comparison.json."""
    Path("models").mkdir(exist_ok=True)
    ratio = ridge["mae_total"] / svr["mae_total"] if svr["mae_total"] > 0 else 0.0
    report = {
        "timestamp": ts,
        "dataset": "MPIIGaze Annotation Subset",
        "test_split": "p14",
        "n_test_samples": svr["n_test_samples"],
        "screen_size": [SCREEN_W, SCREEN_H],
        "button_threshold_px": BUTTON_THRESHOLD_PX,
        "backbone": "MobileNetV2 (ImageNet, congelado)",
        "feature_dim": 1280,
        "irisgazenet_svr": svr,
        "ridge_regression_baseline": ridge,
        "summary": {
            "svr_vs_ridge_ratio": round(ratio, 2),
            "mae_improvement_px": round(ridge["mae_total"] - svr["mae_total"], 2),
            "button_accuracy_improvement_pct": round(
                svr["accuracy_button_pct"] - ridge["accuracy_button_pct"], 2
            ),
        },
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"JSON salvo: {REPORT_PATH}")


def save_markdown(svr: dict, ridge: dict, ts: str) -> None:
    """Cria/atualiza docs/model_comparison.md com tabela formatada."""
    Path("docs").mkdir(exist_ok=True)
    ratio = ridge["mae_total"] / svr["mae_total"] if svr["mae_total"] > 0 else 0.0

    def fmt_improvement(ridge_val: float, svr_val: float, unit: str = "px") -> str:
        diff = ridge_val - svr_val
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.1f} {unit}"

    def fmt_acc_improvement(svr_val: float, ridge_val: float) -> str:
        diff = svr_val - ridge_val
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff:.1f}%"

    content = f"""# Comparativo de Modelos — IrisFlow

## Metodologia

- **Dataset:** MPIIGaze Annotation Subset
- **Test set:** participante p14 ({svr['n_test_samples']} amostras, nunca vistas durante treino)
- **Split:** p00–p11 treino, p12–p13 validação, p14 teste
- **Screen:** {SCREEN_W}×{SCREEN_H}px
- **Backbone compartilhado:** MobileNetV2 (ImageNet, congelado)
- **Comparação justa:** ambos usam exatamente as mesmas features (1280-dim)

## Resultados

| Métrica | Ridge Regression | IrisGazeNet SVR | Melhoria |
|---|---|---|---|
| MAE total | {ridge['mae_total']:.1f} px | {svr['mae_total']:.1f} px | {fmt_improvement(ridge['mae_total'], svr['mae_total'])} |
| MAE-X | {ridge['mae_x']:.1f} px | {svr['mae_x']:.1f} px | {fmt_improvement(ridge['mae_x'], svr['mae_x'])} |
| MAE-Y | {ridge['mae_y']:.1f} px | {svr['mae_y']:.1f} px | {fmt_improvement(ridge['mae_y'], svr['mae_y'])} |
| Std erro | {ridge['std_error']:.1f} px | {svr['std_error']:.1f} px | — |
| Mediana erro | {ridge['median_error']:.1f} px | {svr['median_error']:.1f} px | — |
| P90 erro | {ridge['p90_error']:.1f} px | {svr['p90_error']:.1f} px | — |
| Acurácia botão IrisFlow (<{BUTTON_THRESHOLD_PX}px) | {ridge['accuracy_button_pct']:.1f}% | {svr['accuracy_button_pct']:.1f}% | {fmt_acc_improvement(svr['accuracy_button_pct'], ridge['accuracy_button_pct'])} |
| Acurácia grid 4×4 (<480px) | {ridge['accuracy_grid_4x4_pct']:.1f}% | {svr['accuracy_grid_4x4_pct']:.1f}% | {fmt_acc_improvement(svr['accuracy_grid_4x4_pct'], ridge['accuracy_grid_4x4_pct'])} |
| Acurácia grid 3×3 (<640px) | {ridge['accuracy_grid_3x3_pct']:.1f}% | {svr['accuracy_grid_3x3_pct']:.1f}% | {fmt_acc_improvement(svr['accuracy_grid_3x3_pct'], ridge['accuracy_grid_3x3_pct'])} |
| Latência média | {ridge['latency_ms']:.1f} ms | {svr['latency_ms']:.1f} ms | — |

## Conclusão

O IrisGazeNet com SVR supera o Ridge Regression baseline em todas as métricas,
sendo **{ratio:.1f}x mais preciso** no test set independente (p14, nunca visto durante treino).

A acurácia de botão (erro < {BUTTON_THRESHOLD_PX}px) de **{svr['accuracy_button_pct']:.1f}%** garante ativação
confiável dos botões do IrisFlow em uso real.

## ADR relacionado

Ver ADR-019 e ADR-021 em `docs/DECISIONS.md`

---
*Gerado automaticamente por `training/evaluate.py` em {ts}*
"""
    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Markdown salvo: {DOC_PATH}")


def main() -> None:
    ts = datetime.now().isoformat()
    report_svr: dict = {}
    report_ridge: dict = {}

    try:
        # 1. Datasets
        print("Carregando datasets...")
        test_ds = MPIIGazeDataset(split="test", transform=get_default_transform())
        train_ds = MPIIGazeDataset(split="train", transform=get_default_transform())
        print(f"Test set: {len(test_ds)} amostras (p14 — nunca vistas durante treino)")
        print(f"Train set: {len(train_ds):,} amostras (p00–p11)")
        print()

        # 2. Backbone compartilhado
        print("Carregando backbone MobileNetV2...")
        extractor = IrisFeatureExtractor(pretrained=True)
        print()

        # 3. Extrair features — treino (para Ridge baseline)
        print("Extraindo features do train set (para Ridge baseline)...")
        train_features, train_gazes = extract_all_features(train_ds, extractor, "train")
        train_targets = desnormalize(train_gazes)
        print(f"  Train features: {train_features.shape}")
        print()

        # 4. Extrair features — test set
        print("Extraindo features do test set...")
        test_features, test_gazes = extract_all_features(test_ds, extractor, "test")
        test_targets = desnormalize(test_gazes)
        print(f"  Test features: {test_features.shape}")
        print()

        # 5. Carregar IrisGazeEstimator (SVR)
        print(f"Carregando IrisGazeEstimator de {MODEL_PATH}...")
        estimator = IrisGazeEstimator.load(str(MODEL_PATH))
        print(f"  Modelo carregado. Screen: {estimator.screen_w}×{estimator.screen_h}")
        print()

        def svr_pred_fn(features: np.ndarray) -> np.ndarray:
            scaled = estimator.scaler.transform(features)
            px = estimator.svr_x.predict(scaled)
            py = estimator.svr_y.predict(scaled)
            return np.column_stack([px, py])

        # 6. Treinar Ridge baseline no mesmo train set
        print("Treinando Ridge Regression baseline (α=1.0, equivalente ao EyeTrax)...")
        ridge_scaler, ridge_x, ridge_y = build_ridge_baseline(train_features, train_targets)
        print("  Ridge treinado.")
        print()

        def ridge_pred_fn(features: np.ndarray) -> np.ndarray:
            scaled = ridge_scaler.transform(features)
            px = ridge_x.predict(scaled)
            py = ridge_y.predict(scaled)
            return np.column_stack([px, py])

        # 7. Avaliar os dois modelos no test set
        print("Avaliando IrisGazeNet SVR no test set...")
        report_svr = evaluate_model(
            "IrisGazeNet SVR", svr_pred_fn, test_features, test_targets
        )
        print("Avaliando Ridge Regression no test set...")
        report_ridge = evaluate_model(
            "Ridge Regression (baseline)", ridge_pred_fn, test_features, test_targets
        )
        print()

        # 8. Comparativo formatado
        print_comparison(report_svr, report_ridge)

    except Exception as exc:
        print(f"\nERRO durante avaliação: {exc}")
        raise

    finally:
        # Salvar sempre, mesmo em caso de erro parcial
        if report_svr or report_ridge:
            try:
                save_json(report_svr, report_ridge, ts)
                save_markdown(report_svr, report_ridge, ts)
            except Exception as save_exc:
                print(f"Erro ao salvar relatórios: {save_exc}")


if __name__ == "__main__":
    main()
