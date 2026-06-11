# IrisFlow — Arquitetura de Machine Learning

## Visão Geral

O IrisFlow implementa um pipeline de gaze estimation em três fases, inspirado na arquitetura do GazeFollower (Zhu et al., ACM CGIT 2025).

O pipeline é chamado **IrisGazeNet**. O **algoritmo de Machine Learning treinado pela equipe é o SVR (Support Vector Regression)** — dois modelos separados, SVR-X e SVR-Y, que mapeiam um vetor de features visuais para coordenadas de tela. O MobileNetV2 é utilizado apenas como extrator de features pré-treinado (pesos ImageNet, congelados) — a equipe não treina o backbone.

---

## Fluxo Completo

### Fase 1 — Pré-treino offline (CONCLUÍDO ✅)

| Item | Detalhe |
|------|---------|
| Dataset | MPIIGaze — Annotation Subset: **10.654 amostras** (de 213.658 imagens totais) |
| Backbone | MobileNetV2 pré-treinado em ImageNet (congelado — não treinado pela equipe) |
| Algoritmo de ML | **SVR-X e SVR-Y** — treinados nas 9.067 amostras de treino |
| Split | Treino: 9.067 / Validação: 972 / Teste: 615 |
| Output | `models/irisflow_base_model.pkl` |
| Ambiente | CPU suficiente — SVR treina em segundos |
| Script | `training/pretrain.py` |
| **MAE val set** | **51,8px** (participantes p12–p13, 972 amostras) |
| **MAE test set** | **22,7px** (participante p14, 615 amostras — nunca visto no treino) |
| **Acurácia de botão** | **100%** em ambos os conjuntos (erro < 110px) |

O backbone MobileNetV2 extrai um vetor de **1.280 features** do crop do olho (224×224px, RGB). Esse vetor de 1.280 dimensões é usado diretamente como entrada para os modelos SVR.

> **Nota sobre pose:** O MPIIGaze Annotation Subset não fornece ângulos de pitch/yaw — apenas landmarks faciais em pixels, sem ângulos em radianos. A calibração individual por paciente captura implicitamente a pose típica do usuário no seu setup físico, tornando a pose explícita desnecessária. Ver ADR-020.

### Fase 2 — Fine-tuning por paciente (implementado — aguarda teste clínico real)

| Item | Detalhe |
|------|---------|
| Dados | ~200 amostras coletadas durante calibração (~60 segundos) |
| Backbone | MobileNetV2 (congelado) — extrai features do crop do olho |
| Algoritmo | **SVR-X e SVR-Y** — retreinados com os dados de calibração do paciente |
| Output | `irisflow/profiles/{profile_id}/svr_x.pkl` e `svr_y.pkl` |
| Ambiente | On-device, durante a tela de calibração do IrisFlow |
| Tempo de treino | < 5 segundos em Intel i5 sem GPU |

`IrisGazeNetAdapter.calibrate()` implementado — coleta amostras durante calibração, treina SVR-X e SVR-Y, salva modelo personalizado por perfil.

### Fase 3 — Inferência em tempo real (implementado ✅)

`IrisGazeNetAdapter._capture_loop()` operacional. MediaPipe detecta face → crop do olho → MobileNetV2 → SVR → GazePoint.

```
Webcam
  → frame (BGR)
  → MediaPipe Face Mesh (478 landmarks)
  → crop 224×224 do olho esquerdo (RGB)
  → MobileNetV2 (congelado) → vetor 1.280 features
  → SVR-X → x_norm ∈ [0.0, 1.0]
  → SVR-Y → y_norm ∈ [0.0, 1.0]
  → desnormalizar: x = x_norm × screen_width
                   y = y_norm × screen_height
  → Deadzone (12px, 25 frames)
  → GazePoint
  → DwellController
```

**Meta de latência:** < 30ms por frame em hardware comum (Intel i5 + 8GB RAM, sem GPU).

---

