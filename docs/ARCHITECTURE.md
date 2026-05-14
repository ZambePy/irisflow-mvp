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
