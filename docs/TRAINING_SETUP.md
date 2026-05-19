# IrisFlow — Configuração do Ambiente de Treino

Guia passo a passo para configurar o ambiente de pré-treino do IrisGazeNet.
Este processo é executado uma vez pela equipe em ambiente com GPU — não é necessário nos dispositivos dos pacientes.

---

## Requisitos

### Software

| Pacote | Versão mínima |
|--------|--------------|
| Python | 3.11 |
| PyTorch | >= 2.0 |
| torchvision | >= 0.15 |
| albumentations | >= 1.3 |
| opencv-python | >= 4.8 |
| mediapipe | >= 0.10 |
| numpy | >= 1.24 |
| pandas | >= 2.0 |
| matplotlib | >= 3.7 |
| PyYAML | >= 6.0 |

### Hardware

| Opção | Especificação |
|-------|--------------|
| Recomendado (local) | GPU NVIDIA GTX 1060 6GB+ com CUDA 11.8+ |
| Recomendado (nuvem) | Google Colab T4 (gratuito) ou A100 (Colab Pro) |
| Mínimo (sem GPU) | Intel i5 + 16GB RAM — treino muito lento, não recomendado |

---

## Download dos Datasets

### MPIIGaze

1. Acessar o site do Max Planck Institute:
   ```
   https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/
   research/gaze-based-human-computer-interaction/
   appearance-based-gaze-estimation-in-the-wild
   ```
2. Baixar o dataset completo (~3.8GB comprimido).
3. Extrair dentro de `datasets/MPIIGaze/`.

Estrutura esperada após extração:
```
datasets/MPIIGaze/
├── Data/
│   ├── p00/
│   │   ├── day01/
│   │   │   ├── *.jpg          ← imagens 36×60px
│   │   │   └── annotation.txt ← pose + vetor de olhar
│   │   └── ...
│   └── p14/
└── Evaluation Subset/
```

### OpenEDS

1. Solicitar acesso pelo formulário da Meta AI:
   ```
   https://ai.meta.com/datasets/open-eds/
   ```
   > **Atenção:** aprovação pode levar 3–10 dias úteis. Solicitar com antecedência.

2. Após aprovação, baixar o dataset (~1.2GB).
3. Extrair dentro de `datasets/OpenEDS/`.

Estrutura esperada após extração:
```
datasets/OpenEDS/
├── images/
│   ├── train/
│   │   ├── *.png              ← imagens anotadas
│   │   └── *.json             ← máscaras de segmentação
│   ├── validation/
│   └── test/
└── README.txt
```

---

## Estrutura de Pastas do Projeto

```
irisflow-mvp/
├── training/
│   ├── pretrain.py            ← script de pré-treino (Fase 1)
│   ├── finetune.py            ← script de fine-tuning para teste offline
│   ├── evaluate.py            ← métricas: MAE, acurácia de tecla, latência
│   ├── dataset.py             ← MPIIGaze + OpenEDS DataLoader
│   ├── augmentation.py        ← pipeline Albumentations para ELA
│   ├── model.py               ← IrisGazeNet (MobileNetV2 + MLP)
│   └── config.yaml            ← hiperparâmetros centralizados
│
├── datasets/                  ← NÃO commitado (.gitignore)
│   ├── MPIIGaze/
│   └── OpenEDS/
│
└── models/                    ← NÃO commitado (.gitignore)
    ├── .gitkeep
    └── irisflow_base_model.pt ← gerado pelo pretrain.py
```

---

## Hiperparâmetros Iniciais

Arquivo: `training/config.yaml`

```yaml
# Backbone
backbone: mobilenet_v2
pretrained: true            # carrega pesos ImageNet do torchvision

# Arquitetura MLP
# input = features(1280) + pose(3) = 1283
mlp_layers: [1283, 256, 64, 2]

# Otimização — pré-treino
learning_rate: 1.0e-4
batch_size: 64
epochs_pretrain: 30
optimizer: AdamW
scheduler: CosineAnnealingLR
loss: MSELoss

# Otimização — fine-tuning por paciente
epochs_finetune: 20
lr_finetune: 1.0e-4        # igual ao pré-treino; backbone congelado

# Augmentation
augmentation: true
ear_threshold: 0.15         # filtro anti-piscar
noise_sigma_px: 3           # microtremores oculares (σ em pixels)
brightness_limit: -0.4      # RandomBrightnessContrast
rotate_limit: 20            # Rotate (graus)
gauss_var_limit: [10, 50]   # GaussNoise

# Paths
dataset_mpii: datasets/MPIIGaze/
dataset_openeds: datasets/OpenEDS/
output_model: models/irisflow_base_model.pt
```

---

## Métricas de Avaliação

As métricas são calculadas pelo script `training/evaluate.py` sobre o conjunto de validação do MPIIGaze (hold-out 10%).

| Métrica | Descrição | Meta |
|---------|-----------|------|
| MAE em pixels | Erro médio absoluto entre ponto predito e ponto real na tela | < 50px |
| Acurácia de tecla (grid 4×4) | % de acertos ao mapear coordenada predita para célula correta em grade 4 colunas × 4 linhas | ≥ 88% |
| Latência de inferência | Tempo médio de um forward pass completo (crop → MLP → coordenada) em CPU i5 | < 30ms |

### Como interpretar os resultados

- **MAE < 50px** em monitor Full HD (1920×1080) equivale a aproximadamente 2,6% da largura da tela — suficiente para selecionar botões de 80px+.
- **Acurácia ≥ 88%** em grid 4×4 garante que o usuário erra menos de 1 tecla em cada 8 tentativas, compatível com uso assistivo.
- **Latência < 30ms** mantém o pipeline de inferência dentro do orçamento de um frame a 30fps (33ms), sem travar a UI.

---

## Fluxo de Execução

```bash
# 1. Instalar dependências (ambiente virtual recomendado)
pip install torch torchvision albumentations opencv-python mediapipe numpy pandas matplotlib pyyaml

# 2. Verificar GPU disponível
python -c "import torch; print(torch.cuda.is_available())"

# 3. Executar pré-treino (Fase 1)
python training/pretrain.py --config training/config.yaml

# 4. Avaliar o modelo gerado
python training/evaluate.py --model models/irisflow_base_model.pt

# 5. (Opcional) Testar fine-tuning offline com amostras sintéticas
python training/finetune.py --base models/irisflow_base_model.pt --samples 200
```

---

## Notas de Segurança e Privacidade

- Os datasets MPIIGaze e OpenEDS **não devem ser commitados** no repositório — estão no `.gitignore`.
- Modelos `.pt` também ficam fora do git — o arquivo `irisflow_base_model.pt` será distribuído separadamente (release ou download automático).
- Dados de calibração dos pacientes (`profiles/{id}/gaze_model.pt`) são armazenados apenas localmente no dispositivo do paciente — nunca enviados a servidores.
