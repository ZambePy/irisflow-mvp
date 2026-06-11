"""
DataLoader do MPIIGaze para o IrisGazeNet.

Fonte: Annotation Subset — único subconjunto com labels de gaze
(path + 12 landmarks + gaze_x + gaze_y + 2 coords extras).

O Annotation Subset não fornece ângulos de pose (pitch/yaw) — apenas
landmarks e coordenadas de gaze em pixels. O pipeline usa apenas features
de imagem extraídas pelo MobileNetV2.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

logger = logging.getLogger(__name__)

_SPLIT_PARTICIPANTS: dict[str, list[str]] = {
    "train": [f"p{i:02d}" for i in range(12)],     # p00–p11
    "val":   [f"p{i:02d}" for i in range(12, 14)],  # p12–p13
    "test":  [f"p{i:02d}" for i in range(14, 15)],  # p14
}

_ANNOTATION_DIR = "Annotation Subset"

# Formato verificado: path + 12 landmarks + gaze_x + gaze_y [+ 2 extras em pixels]
_MIN_COLS = 15
_COL_GAZE_X = 13
_COL_GAZE_Y = 14


def get_default_transform() -> transforms.Compose:
    """Retorna transform padrão compatível com MobileNetV2 (normalização ImageNet)."""
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


class MPIIGazeDataset(Dataset):
    """Dataset MPIIGaze para treinamento do IrisGazeNet."""

    def __init__(
        self,
        root: str = "datasets/MPIIGaze",
        participants: list[str] | None = None,
        split: str = "train",
        transform: Any = None,
        screen_w: int = 1920,
        screen_h: int = 1080,
    ) -> None:
        """
        Inicializa o dataset MPIIGaze.

        Args:
            root: Caminho raiz do diretório MPIIGaze.
            participants: Lista explícita de participantes (ex.: ["p00", "p01"]).
                          Se None, usa o split padrão.
            split: Divisão a carregar — "train" (p00–p11), "val" (p12–p13)
                   ou "test" (p14).
            transform: Transform torchvision aplicado à imagem. Se None,
                       usa get_default_transform().
            screen_w: Largura da tela em pixels usada para normalizar gaze_x.
            screen_h: Altura da tela em pixels usada para normalizar gaze_y.
        """
        if split not in _SPLIT_PARTICIPANTS:
            raise ValueError(
                f"split deve ser um de {list(_SPLIT_PARTICIPANTS.keys())}, "
                f"recebido '{split}'"
            )

        self.root = Path(root)
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.transform = transform if transform is not None else get_default_transform()
        self.participants = (
            participants if participants is not None else _SPLIT_PARTICIPANTS[split]
        )

        self.samples: list[dict[str, Any]] = []
        self._load_all()

    # ------------------------------------------------------------------
    # Carregamento de dados
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Percorre todos os participantes e carrega suas amostras."""
        annotation_root = self.root / _ANNOTATION_DIR

        for participant in self.participants:
            annotation_file = annotation_root / f"{participant}.txt"
            if not annotation_file.exists():
                logger.warning(
                    "Arquivo de anotação não encontrado: %s — participante ignorado.",
                    annotation_file,
                )
                continue

            for entry in self.parse_annotation_file(annotation_file):
                img_rel = Path(entry["img_path"])
                img_path = self.root / "Data" / "Original" / participant / img_rel

                gaze_x, gaze_y = entry["gaze"]
                self.samples.append(
                    {
                        "img_path": img_path,
                        "gaze_x_norm": gaze_x / self.screen_w,
                        "gaze_y_norm": gaze_y / self.screen_h,
                    }
                )

    # ------------------------------------------------------------------
    # Interface do Dataset
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """Retorna o número total de amostras carregadas."""
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        """
        Retorna uma amostra do dataset.

        Args:
            idx: Índice da amostra.

        Returns:
            Dict com:
                "image": tensor (3, 224, 224)
                "gaze":  tensor (2,)   — [x_norm, y_norm] em [0, 1]
        """
        sample = self.samples[idx]
        img_path: Path = sample["img_path"]

        try:
            img = Image.open(img_path).convert("RGB")
            image_tensor: torch.Tensor = self.transform(img)
        except Exception as exc:
            logger.warning(
                "Imagem corrompida ignorada (%s): %s — substituída por zeros.",
                img_path,
                exc,
            )
            image_tensor = torch.zeros(3, 224, 224)

        gaze = torch.tensor(
            [sample["gaze_x_norm"], sample["gaze_y_norm"]], dtype=torch.float32
        )

        return {"image": image_tensor, "gaze": gaze}

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_annotation_file(filepath: Path) -> list[dict[str, Any]]:
        """
        Parseia um arquivo pXX.txt do Annotation Subset.

        Formato verificado (17 colunas, todos inteiros):
            dayYY/ZZZZ.jpg  lm1x lm1y ... lm6x lm6y  gaze_x gaze_y  extra1 extra2

        Args:
            filepath: Caminho absoluto para o arquivo de anotação.

        Returns:
            Lista de dicts com chaves:
                "img_path"  (str)                 — caminho relativo dentro de pXX/
                "gaze"      (tuple[float, float]) — (gaze_x, gaze_y) em pixels
        """
        results: list[dict[str, Any]] = []
        with open(filepath, "r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                parts = line.split()

                if len(parts) < _MIN_COLS:
                    logger.warning(
                        "%s linha %d: esperado ≥%d tokens, encontrado %d — ignorando.",
                        filepath.name,
                        line_no,
                        _MIN_COLS,
                        len(parts),
                    )
                    continue

                try:
                    img_path = parts[0]
                    gaze_x = float(parts[_COL_GAZE_X])
                    gaze_y = float(parts[_COL_GAZE_Y])
                except ValueError as exc:
                    logger.warning(
                        "%s linha %d: erro de parse — %s — ignorando.",
                        filepath.name,
                        line_no,
                        exc,
                    )
                    continue

                results.append({"img_path": img_path, "gaze": (gaze_x, gaze_y)})
        return results

    # ------------------------------------------------------------------
    # Estatísticas
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas descritivas do dataset.

        Returns:
            Dict com:
                "n_samples"      (int)
                "n_participants" (int)
                "gaze_mean"      (tuple[float, float]) — (mean_x, mean_y)
                "gaze_std"       (tuple[float, float]) — (std_x,  std_y)
        """
        if not self.samples:
            return {
                "n_samples": 0,
                "n_participants": len(self.participants),
                "gaze_mean": (0.0, 0.0),
                "gaze_std": (0.0, 0.0),
            }

        gx = np.array([s["gaze_x_norm"] for s in self.samples], dtype=np.float32)
        gy = np.array([s["gaze_y_norm"] for s in self.samples], dtype=np.float32)
        return {
            "n_samples": len(self.samples),
            "n_participants": len(self.participants),
            "gaze_mean": (float(gx.mean()), float(gy.mean())),
            "gaze_std": (float(gx.std()), float(gy.std())),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    ds_train = MPIIGazeDataset(split="train")
    ds_val = MPIIGazeDataset(split="val")
    ds_test = MPIIGazeDataset(split="test")

    print("\nMPIIGaze Dataset")
    print(f"  Train: {len(ds_train):>7,} amostras (p00-p11)")
    print(f"  Val:   {len(ds_val):>7,} amostras  (p12-p13)")
    print(f"  Test:  {len(ds_test):>7,} amostras  (p14)")

    if len(ds_train) > 0:
        sample = ds_train[0]
        image_t: torch.Tensor = sample["image"]
        gaze_t: torch.Tensor = sample["gaze"]

        print("\nPrimeiro item:")
        print(f"  image: {image_t.shape}")
        print(f"  gaze:  {gaze_t}")

        gaze_in_range = bool((gaze_t >= 0.0).all() and (gaze_t <= 1.0).all())
        print(f"OK Gaze em [0, 1]: {gaze_in_range}")

        stats = ds_train.get_stats()
        print("\nEstatisticas (train):")
        print(f"  gaze_mean: ({stats['gaze_mean'][0]:.4f}, {stats['gaze_mean'][1]:.4f})")
        print(f"  gaze_std:  ({stats['gaze_std'][0]:.4f}, {stats['gaze_std'][1]:.4f})")
