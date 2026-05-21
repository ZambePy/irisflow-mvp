# Arquitetura IrisFlow

## Visão geral

```
┌─────────────────────────────────────────┐
│              IrisFlow UI                │
│  (PyQt6 — screens, components, theme)  │
└────────────────┬────────────────────────┘
                 │ GazePoint, eventos
┌────────────────▼────────────────────────┐
│          Accessibility Layer            │
│   DwellController · RegionMapper        │
│   FixationDetector · FeedbackManager    │
└────────────────┬────────────────────────┘
                 │ GazePoint stream
┌────────────────▼────────────────────────┐
│            TrackingService              │
│    (gerencia engine, emite eventos)     │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼────────┐
         │  EngineFactory │
         └───┬────────┬───┘
             │        │
    ┌────────▼──┐  ┌──▼──────────────┐
    │ MockGaze  │  │ EyeTraxAdapter  │
    │  Engine   │  │ (isolado aqui)  │
    └───────────┘  └────────┬────────┘
                            │
                     ┌──────▼──────┐
                     │   EyeTrax   │
                     │  (3rd party)│
                     └─────────────┘
```

## Pipeline de Processamento

```
Webcam (30fps)
  → MediaPipe Face Mesh (478 landmarks)
    → Extração de features oculares (EyeTrax GazeEstimator)
      → Ridge Regression (modelo treinado na calibração)
        → Deadzone Filter (radius=12px, threshold=25 frames)
          → Kalman EMA (α=0.2)
            → GazePoint (x, y, confidence)
              → DwellController (1000ms)
                → Ação + TTS
```

> Esta é a arquitetura canônica v1.0 do IrisFlow MVP (EyeTrax como engine padrão).
> O IrisGazeNet (MobileNetV2 como extrator + SVR como algoritmo de ML treinado) está em desenvolvimento como engine própria — ver `docs/ML_ARCHITECTURE.md`, ADR-017 e ADR-019.

## Decisão de Arquitetura — Engine padrão vs IrisGazeNet

O IrisFlow MVP utiliza MediaPipe + Ridge Regression (via EyeTrax) como engine padrão na v1.0, priorizando velocidade de entrega e funcionamento comprovado em hardware comum. O modelo próprio **IrisGazeNet** usa MobileNetV2 como extrator de features (pré-treinado ImageNet, congelado) e **SVR (Support Vector Regression)** como algoritmo de ML treinado pela equipe — dois modelos separados (SVR-X e SVR-Y), inspirados no GazeFollower (Zhu et al., ACM CGIT 2025). CNN treinada do zero e LSTM não fazem parte do pipeline. Ver ADR-014, ADR-017 e ADR-019.

## Tipos próprios do IrisFlow

- `GazePoint` — ponto de olhar (x, y, confiança, timestamp)
- Nunca expor classes do EyeTrax fora de `integrations/eyetrax/`

## Camadas

| Camada | Responsabilidade |
|---|---|
| `ui/` | Renderização, interação visual |
| `accessibility/` | Dwell click, detecção de fixação, mapeamento de regiões |
| `tracking/` | Abstração do motor de rastreamento |
| `integrations/eyetrax/` | Adaptador isolado para EyeTrax |
| `speech/` | TTS e fila de fala |
| `profiles/` | Perfis de usuário locais |
| `core/` | Config, eventos, estado global, logger |
