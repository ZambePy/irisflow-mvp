"""
IrisGazeNet — modelo próprio do IrisFlow para gaze estimation.

Arquitetura:
  MobileNetV2 backbone (pré-treinado ImageNet)
    → features (1280)
  + pose da cabeça (yaw, pitch, roll)
    → concatenação (1283)
  → MLP: 1283 → 256 → 64 → 2 (x_norm, y_norm)

Output: coordenadas normalizadas [0, 1] relativas à tela.
Desnormalizar: x_pixel = x_norm * screen_width
"""
import pickle

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models


class IrisGazeNet(nn.Module):
    """Backbone CNN + MLP para estimativa de ponto de olhar na tela."""

    def __init__(self, pretrained: bool = True, dropout: float = 0.3) -> None:
        super().__init__()

        backbone = models.mobilenet_v2(
            weights="IMAGENET1K_V1" if pretrained else None
        )
        self.backbone = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)

        for param in self.backbone.parameters():
            param.requires_grad = False

        self.mlp = nn.Sequential(
            nn.Linear(1283, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 2),
            nn.Sigmoid(),
        )

    def forward(self, image: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
        """
        Passa imagem e pose pelo modelo e retorna coordenadas normalizadas.

        Args:
            image: tensor (B, 3, 224, 224)
            pose:  tensor (B, 3) — yaw, pitch, roll em radianos

        Returns:
            tensor (B, 2) com valores em [0, 1] representando (x_norm, y_norm)
        """
        features = self.pool(self.backbone(image)).flatten(1)
        combined = torch.cat([features, pose], dim=1)
        return self.mlp(combined)

    def unfreeze_backbone(self, layers: int = 3) -> None:
        """Descongela as últimas N camadas do backbone para fine-tuning."""
        backbone_children = list(self.backbone.children())
        for layer in backbone_children[-layers:]:
            for param in layer.parameters():
                param.requires_grad = True

    def count_parameters(self) -> dict:
        """Retorna contagem de parâmetros treináveis e totais."""
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable}


class IrisGazeNetCalibrated:
    """
    Wrapper que adiciona SVR de calibração sobre o IrisGazeNet.

    Replica o padrão do GazeFollower: dois SVR separados para X e Y.
    O backbone extrai features (1283-d) que o SVR usa para mapear
    o olhar às coordenadas reais de tela do paciente.
    """

    def __init__(self, base_model: IrisGazeNet) -> None:
        self.base_model = base_model
        self.svr_x = None
        self.svr_y = None
        self.is_calibrated: bool = False
        self.screen_w: int = 1920
        self.screen_h: int = 1080

    def extract_features(
        self, image: torch.Tensor, pose: torch.Tensor
    ) -> np.ndarray:
        """
        Extrai features do backbone SEM passar pelo MLP.

        Usado para coletar dados de calibração.

        Args:
            image: tensor (B, 3, 224, 224)
            pose:  tensor (B, 3)

        Returns:
            array numpy (B, 1283)
        """
        with torch.no_grad():
            features = self.base_model.pool(
                self.base_model.backbone(image)
            ).flatten(1)
            combined = torch.cat([features, pose], dim=1)
        return combined.cpu().numpy()

    def calibrate(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        screen_w: int = 1920,
        screen_h: int = 1080,
    ) -> None:
        """
        Treina SVR com dados de calibração do paciente.

        Args:
            features:  (N, 1283) — saída de extract_features
            targets:   (N, 2)    — coordenadas reais (x_pixel, y_pixel)
            screen_w:  largura da tela em pixels
            screen_h:  altura da tela em pixels
        """
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

        self.screen_w = screen_w
        self.screen_h = screen_h

        self.scaler = StandardScaler()
        features_scaled = self.scaler.fit_transform(features)

        self.svr_x = SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.1)
        self.svr_y = SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.1)
        self.svr_x.fit(features_scaled, targets[:, 0])
        self.svr_y.fit(features_scaled, targets[:, 1])
        self.is_calibrated = True

    def predict(
        self, image: torch.Tensor, pose: torch.Tensor
    ) -> tuple[float, float]:
        """
        Prediz coordenadas de tela em pixels.

        Args:
            image: tensor (1, 3, 224, 224)
            pose:  tensor (1, 3)

        Returns:
            (x_pixel, y_pixel) clipados aos limites da tela
        """
        if not self.is_calibrated:
            with torch.no_grad():
                out = self.base_model(image, pose)[0]
            return (
                float(out[0]) * self.screen_w,
                float(out[1]) * self.screen_h,
            )

        features = self.extract_features(image, pose)
        features_scaled = self.scaler.transform(features)
        x = float(self.svr_x.predict(features_scaled)[0])
        y = float(self.svr_y.predict(features_scaled)[0])
        x = max(0, min(x, self.screen_w))
        y = max(0, min(y, self.screen_h))
        return x, y

    def save(self, path: str) -> None:
        """Salva modelo base + SVR + scaler em um único arquivo .pkl."""
        data = {
            "model_state": self.base_model.state_dict(),
            "svr_x": self.svr_x,
            "svr_y": self.svr_y,
            "scaler": self.scaler if hasattr(self, "scaler") else None,
            "is_calibrated": self.is_calibrated,
            "screen_w": self.screen_w,
            "screen_h": self.screen_h,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str, pretrained: bool = False) -> "IrisGazeNetCalibrated":
        """Carrega modelo calibrado salvo em disco."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        base = IrisGazeNet(pretrained=pretrained)
        base.load_state_dict(data["model_state"])
        obj = cls(base)
        obj.svr_x = data["svr_x"]
        obj.svr_y = data["svr_y"]
        obj.scaler = data.get("scaler")
        obj.is_calibrated = data["is_calibrated"]
        obj.screen_w = data["screen_w"]
        obj.screen_h = data["screen_h"]
        return obj


if __name__ == "__main__":
    model = IrisGazeNet(pretrained=False)
    params = model.count_parameters()

    print("IrisGazeNet")
    print(f"  Parâmetros totais:     {params['total'] / 1e6:.1f}M")
    print(f"  Parâmetros treináveis: {params['trainable'] / 1e3:.0f}k (só MLP — backbone congelado)")
    print()

    B = 2
    image = torch.rand(B, 3, 224, 224)
    pose = torch.rand(B, 3)

    model.eval()
    with torch.no_grad():
        output = model(image, pose)

    print("Teste forward pass:")
    print(f"  Input image: {tuple(image.shape)}")
    print(f"  Input pose:  {tuple(pose.shape)}")
    print(f"  Output:      {output}")
    in_range = bool((output >= 0).all() and (output <= 1).all())
    print(f"  ✓ Output em [0, 1]: {in_range}")
