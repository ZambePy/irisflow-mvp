"""
IrisFlow — pipeline de gaze estimation inspirado no GazeFollower (Zhu et al., ACM CGIT 2025).

Arquitetura v2 (multi-fonte):
  MobileNetV2 (backbone único, congelado, pré-treinado ImageNet)
    face_patch  (224×224) → pool → 1280 features
    left_eye    (112×112) → pool → primeiros 640 features
    right_eye   (112×112, flip H) → pool → primeiros 640 features
    rect        (12 floats normalizados) — geometria espacial
    concat → vetor (2572,)
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
    Extrator multi-fonte: face + dois olhos + geometria.

    Único backbone MobileNetV2 compartilhado entre os três canais visuais.
    Equivalente ao MGazeNet do GazeFollower: backbone pré-treinado usado
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

    def _backbone(self, img: torch.Tensor) -> torch.Tensor:
        """Extrai vetor 1280-dim de um lote de imagens."""
        return self.pool(self.features(img)).flatten(1)

    def forward(
        self,
        face_img: torch.Tensor,   # (B, 3, 224, 224)
        left_img: torch.Tensor,   # (B, 3, 112, 112)
        right_img: torch.Tensor,  # (B, 3, 112, 112) — já com flip H
        rect: torch.Tensor,       # (B, 12) — geometria normalizada
    ) -> torch.Tensor:
        """
        Extrai e concatena features de três fontes visuais + geometria.

        Returns:
            tensor (B, 2572)  [1280 face + 640 left + 640 right + 12 rect]
        """
        face_feat  = self._backbone(face_img)            # (B, 1280)
        left_feat  = self._backbone(left_img)[:, :640]   # (B, 640)
        right_feat = self._backbone(right_img)[:, :640]  # (B, 640)
        return torch.cat([face_feat, left_feat, right_feat, rect], dim=1)

    def extract_numpy(
        self,
        face_img: torch.Tensor,
        left_img: torch.Tensor,
        right_img: torch.Tensor,
        rect: "np.ndarray | torch.Tensor",
    ) -> np.ndarray:
        """
        Wrapper que retorna (B, 2572) como array numpy.

        rect pode ser np.ndarray (B, 12) ou (12,) — dimensão batch adicionada
        automaticamente se necessário.
        """
        with torch.no_grad():
            if not isinstance(rect, torch.Tensor):
                rect = torch.as_tensor(rect, dtype=torch.float32)
            if rect.dim() == 1:
                rect = rect.unsqueeze(0)
            return self.forward(face_img, left_img, right_img, rect).cpu().numpy()

    def output_dim(self) -> int:
        """Dimensão do vetor de features concatenado."""
        return 2572


class IrisGazeEstimator:
    """
    Estimador completo de olhar = IrisFeatureExtractor (multi-fonte) + SVR.

    feature_version=2: face(1280) + left_eye(640) + right_eye(640) + rect(12) = 2572.

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
        face_images: "torch.Tensor | None",
        left_images: "torch.Tensor | None",
        right_images: "torch.Tensor | None",
        rects: "np.ndarray | None",
        targets: np.ndarray,
        screen_w: int = 1920,
        screen_h: int = 1080,
        svr_kernel: str = "rbf",
        svr_C: float = 10.0,
        svr_gamma: str = "scale",
        svr_epsilon: float = 0.1,
        features: "np.ndarray | None" = None,
    ) -> dict:
        """
        Treina SVR-X e SVR-Y com dados de calibração do paciente.

        Args:
            face_images:  tensor (N, 3, 224, 224) — patches de rosto
            left_images:  tensor (N, 3, 112, 112) — patches do olho esquerdo
            right_images: tensor (N, 3, 112, 112) — olho direito com flip H
            rects:        array (N, 12) — geometria normalizada
                          [fw,fh,fx,fy, lw,lh,lx,ly, rw,rh,rx,ry] / [img_w,img_h]*6
            targets:      array (N, 2) — coordenadas reais (x_px, y_px)
            features:     array (N, 2572) pré-extraído — pula extração se fornecido

        Returns:
            dict com mae_x, mae_y, mae_total (pixels), n_samples,
            n_support_vectors_x, n_support_vectors_y
        """
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVR

        self.screen_w = screen_w
        self.screen_h = screen_h

        if features is None:
            features = self.extractor.extract_numpy(
                face_images, left_images, right_images, rects
            )  # (N, 2572)

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

    def predict(
        self,
        face_img: torch.Tensor,   # (1, 3, 224, 224)
        left_img: torch.Tensor,   # (1, 3, 112, 112)
        right_img: torch.Tensor,  # (1, 3, 112, 112) — flip H
        rect: "np.ndarray | torch.Tensor",  # (12,) ou (1, 12)
    ) -> tuple[float, float]:
        """
        Prediz coordenadas de tela com inputs multi-fonte.

        Args:
            face_img:  tensor (1, 3, 224, 224)
            left_img:  tensor (1, 3, 112, 112)
            right_img: tensor (1, 3, 112, 112) — flip H já aplicado
            rect:      array (12,) ou (1, 12) — geometria normalizada

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
        features = self.extractor.extract_numpy(face_img, left_img, right_img, rect)
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
            "feature_version": 2,
            "architecture": "MobileNetV2+SVR multi-fonte (IrisFlow v2, GazeFollower)",
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "IrisGazeEstimator":
        """
        Carrega modelo salvo do disco.

        Suporta feature_version=2 (multi-fonte). Modelos v1 (1280-dim,
        sem feature_version) podem ser carregados mas o predict falhará —
        recalibre com o novo pipeline.

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

    B = 2
    face_t = torch.rand(B, 3, 224, 224)
    left_t = torch.rand(B, 3, 112, 112)
    right_t = torch.rand(B, 3, 112, 112)
    rect_t = torch.rand(B, 12)
    feat = extractor.extract_numpy(face_t, left_t, right_t, rect_t)
    assert feat.shape == (B, 2572), f"Esperado (B, 2572), obtido {feat.shape}"
    print(f"  Smoke test extract_numpy: {feat.shape}  OK")
    print()

    # ── IrisGazeEstimator — calibração ───────────────────────────────────
    estimator = IrisGazeEstimator(pretrained=False)

    N = 50
    face_cal  = torch.rand(N, 3, 224, 224)
    left_cal  = torch.rand(N, 3, 112, 112)
    right_cal = torch.rand(N, 3, 112, 112)
    rects_cal = np.random.uniform(0, 1, (N, 12)).astype(np.float32)
    targets_cal = np.column_stack([
        np.random.uniform(0, 1920, N),
        np.random.uniform(0, 1080, N),
    ])

    metrics = estimator.calibrate(
        face_cal, left_cal, right_cal, rects_cal, targets_cal
    )

    print("IrisGazeEstimator")
    print("  Teste de calibração com dados sintéticos:")
    print(f"    N={N} amostras sintéticas")
    print(f"    MAE-X: {metrics['mae_x']:.1f} px")
    print(f"    MAE-Y: {metrics['mae_y']:.1f} px")
    print(f"    Support vectors X: {metrics['n_support_vectors_x']}")
    print(f"    Support vectors Y: {metrics['n_support_vectors_y']}")
    print()

    # ── Predict ──────────────────────────────────────────────────────────
    face_s  = torch.rand(1, 3, 224, 224)
    left_s  = torch.rand(1, 3, 112, 112)
    right_s = torch.rand(1, 3, 112, 112)
    rect_s  = np.random.uniform(0, 1, 12).astype(np.float32)
    x_pred, y_pred = estimator.predict(face_s, left_s, right_s, rect_s)

    print("  Teste de predict:")
    print(f"    Output: (x={x_pred:.1f}, y={y_pred:.1f})  (coordenadas em pixels)")
    print()

    # ── Save / Load ───────────────────────────────────────────────────────
    tmp_path = os.path.join(tempfile.gettempdir(), "test_irisgazenet_v2.pkl")
    estimator.save(tmp_path)
    loaded = IrisGazeEstimator.load(tmp_path)
    x_load, y_load = loaded.predict(face_s, left_s, right_s, rect_s)

    print("  Teste de save/load:")
    print(f"    Salvo em: {tmp_path}")
    print(f"    Carregado com sucesso: {loaded.is_calibrated}")
    print(f"    Predict após load: (x={x_load:.1f}, y={y_load:.1f})  (igual ao anterior)")
    assert abs(x_load - x_pred) < 0.01 and abs(y_load - y_pred) < 0.01, (
        f"Save/load divergiu! {x_pred:.4f}≠{x_load:.4f} ou {y_pred:.4f}≠{y_load:.4f}"
    )
    print("    Consistência save/load: OK")
    print()
    print("Todos os testes passaram.")
