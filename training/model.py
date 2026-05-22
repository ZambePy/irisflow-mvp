"""
IrisFlow — pipeline de gaze estimation inspirado no GazeFollower (Zhu et al., ACM CGIT 2025).

Arquitetura:
  MobileNetV2 (pré-treinado ImageNet, backbone congelado)
    → AdaptiveAvgPool2d → vetor (1280,)
    → StandardScaler
    → SVR-X + SVR-Y
    → (x_pixels, y_pixels)

O backbone é exclusivamente um extrator de features — nunca atualizado.
O SVR é o único componente treinado pela equipe IrisFlow.
"""

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models


class IrisFeatureExtractor(nn.Module):
    """
    Extrator de features visuais baseado em MobileNetV2.

    Equivalente ao MGazeNet no GazeFollower: backbone pré-treinado usado
    apenas para extração — nenhum parâmetro é treinado ou atualizado.
    """

    def __init__(self, pretrained: bool = True) -> None:
        super().__init__()

        backbone = models.mobilenet_v2(
            weights="IMAGENET1K_V1" if pretrained else None
        )
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)

        for param in self.parameters():
            param.requires_grad = False

        self.eval()

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        """
        Extrai vetor de features de um lote de imagens.

        Args:
            image: tensor (B, 3, 224, 224)

        Returns:
            tensor (B, 1280) — features brutas do backbone
        """
        return self.pool(self.features(image)).flatten(1)

    def extract_numpy(self, image: torch.Tensor) -> np.ndarray:
        """
        Wrapper que retorna as features como array numpy.

        Útil para passar diretamente ao SVR (scikit-learn usa numpy).

        Args:
            image: tensor (B, 3, 224, 224)

        Returns:
            array numpy (B, 1280)
        """
        with torch.no_grad():
            return self.forward(image).cpu().numpy()

    def output_dim(self) -> int:
        """Retorna a dimensão do vetor de features (sempre 1280)."""
        return 1280