## Resultados Medidos (Maio 2026)

Avaliação formal realizada pelo script `training/evaluate.py` sobre o MPIIGaze Annotation Subset (participante p14, 615 amostras — nunca vistas durante treino ou validação).

| Conjunto | Modelo | MAE total | MAE-X | MAE-Y | Acurácia botão |
|---|---|---|---|---|---|
| Validação (p12–p13, 972 amostras) | SVR (IrisGazeNet) | 51,8px | 40,4px | 24,9px | 100% |
| Teste (p14, 615 amostras) | SVR (IrisGazeNet) | 22,7px | 14,0px | 14,4px | 100% |
| Teste (p14, 615 amostras) | Ridge Regression (baseline) | 20,2px | 16,8px | 8,2px | 100% |

**Acurácia de botão:** proporção de predições com erro < 110px (tamanho mínimo dos botões da interface IrisFlow).  
**Comparativo formal** SVR vs Ridge Regression documentado em `docs/model_comparison.md`.

---

## Por que SVR

- **Robusto com poucos dados:** SVR com kernel RBF generaliza bem com ~200 amostras — exatamente o volume coletado em 60 segundos de calibração. Modelos neurais exigiriam ordens de magnitude mais dados para convergir.
- **Treino rápido on-device:** SVR treina em segundos em CPU comum (Intel i5), viabilizando re-calibração a qualquer momento sem GPU.
- **Dois modelos independentes (SVR-X e SVR-Y):** Permite otimização e debug independentes de cada eixo — padrão adotado pelo GazeFollower.
- **Comparável ao baseline:** O baseline de comparação usa Ridge Regression — mesma família de modelos lineares generalizados; o SVR com kernel RBF é o próximo passo natural, adicionando capacidade não-linear.
- **Sem risco de overfitting na calibração:** Com backbone congelado e SVR treinado em ~200 pontos, o modelo pessoal do paciente não colapsa por excesso de capacidade.
- **Desempenho equivalente ao baseline:** Resultados medidos confirmam que SVR e Ridge Regression têm desempenho equivalente no test set independente (diferença de 2,5px — 22,7px vs 20,2px). O diferencial do SVR está na personalização por paciente via calibração individual — não no modelo base genérico.

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
| Anotações | landmarks faciais (pixel) + vetor de olhar (gaze_x, gaze_y) |
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
├── irisflow/integrations/irisgazenet/     ← adapter do modelo próprio (produção)
│   └── adapter.py                         ← IrisGazeNetAdapter ✅
│
├── irisflow/integrations/eyetrax/         ← código legacy (removido do pipeline)
│   └── adapter.py                         ← EyeTraxAdapter (inalcançável via factory)
│
└── irisflow/profiles/{profile_id}/
    ├── svr_x.pkl                          ← SVR-X calibrado por paciente
    └── svr_y.pkl                          ← SVR-Y calibrado por paciente
```

---

## Engine de Produção

O `IrisGazeNetAdapter` é a engine de produção do IrisFlow. O `EyeTraxAdapter` foi removido do `EngineFactory` — qualquer chamada com `engine_type="eyetrax"` retorna o `MockGazeEngine` com aviso de log.

Para selecionar a engine via configuração:

```yaml
tracking_engine: mock        # desenvolvimento (padrão)
tracking_engine: irisgazenet # produção — MobileNetV2 + SVR
```

A mudança de engine não requer alteração de código na UI — apenas a chave de configuração.

---

## Referências

- **GazeFollower:** Zhu et al., "GazeFollower: Real-Time Gaze Estimation via Multi-Stage Learning", ACM CGIT 2025
- **MPIIGaze:** Zhang et al., "Appearance-Based Gaze Estimation in the Wild", CVPR 2015
- **MobileNetV2:** Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks", CVPR 2018
- **OpenEDS:** Garbin et al., "OpenEDS: Open Eye Dataset", Meta AI / arXiv 2019
