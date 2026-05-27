# Roadmap IrisFlow MVP

**Meta:** demonstração para profissionais de saúde em julho/agosto 2026.
**Prazo final:** início de outubro de 2026.

## Fases concluídas

### Fase 1 ✅ — Base funcional
MockGazeEngine, UI base, dwell click, TTS via SAPI Windows

### Fase 2 ✅ — EyeTrax real
EyeTraxAdapter, calibração dense 7x7, cursor vermelho, Kalman EMA,
filtro Deadzone, detecção de qualidade de frame

### Fase 3 ✅ — Funcionalidades assistivas
Frases rápidas por contexto (JSON editável), teclado virtual,
perfis de usuário com modo cuidador via F10

### Fase 4 ✅ — Pipeline de ML próprio (IrisGazeNet)
- **IrisFeatureExtractor:** MobileNetV2 congelado, 0 parâmetros treináveis
- **IrisGazeEstimator:** SVR-X + SVR-Y (igual GazeFollower — Zhu et al., ACM CGIT 2025)
- **Dataset:** MPIIGaze Annotation Subset — 10.654 amostras (split 9.067 / 972 / 615)
- **Augmentation ELA (pipeline ELA):** 7 transformações — `low_light`, `noise`, `blur`,
  `shadow`, `rotate`, `flip`, `blink_simulation`
- **Pré-treino:** MAE 51,8px no val set, acurácia grid 4×4 100%
- **Avaliação formal test set:** MAE 22,7px, acurácia de botão 100%
- **IrisGazeNetAdapter** integrado como engine alternativa ao EyeTrax via `EngineFactory`
- **Comparativo formal** SVR vs Ridge Regression documentado em `docs/model_comparison.md`
- **ADR-020** (remoção de pose explícita) e **ADR-021** (remoção da MLP) adicionados

### Fase 5 ✅ — Frontend React + Electron
- Migração completa do PyQt6 para React 18 + Vite + Electron
- Design system Lumina (glassmorphism, dark mode clínico, Manrope)
- 4 telas convertidas do Stitch: Dashboard, Frases, Teclado, Calibração
- Componentes: GazeCursor, GazeButton, GlassPanel, SideNav, TopBar,
  EmergencyButton
- Hooks: useDwell (dwell click), useGazeSocket (WebSocket stub)
- Estado global: Zustand (activeMessage, dwellTime, isCalibrated)
- Electron configurado: spawn Python backend + BrowserWindow
- Mouse simula gaze enquanto WebSocket não conectado

### Fase 6 ✅ — Backend FastAPI + WebSocket
- irisflow/api/ criado com FastAPI + Uvicorn na porta 8765
- WebSocket /ws — stream bidirecional React ↔ Python
- REST /profiles, /phrases, /calibration implementados
- QApplication offscreen inicializado antes do FastAPI
  (necessário para DwellController com pyqtSignal)
- ConnectionManager singleton — broadcast para todos os clientes
- Reconexão automática no frontend a cada 3 segundos
- Mensagens implementadas:
    Frontend → Backend: start_tracking, stop_tracking, speak,
                        emergency, dwell_regions
    Backend → Frontend: gaze, dwell_progress, dwell_completed,
                        dwell_cancelled, tracking_status, error
- TTS via WebSocket funcionando — botão YES fala "Sim" ✅
- GazeSocketContext.jsx — provider React singleton

### Fase 7 ✅ — Integração completa React ↔ FastAPI (5 sistemas conectados)

#### TTS via backend (ADR-026)
- Removido `window.speechSynthesis` do Dashboard — substituído por `sendMessage('speak', { text })`
- Botões YES e NO falam "SIM" / "NÃO" via SAPI Windows
- QuickPhrases fala a frase selecionada via WebSocket

#### Dwell loop real com DwellController (ADR-027)
- Frontend registra bounding boxes dos botões via `registerDwellRegion(id, rect, onCompleted)`
- GazeSocketContext mantém mapa de regiões por ID e reenvia ao backend a cada mudança
- `TiltCard` em Dashboard.jsx registra automaticamente sua região ao montar
- Helper `clientToScreen()` converte coordenadas viewport → tela para o DwellController
- Correção crítica: sinais Qt usam `Qt.ConnectionType.DirectConnection` (ver ADR-027)

#### Calibração conectada ao backend
- Calibration.jsx chama `POST /calibration/start?engine=mock` no primeiro ponto
- Ao completar os 6 pontos: `setCalibrated(true)` no appStore → estado global atualizado

#### Estado unificado — fonte única de verdade (ADR-028)
- `isCalibrated` removido do GazeSocketContext; derivado diretamente do appStore
- `dwellTime` do appStore sincronizado ao backend via mensagem `set_dwell_time` ao conectar/mudar
- Novo handler `set_dwell_time` no backend + `DwellController.set_dwell_time(ms)` para atualização em runtime
- `activeMessage` lido do appStore no Dashboard (não existia no contexto WS)

#### Frases da API
- QuickPhrases.jsx busca `GET /phrases/categories` ao montar (24 frases PT-BR, 4 categorias)
- Mapeamento `CATEGORY_META` → ícones Material Symbols + cores Tailwind por categoria
- Frase selecionada atualiza ACTIVE MESSAGE no Dashboard e dispara TTS

## Próximas fases

### Fase 8 ⏳ — EyeTrax/IrisGazeNet conectado ao frontend
- TrackingService integrado ao WebSocket com engine real (não mock)
- Cursor de gaze ativo com dados de câmera real
- Calibração com IrisGazeNet via fluxo de 6 pontos existente

### Fase 10 ⏳ — Piloto clínico com AACD
- Parceria com AACD ou AME para 5-10 pacientes com ELA
- Protocolo de coleta com aprovação ética (CAAE)
- Fine-tuning com dados reais de ELA
- Dataset "IrisFlow-ELA-v1" documentado
- Recalibração automática semanal

### Fase 11 ⏳ — Regulação e negócio
- Consultor regulatório ANVISA RDC 657/2022 (SaMD Classe I)
- Log de auditoria imutável de sessões
- Política de Privacidade e Termos de Uso (LGPD Art. 11)
- TAM/SAM/SOM formalizado com dados do piloto
- CAC/LTV calculado com primeiros 10 clientes

### Fase 12 ⏳ — Empacotamento .exe Windows
- Electron Builder → instalador .exe Windows
- Landing page de vendas
- Submissão FAPESP PIPE
- Pitch com métricas reais de 5+ pacientes

## Matriz de riscos prioritários

| Risco | Nível | Mitigação |
|---|---|---|
| Modelo não atinge 92% em ELA real | 🔴 P1 | Dados reais AACD + augmentation ELA |
| Latência >30ms em hardware básico | 🟠 P2 | ONNX + INT8 antes do beta |
| Exigência ANVISA antes de clínicas | 🟠 P3 | Consultor desde Fase 11 |
| Concorrente lança antes do MVP | 🟡 P4 | Acelerar beta + fortalecer AACD |
| ELA progressiva — modelo não acompanha | 🟡 P6 | Recalibração semanal automática |
