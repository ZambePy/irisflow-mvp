# Arquitetura IrisFlow

## Arquitetura completa atual

```
Electron (shell desktop)
  → React App (Vite, porta 5173)
    → GazeSocketContext (WebSocket singleton)
      → ws://localhost:8765/ws
        → FastAPI (irisflow/api/main.py)
          → QApplication offscreen (necessário para Qt signals)
          → ConnectionManager (broadcast para todos os clientes)
          → TrackingService → IrisGazeNet | Mock
          → DwellController (pyqtSignal → asyncio bridge)
          → TTSEngine (SAPI Windows via PowerShell)
          → ProfileStore (JSON local)
          → PhrasesStore (JSON local)
```

## Portas e endpoints

| Serviço | Porta | Protocolo |
|---|---|---|
| Backend FastAPI | 8765 | HTTP + WebSocket |
| Frontend Vite (dev) | 5173 | HTTP |
| Frontend Electron (prod) | arquivo local | file:// |

## Engines disponíveis

| Engine | Como ativar | Status |
|---|---|---|
| mock | config.tracking_engine = "mock" | ✅ Padrão dev |
| irisgazenet | config.tracking_engine = "irisgazenet" | ✅ Produção |
| eyetrax | config.tracking_engine = "eyetrax" | ❌ Removido (retorna mock com aviso) |

## Visão geral (backend Python)

```
┌─────────────────────────────────────────┐
│              IrisFlow UI                │
│  (React 18 + Electron — Fase 5+)       │
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
    ┌────────▼──┐  ┌──▼──────────────────┐
    │ MockGaze  │  │ IrisGazeNetAdapter  │
    │  Engine   │  │   (modelo próprio)  │
    └───────────┘  └─────────────────────┘
```

## Pipeline de Processamento

```
Webcam (30fps)
  → MediaPipe Face Mesh (478 landmarks)
    → Crop do olho esquerdo (224×224px)
      → MobileNetV2 (congelado) → vetor 1.280 features
        → SVR-X + SVR-Y (calibração por paciente)
          → Deadzone Filter (radius=12px, threshold=25 frames)
            → GazePoint (x, y, confidence)
              → DwellController (1000ms)
                → Ação + TTS
```

> Pipeline principal do IrisFlow MVP com IrisGazeNet como engine de produção. Ver `docs/ML_ARCHITECTURE.md`.

### Engine IrisGazeNet (alternativa — modelo próprio IrisFlow)

```
Webcam (30fps)
  → MediaPipe Face Mesh (478 landmarks)
    → Crop do olho esquerdo (224×224px)
      → IrisFeatureExtractor / MobileNetV2 (congelado)
        → vetor 1.280 features
          → SVR-X + SVR-Y (treinados no MPIIGaze — MAE 22,7px)
            → (x, y) em pixels
              → Deadzone (12px, 25 frames)
                → GazePoint
                  → DwellController
```

Para usar: `config.tracking_engine = "irisgazenet"`  
Modelo base: `models/irisflow_base_model.pkl`  
Documentação completa: `docs/ML_ARCHITECTURE.md`

### Engines disponíveis

| Engine | Algoritmo de ML | Quando usar |
|---|---|---|
| `mock` | nenhum (mouse) | desenvolvimento |
| `irisgazenet` | SVR (IrisFlow — modelo próprio) | produção |

## Decisão de Arquitetura — Engine de produção

O IrisFlow MVP utiliza o **IrisGazeNet** como engine de produção — MobileNetV2 como extrator de features (pré-treinado ImageNet, congelado) e **SVR (Support Vector Regression)** como algoritmo de ML treinado pela equipe — dois modelos separados (SVR-X e SVR-Y), inspirados no GazeFollower (Zhu et al., ACM CGIT 2025). CNN treinada do zero e LSTM não fazem parte do pipeline. Ver ADR-014, ADR-017 e ADR-019.

## Tipos próprios do IrisFlow

- `GazePoint` — ponto de olhar (x, y, confiança, timestamp)
- Nunca expor classes internas dos adapters fora de `integrations/`

## Camadas

| Camada | Responsabilidade |
|---|---|
| `ui/` | Renderização, interação visual |
| `accessibility/` | Dwell click, detecção de fixação, mapeamento de regiões |
| `tracking/` | Abstração do motor de rastreamento |
| `integrations/irisgazenet/` | Adaptador do modelo próprio IrisGazeNet (SVR + MobileNetV2) |
| `speech/` | TTS e fila de fala |
| `profiles/` | Perfis de usuário locais |
| `core/` | Config, eventos, estado global, logger |
