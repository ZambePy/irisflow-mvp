# IrisFlow — Arquitetura de Machine Learning

## Visão Geral

O IrisFlow implementa um pipeline de gaze estimation em três fases, inspirado na arquitetura do GazeFollower (Zhu et al., ACM CGIT 2025).

O pipeline é chamado **IrisGazeNet**. O **algoritmo de Machine Learning treinado pela equipe é o SVR (Support Vector Regression)** — dois modelos separados, SVR-X e SVR-Y, que mapeiam um vetor de features visuais para coordenadas de tela. O MobileNetV2 é utilizado apenas como extrator de features pré-treinado (pesos ImageNet, congelados) — a equipe não treina o backbone.

---

## Fluxo Completo

### Fase 1 — Pré-treino offline (executado uma vez pela equipe)

| Item | Detalhe |
|------|---------|
| Dataset | MPIIGaze — Annotation Subset: **10.654 amostras** (de 213.658 imagens totais) |
| Backbone | MobileNetV2 pré-treinado em ImageNet (congelado — não treinado pela equipe) |
| Algoritmo de ML | **SVR-X e SVR-Y** — treinados nas 9.067 amostras de treino |
| Split | Treino: 9.067 / Validação: 972 / Teste: 615 |
| Output | `models/svr_x_base.pkl` e `models/svr_y_base.pkl` |
| Ambiente | CPU suficiente — SVR treina em segundos |
| Script | `training/pretrain.py` |

O backbone MobileNetV2 extrai um vetor de 1.280 features do crop do olho (224×224px, RGB). Esse vetor é concatenado com os 3 ângulos de pose da cabeça (yaw, pitch, roll) fornecidos pelo MediaPipe Face Mesh, resultando em um vetor de entrada de 1.283 dimensões para os modelos SVR.

### Fase 2 — Calibração por paciente (executado no dispositivo)

| Item | Detalhe |
|------|---------|
| Dados | ~200 amostras coletadas durante calibração (~60 segundos) |
| Backbone | MobileNetV2 (congelado) — extrai features do crop do olho |
| Algoritmo | **SVR-X e SVR-Y** — retreinados com os dados de calibração do paciente |
| Output | `irisflow/profiles/{profile_id}/svr_x.pkl` e `svr_y.pkl` |
| Ambiente | On-device, durante a tela de calibração do IrisFlow |
| Tempo de treino | < 5 segundos em Intel i5 sem GPU |

O SVR é retreinado inteiramente com os dados de calibração de cada paciente. O backbone permanece congelado — não há retropropagação nem ajuste de pesos de rede neural.

### Fase 3 — Inferência em tempo real

```
Webcam
  → frame (BGR)
  → MediaPipe Face Mesh (478 landmarks)
  → crop 224×224 do olho esquerdo/direito (RGB)
  → MobileNetV2 (congelado) → vetor 1.280 features
  → concat pose (yaw, pitch, roll) → vetor 1.283
  → SVR-X → x_norm ∈ [0.0, 1.0]
  → SVR-Y → y_norm ∈ [0.0, 1.0]
  → desnormalizar: x = x_norm × screen_width
                   y = y_norm × screen_height
  → Deadzone (12px, 25 frames)
  → Kalman EMA (α=0.2)
  → GazePoint
  → DwellController
```

**Meta de latência:** < 30ms por frame em hardware comum (Intel i5 + 8GB RAM, sem GPU).

---

## Por que SVR

- **Robusto com poucos dados:** SVR com kernel RBF generaliza bem com ~200 amostras — exatamente o volume coletado em 60 segundos de calibração. Modelos neurais exigiriam ordens de magnitude mais dados para convergir.
- **Treino rápido on-device:** SVR treina em segundos em CPU comum (Intel i5), viabilizando re-calibração a qualquer momento sem GPU.
- **Dois modelos independentes (SVR-X e SVR-Y):** Permite otimização e debug independentes de cada eixo — padrão adotado pelo GazeFollower.
- **Comparável ao baseline:** O EyeTrax usa Ridge Regression para calibração; o SVR é a escolha natural como próximo passo — mesma família de modelos lineares generalizados, com kernel não-linear como vantagem.
- **Sem risco de overfitting na calibração:** Com backbone congelado e SVR treinado em ~200 pontos, o modelo pessoal do paciente não colapsa por excesso de capacidade.

