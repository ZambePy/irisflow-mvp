# OBSOLETO — MPIIGaze crops de olho não suportam MediaPipe.
# Pose extraída diretamente das anotações do dataset (quando disponível).
"""
Script standalone para construir o cache de poses MediaPipe do MPIIGaze.

Uso (a partir da raiz do projeto):
    python training/build_pose_cache.py

Processa todas as imagens do split "train" com MediaPipe Face Mesh + solvePnP
e salva o resultado em datasets/mpiigaze_pose_cache.npz.
Estimativa: ~10.654 imagens x 50 ms/imagem ≈ 9 minutos em CPU.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

# Permite rodar tanto de training/ quanto da raiz do projeto
sys.path.insert(0, str(Path(__file__).parent))

from dataset import MPIIGazeDataset, _CACHE_PATH  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Constrói o cache de poses e exibe estatísticas ao final."""
    logger.info("Carregando MPIIGazeDataset (split=train)...")
    ds = MPIIGazeDataset(split="train")
    total_amostras = len(ds)
    logger.info("Dataset carregado: %d amostras.", total_amostras)

    estimativa_min = total_amostras * 50 / 1000 / 60
    logger.info(
        "Iniciando construção do cache de poses MediaPipe "
        "(estimativa: ~%.0f minutos em CPU)...",
        estimativa_min,
    )

    stats = ds.build_pose_cache(force=False)

    total = stats["total"]
    detected = stats["detected"]
    failed = stats["failed"]

    pct_detected = 100.0 * detected / total if total else 0.0
    pct_failed = 100.0 * failed / total if total else 0.0

    print("\n--- Resultado ---")
    print(f"Total de imagens processadas:  {total:,}")
    print(f"Faces detectadas:              {detected:,} ({pct_detected:.1f}%)")
    print(f"Falhas (sem face / erro):      {failed:,} ({pct_failed:.1f}%)")
    print(f"Arquivo salvo em:              {_CACHE_PATH.resolve()}")

    if total > 0 and _CACHE_PATH.exists():
        data = np.load(_CACHE_PATH, allow_pickle=False)
        poses: np.ndarray = data["poses"]  # shape (N, 3)

        print("\nDistribuicao de poses [normalizadas em -1..1]:")
        labels = [("yaw  ", 0), ("pitch", 1), ("roll ", 2)]
        for label, col_idx in labels:
            col = poses[:, col_idx]
            print(
                f"  {label}: media={col.mean():+.4f}  std={col.std():.4f}"
                f"  min={col.min():+.4f}  max={col.max():+.4f}"
            )


if __name__ == "__main__":
    main()
