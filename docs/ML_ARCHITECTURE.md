# IrisFlow — Arquitetura de Machine Learning

## Visão Geral

O IrisFlow implementa um pipeline de gaze estimation em três fases, inspirado na arquitetura do GazeFollower (Zhu et al., ACM CGIT 2025), porém com modelo próprio treinado do zero pela equipe IrisFlow.

O modelo é chamado **IrisGazeNet** e combina um backbone MobileNetV2 pré-treinado em ImageNet com uma MLP de três camadas para mapear features visuais do olho + pose da cabeça em coordenadas de tela normalizadas.

---

## Fluxo Completo

### Fase 1 — Pré-treino offline (executado uma vez pela equipe)

| Item | Detalhe |
|------|---------|
| Datasets | MPIIGaze (213.658 amostras) + OpenEDS (12.759 imagens) |
| Backbone | MobileNetV2 pré-treinado em ImageNet |
| MLP | features(1280) + pose(3) → 256 → 64 → 2 (x\_norm, y\_norm) |
| Output | `models/irisflow_base_model.pt` |
| Ambiente | GPU recomendada (Google Colab T4 ou local ≥ GTX 1060 6GB) |
| Script | `training/pretrain.py` |

O backbone MobileNetV2 extrai um vetor de 1280 features do crop do olho. Esse vetor é concatenado com os 3 ângulos de pose da cabeça (yaw, pitch, roll) fornecidos pelo MediaPipe Face Mesh, resultando em um vetor de entrada de 1283 dimensões para a MLP.

### Fase 2 — Fine-tuning por paciente (executado na calibração)

| Item | Detalhe |
|------|---------|
| Dados | ~200 amostras coletadas durante calibração (~60 segundos) |
| Base | Modelo `irisflow_base_model.pt` carregado e fine-tuned |
| Learning rate | 1e-4 (baixo, para preservar o pré-treino) |
| Epochs | 20 |
| Output | `irisflow/profiles/{profile_id}/gaze_model.pt` |
| Ambiente | On-device, durante a tela de calibração do IrisFlow |

O fine-tuning adapta os pesos da MLP às características individuais do paciente (geometria facial, postura habitual, iluminação do ambiente). O backbone permanece congelado nesta fase para evitar overfitting com poucas amostras.

### Fase 3 — Inferência em tempo real

```
Webcam
  → frame (BGR)
  → MediaPipe Face Mesh
  → crop 224×224 do olho esquerdo/direito
  → MobileNetV2 → vetor 1280 features
  → concat pose (yaw, pitch, roll) → vetor 1283
  → MLP → (x_norm, y_norm) ∈ [0.0, 1.0]
  → desnormalizar: x = x_norm × screen_width
                   y = y_norm × screen_height
  → Deadzone (12px, 25 frames)
  → Kalman EMA (α=0.2)
  → GazePoint
  → DwellController
```

**Meta de latência:** < 30ms por frame em hardware comum (Intel i5 + 8GB RAM, sem GPU).

---

## Por que MobileNetV2 + MLP

- **Transfer learning de ImageNet** elimina a necessidade de treinar um backbone do zero — economiza semanas de GPU e dados.
- **Inference < 10ms em CPU** comum — MobileNetV2 foi projetado para edge/mobile, adequado ao hardware dos pacientes.
- **Arquitetura validada** em literatura de gaze estimation; complexidade comparável ao MGazeNet do GazeFollower.
- **Fine-tuning simples** — congelar o backbone e retreinar apenas a MLP é seguro com poucas amostras de calibração.
- **Footprint pequeno** — modelo `.pt` < 20MB, adequado para distribuição embutida no instalador.

---

## Datasets

### MPIIGaze — Max Planck Institute

| Atributo | Valor |
|----------|-------|
| Amostras | 213.658 |
| Participantes | 15 (25 dias cada) |
| Formato de imagem | 36×60px, escala de cinza |
| Anotações | pose da cabeça (3 ângulos) + vetor de olhar (yaw, pitch) |
| Uso no IrisFlow | Treino principal do mapeamento olhar → coordenada de tela |
| Referência | Zhang et al., CVPR 2015 |

### OpenEDS — Meta AI

| Atributo | Valor |
|----------|-------|
| Imagens | 12.759 anotadas pixel a pixel |
| Anotações | Segmentação de íris, pupila e esclera |
| Uso no IrisFlow | Pré-treino da localização da íris no backbone (Fase 1) |
| Acesso | Requer aprovação: https://ai.meta.com/datasets/open-eds/ |
| Referência | Garbin et al., Meta AI 2019 |

---

## Augmentation para ELA

Pacientes com ELA têm padrões oculares específicos que os datasets públicos não cobrem adequadamente. As seguintes transformações são aplicadas durante o pré-treino para aproximar o domínio:

| Transformação | Parâmetro | Motivação |
|---------------|-----------|-----------|
| Filtro anti-piscar | Descartar frames com EAR < 0.15 | Pacientes com ELA piscam menos e com menor amplitude |
| Microtremores oculares | Ruído gaussiano σ=2–5px nas coordenadas | Simula tremor involuntário característico da condição |
| Baixa iluminação | `RandomBrightnessContrast(limit=-0.4)` | Ambientes domésticos com iluminação irregular |
| Posições extremas de cabeça | `Rotate(limit=20°)` | Postura reclinada em cadeira de rodas elétrica |
| Webcam de baixo custo | `GaussNoise(var_limit=(10,50))` | Hardware de entrada (< R$ 100) usado por famílias |

Todas as transformações são implementadas com a biblioteca **Albumentations** em `training/augmentation.py`.

---

## Separação de Responsabilidades

```
irisflow-mvp/
├── training/                              ← ambiente offline, requer GPU
│   ├── pretrain.py                        ← pré-treino nos datasets públicos
│   ├── finetune.py                        ← fine-tuning de teste offline
│   ├── evaluate.py                        ← métricas: MAE, acurácia de tecla
│   ├── dataset.py                         ← DataLoader MPIIGaze + OpenEDS
│   ├── augmentation.py                    ← pipeline Albumentations
│   ├── model.py                           ← IrisGazeNet (MobileNetV2 + MLP)
│   └── config.yaml                        ← hiperparâmetros
│
├── irisflow/integrations/irisgazenet/     ← adapter do modelo próprio
│   └── adapter.py                         ← IrisGazeNetAdapter (futuro)
│
├── irisflow/integrations/eyetrax/         ← mantido como fallback
│   └── adapter.py                         ← EyeTraxAdapter (atual/padrão)
│
└── irisflow/profiles/{profile_id}/
    └── gaze_model.pt                      ← modelo fine-tuned por paciente
```

---

## Decisão de Fallback

Durante o MVP, enquanto o modelo próprio está sendo desenvolvido, o `EyeTraxAdapter` permanece como engine padrão. A troca será feita via `EngineFactory` no arquivo de configuração do perfil:

```yaml
# perfil atual (fallback)
tracking_engine: eyetrax

# perfil futuro (após validação do IrisGazeNet)
tracking_engine: irisgazenet
```

A mudança de engine não requer alteração de código na UI — apenas a chave de configuração.

---

## Referências

- **GazeFollower:** Zhu et al., "GazeFollower: Real-Time Gaze Estimation via Multi-Stage Learning", ACM CGIT 2025
- **MPIIGaze:** Zhang et al., "Appearance-Based Gaze Estimation in the Wild", CVPR 2015
- **MobileNetV2:** Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks", CVPR 2018
- **OpenEDS:** Garbin et al., "OpenEDS: Open Eye Dataset", Meta AI / arXiv 2019