---

## Por que MobileNetV2 como backbone

- **Transfer learning de ImageNet** elimina a necessidade de treinar um backbone do zero — economiza semanas de GPU e dados.
- **Inference < 10ms em CPU** comum — projetado para edge/mobile, adequado ao hardware dos pacientes.
- **Footprint pequeno** — pesos < 14MB, adequado para distribuição embutida no instalador.
- **Separação clara de responsabilidades:** backbone extrai features visuais (pré-treinado), SVR aprende o mapeamento olhar → tela (treinado pela equipe).

---

## Inspiração — GazeFollower

A modelagem de ML do IrisFlow é inspirada no GazeFollower (Zhu et al., ACM CGIT 2025), que usa um backbone CNN para extração de features seguido de SVR para calibração personalizada. O IrisFlow replica essa abordagem com backbone próprio (MobileNetV2) e SVR, sem usar o modelo proprietário MGazeNet de 32M imagens do GazeFollower (licença não-comercial).

A principal diferença é de escala: o GazeFollower pré-treina o MGazeNet com 32 milhões de imagens e usa o SVR apenas para calibração final. O IrisFlow usa o MobileNetV2 (pré-treinado em ImageNet) e treina o SVR tanto no MPIIGaze Annotation Subset (9.067 amostras de treino) quanto na calibração individual (~200 amostras).

---

## Datasets

### MPIIGaze — Max Planck Institute

| Atributo | Valor |
|----------|-------|
| Imagens totais | 213.658 |
| **Amostras anotadas (Annotation Subset)** | **10.654** |
| Split (Annotation Subset) | Treino: 9.067 / Validação: 972 / Teste: 615 |
| Participantes | 15 (25 dias cada) |
| Formato de imagem | RGB, redimensionadas para **224×224px** antes do MobileNetV2 |
| Anotações | pose da cabeça (3 ângulos) + vetor de olhar (yaw, pitch) |
| Uso no IrisFlow | Treino dos SVR base (SVR-X e SVR-Y offline) |
| Referência | Zhang et al., CVPR 2015 |

> O dataset completo tem 213.658 imagens, mas apenas o **Annotation Subset** (10.654 amostras) possui anotações de gaze utilizáveis para treinar os modelos SVR. Os números de treino/validação/teste referem-se exclusivamente ao Annotation Subset.

### OpenEDS — Meta AI *(planejado — ainda não integrado)*

| Atributo | Valor |
|----------|-------|
| Imagens | 12.759 anotadas pixel a pixel |
| Anotações | Segmentação de íris, pupila e esclera |
| Status | **Planejado — requer aprovação da Meta. Não integrado ao pipeline atual.** |
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
├── training/                              ← ambiente offline, CPU suficiente
│   ├── pretrain.py                        ← treino do SVR base no MPIIGaze
│   ├── evaluate.py                        ← métricas: MAE, acurácia de tecla
│   ├── dataset.py                         ← DataLoader MPIIGaze
│   ├── augmentation.py                    ← pipeline Albumentations
│   ├── model.py                           ← IrisGazeNet (MobileNetV2 + SVR)
│   └── config.yaml                        ← hiperparâmetros
│
├── irisflow/integrations/irisgazenet/     ← adapter do modelo próprio
│   └── adapter.py                         ← IrisGazeNetAdapter (futuro)
│
├── irisflow/integrations/eyetrax/         ← mantido como fallback
│   └── adapter.py                         ← EyeTraxAdapter (atual/padrão)
│
└── irisflow/profiles/{profile_id}/
    ├── svr_x.pkl                          ← SVR-X calibrado por paciente
    └── svr_y.pkl                          ← SVR-Y calibrado por paciente
```

---

## Decisão de Fallback

Durante o MVP, enquanto o modelo próprio está sendo validado, o `EyeTraxAdapter` permanece como engine padrão. A troca será feita via `EngineFactory` no arquivo de configuração do perfil:

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
