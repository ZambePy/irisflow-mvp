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

> Esta é a arquitetura canônica v1.0 do IrisFlow MVP.
> CNN/LSTM são considerados para versões futuras após coleta de dados reais de pacientes com ELA.

## Decisão de Arquitetura — CNN vs LSTM

O IrisFlow MVP utiliza MediaPipe + Ridge Regression como arquitetura canônica v1.0. Esta decisão prioriza velocidade de entrega e funcionamento comprovado em hardware comum. CNN (MobileNetV2) e LSTM são planejados para v2.0 após coleta de dados reais de pacientes com ELA em parceria com instituições como AACD. Ver ADR-014.

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
