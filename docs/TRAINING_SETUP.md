# IrisFlow — Configuração do Ambiente de Treino

Guia passo a passo para configurar o ambiente de pré-treino do IrisGazeNet.
Este processo é executado uma vez pela equipe em ambiente com CPU (GPU opcional para acelerar a extração de features) — não é necessário nos dispositivos dos pacientes.

---

## Requisitos

### Software

| Pacote | Versão mínima |
|--------|--------------|
| Python | 3.11 |
| PyTorch | >= 2.0 |
| torchvision | >= 0.15 |
| scikit-learn | >= 1.3 |
| joblib | >= 1.3 |
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
| Recomendado (local) | Intel i5 + 8GB RAM — suficiente; GPU acelera a extração de features mas não é obrigatória |
| Opcional (nuvem) | Google Colab T4 (gratuito) — recomendado para extração de features mais rápida |
| Mínimo | Intel i3 + 4GB RAM — treino SVR roda em segundos; extração de features via MobileNetV2 será mais lenta |

> O SVR não usa GPU. GPU acelera apenas a etapa de extração de features pelo MobileNetV2 (~10.654 imagens MPIIGaze). Após a extração, o treino dos modelos SVR-X e SVR-Y é inteiramente em CPU e leva segundos.

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
│   │   │   ├── *.jpg          ← imagens RGB (redimensionadas para 224×224px pelo DataLoader)
│   │   │   └── annotation.txt ← pose + vetor de olhar
│   │   └── ...
│   └── p14/
└── Evaluation Subset/         ← 10.654 amostras anotadas utilizadas pelo IrisFlow
```

> O dataset completo contém 213.658 imagens, mas apenas o **Evaluation Subset / Annotation Subset** (10.654 amostras) possui anotações de gaze utilizáveis para treinar os modelos SVR. O DataLoader carrega exclusivamente esse subconjunto.

### OpenEDS *(planejado — ainda não integrado)*

> **Status:** OpenEDS não está integrado ao pipeline atual do IrisFlow. Requer aprovação da Meta AI — aprovação ainda não obtida. As instruções abaixo servem de referência para quando a integração for implementada.

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
│   ├── pretrain.py            ← extrai features com MobileNetV2 + treina SVR-X e SVR-Y
│   ├── evaluate.py            ← métricas: MAE, acurácia de tecla, latência
│   ├── dataset.py             ← MPIIGaze DataLoader (Annotation Subset: 10.654 amostras)
│   ├── augmentation.py        ← pipeline Albumentations para ELA
│   ├── model.py               ← IrisGazeNet (MobileNetV2 como extrator + SVR)
│   └── config.yaml            ← hiperparâmetros centralizados
│
├── datasets/                  ← NÃO commitado (.gitignore)
│   ├── MPIIGaze/
│   └── OpenEDS/               ← planejado; não integrado ainda
│
└── models/                    ← NÃO commitado (.gitignore)
    ├── .gitkeep
    ├── svr_x_base.pkl         ← SVR-X gerado pelo pretrain.py
    └── svr_y_base.pkl         ← SVR-Y gerado pelo pretrain.py
```

---

## Hiperparâmetros

Arquivo: `training/config.yaml`

```yaml
# Backbone (extrator de features — congelado, NÃO treinado pela equipe)
backbone: mobilenet_v2
pretrained: true            # carrega pesos ImageNet do torchvision
backbone_frozen: true       # backbone permanece congelado durante todo o processo

# Vetor de entrada para o SVR
# features MobileNetV2(1280) — sem pose (MPIIGaze não fornece ângulos)
feature_dim: 1280

# SVR — algoritmo de ML treinado pela equipe
# Dois modelos separados: SVR-X (eixo horizontal) e SVR-Y (eixo vertical)
svr_kernel: rbf
svr_C: 10.0                 # parâmetro de regularização
svr_gamma: scale            # kernel RBF: 'scale' = 1 / (n_features * X.var())
svr_epsilon: 0.01           # margem de erro tolerada na regressão

# Split (Annotation Subset — 10.654 amostras anotadas)
# Treino: 9.067 | Validação: 972 | Teste: 615
split_train: 9067
split_val: 972
split_test: 615

# Augmentation
augmentation: true
ear_threshold: 0.15         # filtro anti-piscar
noise_sigma_px: 3           # microtremores oculares (σ em pixels)
brightness_limit: -0.4      # RandomBrightnessContrast
rotate_limit: 20            # Rotate (graus)
gauss_var_limit: [10, 50]   # GaussNoise

# Paths
dataset_mpii: datasets/MPIIGaze/
output_svr_x: models/svr_x_base.pkl
output_svr_y: models/svr_y_base.pkl
```

---

## Métricas de Avaliação

As métricas são calculadas pelo script `training/evaluate.py` sobre o conjunto de teste do MPIIGaze Annotation Subset (615 amostras, nunca vistas durante o treino).

| Métrica | Descrição | Meta |
|---------|-----------|------|
| MAE em pixels | Erro médio absoluto entre ponto predito e ponto real na tela | < 50px |
| Acurácia de tecla (grid 4×4) | % de acertos ao mapear coordenada predita para célula correta em grade 4 colunas × 4 linhas | ≥ 88% |
| Latência de inferência | Tempo médio de um forward pass completo (crop → MobileNetV2 → SVR → coordenada) em CPU i5 | < 30ms |

### Como interpretar os resultados

- **MAE < 50px** em monitor Full HD (1920×1080) equivale a aproximadamente 2,6% da largura da tela — suficiente para selecionar botões de 80px+.
- **Acurácia ≥ 88%** em grid 4×4 garante que o usuário erra menos de 1 tecla em cada 8 tentativas, compatível com uso assistivo.
- **Latência < 30ms** mantém o pipeline de inferência dentro do orçamento de um frame a 30fps (33ms), sem travar a UI.

---

## Fluxo de Execução

```bash
# 1. Instalar dependências (ambiente virtual recomendado)
pip install torch torchvision scikit-learn joblib albumentations opencv-python mediapipe numpy pandas matplotlib pyyaml

# 2. (Opcional) Verificar GPU disponível para extração de features mais rápida
python -c "import torch; print(torch.cuda.is_available())"

# 3. Executar pré-treino: extrai features com MobileNetV2 + treina SVR-X e SVR-Y
python training/pretrain.py --config training/config.yaml

# 4. Avaliar os modelos SVR gerados no conjunto de teste (615 amostras)
python training/evaluate.py --svr_x models/svr_x_base.pkl --svr_y models/svr_y_base.pkl
```

---

## Notas de Segurança e Privacidade

- Os datasets MPIIGaze e OpenEDS **não devem ser commitados** no repositório — estão no `.gitignore`.
- Modelos `.pkl` também ficam fora do git — os arquivos `svr_x_base.pkl` e `svr_y_base.pkl` serão distribuídos separadamente (release ou download automático).
- Dados de calibração dos pacientes (`profiles/{id}/svr_x.pkl` e `svr_y.pkl`) são armazenados apenas localmente no dispositivo do paciente — nunca enviados a servidores.
