"""
Pré-treino do IrisGazeEstimator no MPIIGaze Annotation Subset.

Uso: python training/pretrain.py  (a partir da raiz do projeto)
"""

from pathlib import Path
import numpy as np
import json
import time
from datetime import datetime
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from dataset import MPIIGazeDataset, get_default_transform
from model import IrisFeatureExtractor, IrisGazeEstimator


def extract_all_features(
    dataset: MPIIGazeDataset,
    extractor: IrisFeatureExtractor,
    batch_size: int = 32,
) -> tuple[np.ndarray, np.ndarray]:
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    features_list = []
    gazes_list = []

    for batch in tqdm(loader, desc="  batches"):
        images = batch["image"]
        features = extractor.extract_numpy(images)  # (B, 1280)
        gazes = batch["gaze"].numpy()               # (B, 2) normalizado
        features_list.append(features)
        gazes_list.append(gazes)

    features_all = np.concatenate(features_list, axis=0)
    gazes_all = np.concatenate(gazes_list, axis=0)
    return features_all, gazes_all


def desnormalize_gaze(
    gazes_norm: np.ndarray, screen_w: int, screen_h: int
) -> np.ndarray:
    targets_x = gazes_norm[:, 0] * screen_w
    targets_y = gazes_norm[:, 1] * screen_h
    return np.column_stack([targets_x, targets_y])


def calculate_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, screen_w: int, screen_h: int
) -> dict:
    mae_x = float(np.mean(np.abs(y_pred[:, 0] - y_true[:, 0])))
    mae_y = float(np.mean(np.abs(y_pred[:, 1] - y_true[:, 1])))
    errors = np.sqrt(
        (y_pred[:, 0] - y_true[:, 0]) ** 2 + (y_pred[:, 1] - y_true[:, 1]) ** 2
    )
    mae_total = float(np.mean(errors))
    std_error = float(np.std(errors))
    accuracy_4x4 = float(np.mean(errors < screen_w / 4) * 100)
    return {
        "mae_x": round(mae_x, 2),
        "mae_y": round(mae_y, 2),
        "mae_total": round(mae_total, 2),
        "std_error": round(std_error, 2),
        "accuracy_4x4": round(accuracy_4x4, 2),
    }


def main() -> None:
    SCREEN_W = 1920
    SCREEN_H = 1080
    BATCH_SIZE = 32
    SVR_KERNEL = "rbf"
    SVR_C = 10.0
    SVR_GAMMA = "scale"
    SVR_EPSILON = 0.1
    MODEL_PATH = Path("models/irisflow_base_model.pkl")
    REPORT_PATH = Path("models/pretrain_report.json")

    report: dict = {}

    try:
        # 1. Backbone
        extractor = IrisFeatureExtractor(pretrained=True)
        print("Backbone carregado (MobileNetV2, ImageNet)")
        print()

        # 2. Datasets
        train_ds = MPIIGazeDataset(split="train", transform=get_default_transform())
        val_ds = MPIIGazeDataset(split="val", transform=get_default_transform())
        print(f"Train: {len(train_ds):,} amostras | Val: {len(val_ds):,} amostras")
        print()

        # 3. Extrair features — treino
        print("Extraindo features do conjunto de treino...")
        t0 = time.time()
        train_features, train_gazes = extract_all_features(train_ds, extractor, BATCH_SIZE)
        print(f"Extração concluída em {time.time() - t0:.1f}s")
        print()

        # 4. Desnormalizar gaze para pixels
        train_targets = desnormalize_gaze(train_gazes, SCREEN_W, SCREEN_H)

        # 5. Treinar SVR
        print("Treinando SVR-X e SVR-Y...")
        estimator = IrisGazeEstimator(pretrained=True)
        metrics_train = estimator.calibrate(
            images=None,
            features=train_features,
            targets=train_targets,
            screen_w=SCREEN_W,
            screen_h=SCREEN_H,
            svr_C=SVR_C,
            svr_gamma=SVR_GAMMA,
            svr_epsilon=SVR_EPSILON,
        )
        print(
            f"  Treino — MAE-X: {metrics_train['mae_x']:.1f} px"
            f" | MAE-Y: {metrics_train['mae_y']:.1f} px"
            f" | Total: {metrics_train['mae_total']:.1f} px"
        )
        print()

        # 6. Avaliar no val set
        print("Avaliando no conjunto de validação...")
        val_features, val_gazes = extract_all_features(val_ds, extractor, BATCH_SIZE)
        val_targets = desnormalize_gaze(val_gazes, SCREEN_W, SCREEN_H)

        val_features_scaled = estimator.scaler.transform(val_features)
        pred_x = estimator.svr_x.predict(val_features_scaled)
        pred_y = estimator.svr_y.predict(val_features_scaled)
        val_preds = np.column_stack([pred_x, pred_y])

        metrics_val = calculate_metrics(val_targets, val_preds, SCREEN_W, SCREEN_H)
        print()

        # 7. Salvar modelo
        Path("models").mkdir(exist_ok=True)
        estimator.save(str(MODEL_PATH))
        print(f"Modelo salvo: {MODEL_PATH}")

        # 8. Montar relatório
        improvement = round(339.4 - metrics_val["mae_total"], 1)
        report = {
            "timestamp": datetime.now().isoformat(),
            "dataset": "MPIIGaze Annotation Subset",
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "screen_size": [SCREEN_W, SCREEN_H],
            "svr_params": {
                "kernel": SVR_KERNEL,
                "C": SVR_C,
                "gamma": SVR_GAMMA,
                "epsilon": SVR_EPSILON,
            },
            "backbone": "MobileNetV2 (ImageNet, congelado)",
            "feature_dim": 1280,
            "metrics_train": metrics_train,
            "metrics_val": metrics_val,
            "model_path": str(MODEL_PATH),
            "baseline_comparison": {
                "eyetrax_ridge_mae": 339.4,
                "irisgazenet_svr_mae_val": metrics_val["mae_total"],
                "improvement_px": improvement,
            },
        }

        # 9. Resumo final
        print()
        sep = "═" * 39
        div = "─" * 39
        print(sep)
        print("RESULTADO DO PRÉ-TREINO IrisGazeNet")
        print(sep)
        print(f"Dataset:      MPIIGaze Annotation Subset")
        print(f"Train:        {len(train_ds):,} amostras")
        print(f"Val:          {len(val_ds):,} amostras")
        print(div)
        print("VALIDAÇÃO:")
        print(f"MAE total:    {metrics_val['mae_total']:.1f} px")
        print(f"MAE-X:        {metrics_val['mae_x']:.1f} px")
        print(f"MAE-Y:        {metrics_val['mae_y']:.1f} px")
        print(f"Std erro:     {metrics_val['std_error']:.1f} px")
        print(f"Acurácia 4x4: {metrics_val['accuracy_4x4']:.1f}%")
        print(div)
        print("COMPARATIVO:")
        print(f"EyeTrax baseline: 339.4 px")
        print(f"IrisGazeNet SVR:  {metrics_val['mae_total']:.1f} px")
        print(f"Melhoria:         +{improvement:.1f} px")
        print(div)
        print(f"Modelo salvo: {MODEL_PATH}")
        print(f"Relatório:    {REPORT_PATH}")
        print(sep)

    except Exception as exc:
        print(f"\nERRO durante pré-treino: {exc}")
        report["error"] = str(exc)
        raise

    finally:
        if report:
            Path("models").mkdir(exist_ok=True)
            with open(REPORT_PATH, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Relatório salvo: {REPORT_PATH}")


if __name__ == "__main__":
    main()