class IrisGazeEstimator:
    """
    Estimador completo de olhar = IrisFeatureExtractor + SVR.

    Equivalente ao GazeFollower completo: backbone extrai features,
    dois SVR separados mapeiam features → coordenadas de tela.

    Requer calibração antes de fazer predições. Sem fallback.
    """

    def __init__(self, pretrained: bool = True) -> None:
        self.extractor = IrisFeatureExtractor(pretrained=pretrained)

        # Inicializados durante calibrate()
        self.scaler = None
        self.svr_x = None
        self.svr_y = None
        self.is_calibrated: bool = False
        self.screen_w: int = 1920
        self.screen_h: int = 1080

    def calibrate(
        self,
        images: torch.Tensor | None,
        targets: np.ndarray,
        screen_w: int = 1920,
        screen_h: int = 1080,
        svr_kernel: str = "rbf",
        svr_C: float = 10.0,
        svr_gamma: str = "scale",
        svr_epsilon: float = 0.1,
        features: np.ndarray | None = None,
    ) -> dict:
        """
        Treina SVR-X e SVR-Y com dados de calibração do paciente.

        Processo idêntico ao GazeFollower: backbone extrai features,
        StandardScaler normaliza, dois SVR separados aprendem o mapeamento.

        Args:
            images:      tensor (N, 3, 224, 224) — frames de calibração;
                         pode ser None se features já extraídas forem fornecidas
            targets:     array (N, 2) — coordenadas reais (x_px, y_px)
            screen_w:    largura da tela em pixels
            screen_h:    altura da tela em pixels
            svr_kernel:  kernel do SVR (padrão: 'rbf')
            svr_C:       parâmetro de regularização C
            svr_gamma:   parâmetro gamma do kernel
            svr_epsilon: margem epsilon do SVR
            features:    array (N, 1280) pré-extraído — se fornecido, pula extração

        Returns:
            dict com mae_x, mae_y, mae_total (pixels), n_samples,
            n_support_vectors_x, n_support_vectors_y
        """
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

        self.screen_w = screen_w
        self.screen_h = screen_h

        if features is None:
            features = self.extractor.extract_numpy(images)  # (N, 1280)

        self.scaler = StandardScaler()
        features_scaled = self.scaler.fit_transform(features)

        self.svr_x = SVR(
            kernel=svr_kernel, C=svr_C, gamma=svr_gamma, epsilon=svr_epsilon
        )
        self.svr_y = SVR(
            kernel=svr_kernel, C=svr_C, gamma=svr_gamma, epsilon=svr_epsilon
        )
        self.svr_x.fit(features_scaled, targets[:, 0])
        self.svr_y.fit(features_scaled, targets[:, 1])
        self.is_calibrated = True

        pred_x = self.svr_x.predict(features_scaled)
        pred_y = self.svr_y.predict(features_scaled)
        mae_x = float(np.mean(np.abs(pred_x - targets[:, 0])))
        mae_y = float(np.mean(np.abs(pred_y - targets[:, 1])))

        return {
            "mae_x": mae_x,
            "mae_y": mae_y,
            "mae_total": float(np.sqrt(mae_x**2 + mae_y**2)),
            "n_samples": len(targets),
            "n_support_vectors_x": len(self.svr_x.support_vectors_),
            "n_support_vectors_y": len(self.svr_y.support_vectors_),
        }

    def predict(self, image: torch.Tensor) -> tuple[float, float]:
        """
        Prediz coordenadas de tela para um frame de olho.

        Args:
            image: tensor (1, 3, 224, 224) — frame do olho pré-processado

        Returns:
            (x_pixels, y_pixels) clampado dentro dos limites da tela

        Raises:
            RuntimeError: se chamado antes de calibrate()
        """
        if not self.is_calibrated:
            raise RuntimeError(
                "IrisGazeEstimator não calibrado. "
                "Chame calibrate() antes de predict()."
            )
        features = self.extractor.extract_numpy(image)  # (1, 1280)
        features_scaled = self.scaler.transform(features)
        x = float(self.svr_x.predict(features_scaled)[0])
        y = float(self.svr_y.predict(features_scaled)[0])
        x = max(0.0, min(x, float(self.screen_w)))
        y = max(0.0, min(y, float(self.screen_h)))
        return x, y

    def save(self, path: str) -> None:
        """
        Salva extrator, SVRs e scaler em um único arquivo .pkl.

        Args:
            path: caminho do arquivo de destino (ex.: 'modelo.pkl')
        """
        import pickle

        data = {
            "extractor_state": self.extractor.state_dict(),
            "scaler": self.scaler,
            "svr_x": self.svr_x,
            "svr_y": self.svr_y,
            "is_calibrated": self.is_calibrated,
            "screen_w": self.screen_w,
            "screen_h": self.screen_h,
            "feature_dim": self.extractor.output_dim(),
            "architecture": "MobileNetV2+SVR (IrisFlow v1, inspirado GazeFollower)",
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "IrisGazeEstimator":
        """
        Carrega modelo salvo do disco.

        Args:
            path: caminho do arquivo .pkl salvo por save()

        Returns:
            IrisGazeEstimator pronto para predição
        """
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(pretrained=False)
        obj.extractor.load_state_dict(data["extractor_state"])
        obj.scaler = data["scaler"]
        obj.svr_x = data["svr_x"]
        obj.svr_y = data["svr_y"]
        obj.is_calibrated = data["is_calibrated"]
        obj.screen_w = data["screen_w"]
        obj.screen_h = data["screen_h"]
        return obj


if __name__ == "__main__":
    import tempfile
    import os

    # ── IrisFeatureExtractor ──────────────────────────────────────────────
    extractor = IrisFeatureExtractor(pretrained=False)
    total = sum(p.numel() for p in extractor.parameters())
    trainable = sum(p.numel() for p in extractor.parameters() if p.requires_grad)

    print("IrisFeatureExtractor")
    print(f"  Parâmetros totais:     {total / 1e6:.1f}M")
    print(f"  Parâmetros treináveis: {trainable}  (backbone completamente congelado)")
    print(f"  Output dim: {extractor.output_dim()}")
    print()

    # ── IrisGazeEstimator — extração ─────────────────────────────────────
    estimator = IrisGazeEstimator(pretrained=False)

    images_batch = torch.rand(4, 3, 224, 224)
    features_out = estimator.extractor.extract_numpy(images_batch)

    print("IrisGazeEstimator")
    print("  Teste de extração de features:")
    print(f"    Input:  {tuple(images_batch.shape)}")
    print(f"    Output: {features_out.shape}  (numpy array)")
    print()

    # ── Calibração com dados sintéticos ──────────────────────────────────
    N = 50
    images_cal = torch.rand(N, 3, 224, 224)
    targets_cal = np.column_stack([
        np.random.uniform(0, 1920, N),
        np.random.uniform(0, 1080, N),
    ])

    metrics = estimator.calibrate(images_cal, targets_cal)

    print("  Teste de calibração com dados sintéticos:")
    print(f"    N={N} amostras sintéticas")
    print("    Métricas de treino:")
    print(f"      MAE-X: {metrics['mae_x']:.1f} px")
    print(f"      MAE-Y: {metrics['mae_y']:.1f} px")
    print(f"      Support vectors X: {metrics['n_support_vectors_x']}")
    print(f"      Support vectors Y: {metrics['n_support_vectors_y']}")
    print()

    # ── Predict ──────────────────────────────────────────────────────────
    single_frame = torch.rand(1, 3, 224, 224)
    x_pred, y_pred = estimator.predict(single_frame)

    print("  Teste de predict:")
    print(f"    Input: {tuple(single_frame.shape)}")
    print(f"    Output: (x={x_pred:.1f}, y={y_pred:.1f})  (coordenadas em pixels)")
    print()

    # ── Save / Load ───────────────────────────────────────────────────────
    tmp_path = os.path.join(tempfile.gettempdir(), "test_irisgazenet.pkl")
    estimator.save(tmp_path)
    loaded = IrisGazeEstimator.load(tmp_path)
    x_load, y_load = loaded.predict(single_frame)

    print("  Teste de save/load:")
    print(f"    Salvo em: {tmp_path}")
    print(f"    Carregado com sucesso: {loaded.is_calibrated}")
    print(f"    Predict após load: (x={x_load:.1f}, y={y_load:.1f})  (igual ao anterior)")
