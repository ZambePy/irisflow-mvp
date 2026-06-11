"""
Pipeline de augmentation específico para ELA aplicado sobre o MPIIGaze.

Objetivo: aumentar robustez do IrisGazeNet para condições reais de
pacientes com ELA — piscar reduzido, microtremores, baixa iluminação,
posições extremas de cabeça, webcam de baixo custo.
"""

import numpy as np
import cv2
from PIL import Image
import torch
from torchvision import transforms
from typing import Callable


class ELAAugmentation:
    """
    Pipeline de augmentation específico para condições de uso em ELA.

    Recebe PIL Image, aplica transformações estocásticas e retorna PIL Image.
    Cada transformação é aplicada de forma independente conforme sua probabilidade.
    """

    def __init__(
        self,
        p_low_light: float = 0.4,
        p_noise: float = 0.4,
        p_blur: float = 0.2,
        p_shadow: float = 0.3,
        p_rotate: float = 0.6,
        p_flip: float = 0.5,
        p_blink_sim: float = 0.3,
        noise_var_limit: tuple = (10, 50),
        brightness_limit: float = -0.4,
        rotate_limit: float = 15.0,
        blink_ear_threshold: float = 0.15,
    ) -> None:
        """
        Inicializa o pipeline de augmentation ELA.

        Args:
            p_low_light: Probabilidade de simular baixa iluminação.
            p_noise: Probabilidade de adicionar ruído gaussiano.
            p_blur: Probabilidade de aplicar motion blur.
            p_shadow: Probabilidade de adicionar sombra lateral.
            p_rotate: Probabilidade de rotacionar a imagem.
            p_flip: Probabilidade de espelhar horizontalmente.
            p_blink_sim: Probabilidade de simular pálpebra semi-fechada.
            noise_var_limit: Intervalo (min, max) do desvio padrão do ruído.
            brightness_limit: Fator mínimo de brilho (máximo é sempre 1.0).
            rotate_limit: Ângulo máximo de rotação em graus.
            blink_ear_threshold: Limiar de EAR referência para simulação de piscar.
        """
        self.p_low_light = p_low_light
        self.p_noise = p_noise
        self.p_blur = p_blur
        self.p_shadow = p_shadow
        self.p_rotate = p_rotate
        self.p_flip = p_flip
        self.p_blink_sim = p_blink_sim
        self.noise_var_limit = noise_var_limit
        self.brightness_limit = brightness_limit
        self.rotate_limit = rotate_limit
        self.blink_ear_threshold = blink_ear_threshold

    def __call__(self, image: Image.Image) -> Image.Image:
        """
        Aplica o pipeline de augmentation ELA sobre a imagem.

        Args:
            image: Imagem PIL de entrada.

        Returns:
            Imagem PIL augmentada.
        """
        img = np.array(image)

        if np.random.random() < self.p_low_light:
            img = self._low_light(img)
        if np.random.random() < self.p_noise:
            img = self._gaussian_noise(img)
        if np.random.random() < self.p_blur:
            img = self._motion_blur(img)
        if np.random.random() < self.p_shadow:
            img = self._random_shadow(img)
        if np.random.random() < self.p_rotate:
            img = self._rotate(img)
        if np.random.random() < self.p_flip:
            img = self._horizontal_flip(img)
        if np.random.random() < self.p_blink_sim:
            img = self._simulate_blink_reduction(img)

        return Image.fromarray(img)

    def _low_light(self, img: np.ndarray) -> np.ndarray:
        """
        Simula ambientes escuros (quarto de paciente, iluminação indireta).

        60% dos pacientes com ELA usam em quarto com iluminação controlada
        ou reduzida — o modelo deve ser robusto a isso.
        """
        factor = np.random.uniform(0.4, 0.8)
        img = img.astype(np.float32) * factor
        return np.clip(img, 0, 255).astype(np.uint8)

    def _gaussian_noise(self, img: np.ndarray) -> np.ndarray:
        """
        Simula ruído de webcam de baixo custo (< R$100).
        """
        std = np.random.uniform(self.noise_var_limit[0], self.noise_var_limit[1])
        noise = np.random.normal(0, std, img.shape).astype(np.float32)
        img = img.astype(np.float32) + noise
        return np.clip(img, 0, 255).astype(np.uint8)

    def _motion_blur(self, img: np.ndarray) -> np.ndarray:
        """
        Simula tremor leve de câmera ou movimento de cabeça.

        Pacientes em cadeira de rodas elétrica têm vibração constante —
        o modelo deve manter acurácia sob blur leve.
        """
        kernel_size = int(np.random.choice([3, 5]))
        kernel = np.zeros((kernel_size, kernel_size), dtype=np.float32)
        if np.random.random() < 0.5:
            kernel[kernel_size // 2, :] = 1.0 / kernel_size
        else:
            kernel[:, kernel_size // 2] = 1.0 / kernel_size
        return cv2.filter2D(img, -1, kernel)

    def _random_shadow(self, img: np.ndarray) -> np.ndarray:
        """
        Simula sombra lateral (janela, abajur, luminária).
        """
        h, w = img.shape[:2]

        shadow_x = np.random.randint(w // 4, 3 * w // 4)
        if np.random.random() < 0.5:
            pts = np.array([[0, 0], [shadow_x, 0], [shadow_x, h], [0, h]], dtype=np.int32)
        else:
            pts = np.array([[shadow_x, 0], [w, 0], [w, h], [shadow_x, h]], dtype=np.int32)

        mask = np.zeros((h, w), dtype=np.float32)
        cv2.fillPoly(mask, [pts], 1.0)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)

        shadow_factor = np.random.uniform(0.4, 0.6)
        img = img.astype(np.float32)
        for c in range(img.shape[2]):
            img[:, :, c] = img[:, :, c] * (1.0 - mask * (1.0 - shadow_factor))
        return np.clip(img, 0, 255).astype(np.uint8)

    def _rotate(self, img: np.ndarray) -> np.ndarray:
        """
        Simula inclinação da cabeça (postura em cadeira de rodas).
        """
        h, w = img.shape[:2]
        angle = np.random.uniform(-self.rotate_limit, self.rotate_limit)
        center = (w / 2.0, h / 2.0)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            img, M, (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

    def _horizontal_flip(self, img: np.ndarray) -> np.ndarray:
        """
        Espelha olho esquerdo ↔ direito para aumentar diversidade de dados.
        """
        return cv2.flip(img, 1)

    def _simulate_blink_reduction(self, img: np.ndarray) -> np.ndarray:
        """
        Simula pálpebra semi-fechada (EAR reduzido em ELA).

        Pacientes com ELA avançada têm EAR cronicamente baixo — o modelo
        deve funcionar corretamente mesmo com olho parcialmente fechado.
        """
        h = img.shape[0]
        strip_height = int(np.random.uniform(0.10, 0.30) * h)

        # Gradiente de 1.0 (topo, totalmente escuro) a 0.0 (base da faixa, sem efeito)
        gradient = np.linspace(1.0, 0.0, strip_height).reshape(-1, 1, 1).astype(np.float32)

        img = img.astype(np.float32)
        img[:strip_height] = img[:strip_height] * (1.0 - gradient)
        return np.clip(img, 0, 255).astype(np.uint8)


def get_ela_transform(augment: bool = True) -> transforms.Compose:
    """
    Retorna transform completo para treino (com augmentation ELA) ou
    validação/teste (sem augmentation).

    Args:
        augment: Se True, inclui ELAAugmentation no pipeline.

    Returns:
        Transform torchvision composto.
    """
    if augment:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            ELAAugmentation(),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])


def visualize_augmentation(image_path: str, n_samples: int = 8) -> None:
    """
    Mostra grade de imagens augmentadas para debug/demonstração.

    Carrega uma imagem do MPIIGaze, aplica ELAAugmentation N vezes
    e salva grade em models/augmentation_samples.png.

    Args:
        image_path: Caminho para imagem JPG do MPIIGaze.
        n_samples: Número de amostras augmentadas a gerar (deve ser par).
    """
    from pathlib import Path

    aug = ELAAugmentation()
    original = Image.open(image_path).convert("RGB")
    original_resized = original.resize((224, 224))

    samples = []
    for _ in range(n_samples):
        augmented = aug(original_resized)
        samples.append(cv2.cvtColor(np.array(augmented), cv2.COLOR_RGB2BGR))

    cols = n_samples // 2
    row1 = cv2.hconcat(samples[:cols])
    row2 = cv2.hconcat(samples[cols:])
    grid = cv2.vconcat([row1, row2])

    Path("models").mkdir(exist_ok=True)
    out_path = "models/augmentation_samples.png"
    cv2.imwrite(out_path, grid)
    print(f"Grade salva: {out_path}")


if __name__ == "__main__":
    from pathlib import Path

    aug = ELAAugmentation()

    imgs = list(Path("datasets/MPIIGaze/Data/Original").rglob("*.jpg"))
    test_img_path = imgs[0] if imgs else None

    if test_img_path:
        original = Image.open(test_img_path).convert("RGB")
        original_resized = original.resize((224, 224))
        img_np = np.array(original_resized)

        print("Testando transformações individuais:")
        for name, fn in [
            ("low_light",        aug._low_light),
            ("noise",            aug._gaussian_noise),
            ("blur",             aug._motion_blur),
            ("shadow",           aug._random_shadow),
            ("rotate",           aug._rotate),
            ("flip",             aug._horizontal_flip),
            ("blink_simulation", aug._simulate_blink_reduction),
        ]:
            result = fn(img_np.copy())
            print(f"  {name}: shape={result.shape}, min={result.min()}, max={result.max()}")

        print()
        print("Aplicando pipeline completo 5 vezes:")
        for i in range(5):
            result = aug(original_resized)
            arr = np.array(result)
            print(f"  [{i + 1}] shape={arr.shape}, mean={arr.mean():.1f}")

        visualize_augmentation(str(test_img_path))

    print()
    print("Pipeline ELA pronto")
    print("Transformações: low_light, noise, blur, shadow, rotate, flip, blink_simulation")
    print("Amostras salvas: models/augmentation_samples.png")
    print()
    print("Configuração ELA:")
    print(f"  p_low_light:    {aug.p_low_light}  (40% das imagens)")
    print(f"  p_noise:        {aug.p_noise}  (webcam baixo custo)")
    print(f"  p_blur:         {aug.p_blur}  (tremor de câmera)")
    print(f"  p_shadow:       {aug.p_shadow}  (iluminação lateral)")
    print(f"  p_rotate:       {aug.p_rotate}  (postura cadeira rodas)")
    print(f"  p_flip:         {aug.p_flip}  (espelhar olho)")
    print(f"  p_blink_sim:    {aug.p_blink_sim}  (pálpebra semi-fechada ELA)")
