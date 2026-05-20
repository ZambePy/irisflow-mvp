"""
DataLoader do MPIIGaze para o IrisGazeNet.

Fonte: Annotation Subset — único subconjunto que contém labels de gaze
(path + 12 landmarks + gaze_x + gaze_y + valores extras).
O "Evaluation Subset/sample list for eye image" referenciado na spec apenas
lista pares (caminho, lado), sem coordenadas de gaze.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

logger = logging.getLogger(__name__)

_SPLIT_PARTICIPANTS: dict[str, list[str]] = {
    "train": [f"p{i:02d}" for i in range(12)],    # p00–p11
    "val":   [f"p{i:02d}" for i in range(12, 14)], # p12–p13
    "test":  [f"p{i:02d}" for i in range(14, 15)], # p14
}

_ANNOTATION_DIR = "Annotation Subset"


def get_default_transform() -> transforms.Compose:
    """Retorna transform padrão compatível com MobileNetV2 (normalização ImageNet)."""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


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

            parsed = self.parse_annotation_file(annotation_file)
            for entry in parsed:
                # Reconstrói o caminho completo: root/Data/Original/pXX/dayYY/ZZZZ.jpg
                img_rel = Path(entry["img_path"])  # ex.: day13/0203.jpg
                img_path = self.root / "Data" / "Original" / participant / img_rel

                gaze_x, gaze_y = entry["gaze"]
                self.samples.append(
                    {
                        "img_path": img_path,
                        "gaze_x_norm": gaze_x / self.screen_w,
                        "gaze_y_norm": gaze_y / self.screen_h,
                        "landmarks": entry["landmarks"],
                    }
                )

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
                "pose":  tensor (3,)   — [yaw, pitch, roll] normalizados em [-1, 1]
                "gaze":  tensor (2,)   — [x_norm, y_norm] em [0, 1]
        """
        sample = self.samples[idx]

        try:
            img = Image.open(sample["img_path"]).convert("RGB")
            image_tensor: torch.Tensor = self.transform(img)
        except Exception as exc:
            logger.warning(
                "Imagem corrompida ignorada (%s): %s — substituída por zeros.",
                sample["img_path"],
                exc,
            )
            image_tensor = torch.zeros(3, 224, 224)

        pose = self._estimate_pose(sample["landmarks"])
        gaze = torch.tensor(
            [sample["gaze_x_norm"], sample["gaze_y_norm"]], dtype=torch.float32
        )

        return {"image": image_tensor, "pose": pose, "gaze": gaze}

    @staticmethod
    def _estimate_pose(landmarks: list[int]) -> torch.Tensor:
        """
        Estima yaw, pitch e roll a partir dos 6 landmarks faciais.

        Ordem dos landmarks no modelo de 6 pontos do MPIIGaze:
            pts[0]: canto externo do olho esquerdo
            pts[1]: canto interno do olho esquerdo
            pts[2]: canto interno do olho direito
            pts[3]: canto externo do olho direito
            pts[4]: canto esquerdo da boca
            pts[5]: canto direito da boca

        Aproximação para o MVP — sem câmera ou modelo 3D:
            yaw   = componente horizontal da direção inter-ocular (coseno)
            pitch = posição vertical dos olhos em relação à boca (normalizada)
            roll  = componente vertical da direção inter-ocular (seno)

        Returns:
            Tensor (3,) com [yaw, pitch, roll] em [-1, 1].
        """
        pts = np.array(landmarks, dtype=np.float32).reshape(6, 2)

        left_eye = pts[0:2].mean(axis=0)
        right_eye = pts[2:4].mean(axis=0)
        mouth_center = pts[4:6].mean(axis=0)

        eye_vec = right_eye - left_eye
        eye_length = float(np.linalg.norm(eye_vec)) + 1e-6
        eye_mid = (left_eye + right_eye) / 2.0

        # yaw: coseno do ângulo da linha inter-ocular com o eixo horizontal
        yaw = float(np.clip(eye_vec[0] / eye_length, -1.0, 1.0))

        # pitch: proporção vertical (olhos vs boca), centrada em 0
        vert_dist = float(mouth_center[1] - eye_mid[1])
        pitch = float(np.clip(vert_dist / (eye_length + 1e-6) - 1.5, -1.0, 1.0))

        # roll: seno do ângulo da linha inter-ocular (inclinação lateral)
        roll_rad = math.atan2(float(eye_vec[1]), float(eye_vec[0]))
        roll = float(np.clip(roll_rad / (math.pi / 2), -1.0, 1.0))

        return torch.tensor([yaw, pitch, roll], dtype=torch.float32)

    @staticmethod
    def parse_annotation_file(filepath: Path) -> list[dict[str, Any]]:
        """
        Parseia um arquivo pXX.txt do Annotation Subset.

        Formato esperado por linha:
            dayYY/ZZZZ.jpg x1 y1 x2 y2 x3 y3 x4 y4 x5 y5 x6 y6 gaze_x gaze_y ...

        Args:
            filepath: Caminho absoluto para o arquivo de anotação.

        Returns:
            Lista de dicts com chaves:
                "img_path"  (str)            — caminho relativo dentro de pXX/
                "landmarks" (list[int])       — 12 valores (6 pontos × 2 coords)
                "gaze"      (tuple[float, float]) — (gaze_x, gaze_y) em pixels
        """
        results: list[dict[str, Any]] = []
        with open(filepath, "r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line:
                    continue
                parts = line.split()
                # mínimo: path + 12 landmarks + gaze_x + gaze_y = 15 tokens
                if len(parts) < 15:
                    logger.warning(
                        "%s linha %d: esperado ≥15 tokens, encontrado %d — ignorando.",
                        filepath.name,
                        line_no,
                        len(parts),
                    )
                    continue
                try:
                    img_path = parts[0]
                    landmarks = [int(v) for v in parts[1:13]]
                    gaze_x = float(parts[13])
                    gaze_y = float(parts[14])
                except ValueError as exc:
                    logger.warning(
                        "%s linha %d: erro de parse — %s — ignorando.",
                        filepath.name,
                        line_no,
                        exc,
                    )
                    continue
                results.append(
                    {
                        "img_path": img_path,
                        "landmarks": landmarks,
                        "gaze": (gaze_x, gaze_y),
                    }
                )
        return results

    def get_stats(self) -> dict[str, Any]:
        """
        Retorna estatísticas descritivas do dataset.

        Returns:
            Dict com:
                "n_samples"     (int)
                "n_participants" (int)
                "gaze_mean"     (tuple[float, float]) — (mean_x, mean_y)
                "gaze_std"      (tuple[float, float]) — (std_x,  std_y)
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

    print("MPIIGaze Dataset")
    print(f"  Train: {len(ds_train):>7,} amostras (p00-p11)")
    print(f"  Val:   {len(ds_val):>7,} amostras  (p12-p13)")
    print(f"  Test:  {len(ds_test):>7,} amostras  (p14)")

    if len(ds_train) > 0:
        sample = ds_train[0]
        print("\nPrimeiro item:")
        print(f"  image: {sample['image'].shape}")
        print(f"  pose:  {sample['pose'].shape}")
        print(f"  gaze:  {sample['gaze']}")
        in_range = bool(
            (sample["gaze"] >= 0.0).all() and (sample["gaze"] <= 1.0).all()
        )
        print(f"OK Gaze em [0, 1]: {in_range}")

        stats = ds_train.get_stats()
        print("\nEstatisticas (train):")
        print(f"  gaze_mean: ({stats['gaze_mean'][0]:.4f}, {stats['gaze_mean'][1]:.4f})")
        print(f"  gaze_std:  ({stats['gaze_std'][0]:.4f}, {stats['gaze_std'][1]:.4f})")
