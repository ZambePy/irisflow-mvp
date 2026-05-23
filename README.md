# IrisFlow MVP

> Plataforma assistiva de comunicação por rastreamento ocular para pessoas com ELA, tetraplegia e limitações motoras severas.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![React](https://img.shields.io/badge/UI-React%2018%20%2B%20Electron-61DAFB?logo=react) ![EyeTrax](https://img.shields.io/badge/EyeTrax-0.4-orange) ![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows)

---

## O que é o IrisFlow?

O IrisFlow permite que pessoas com mobilidade extremamente reduzida se comuniquem usando apenas o olhar — via webcam comum, sem hardware especializado.

O foco do MVP é:
- Seleção confiável por olhar (dwell click com filtro kalman_ema)
- Botões grandes e de alto contraste
- Painel Sim/Não instantâneo
- Frases rápidas por contexto editáveis em JSON (dois níveis)
- Teclado virtual completo com botão FALAR
- Text-to-speech em português (SAPI / pyttsx3)
- Botão de emergência
- Perfis locais por usuário (último perfil carregado automaticamente)
- Modo cuidador via F10 (configuração sem gaze)
- Calibração dense grid 7×7
- Baixa fadiga ocular

---

## Equipe

| Nome | Cargo |
|---|---|
| Gabriel Zambe | CEO e Desenvolvedor Full-Stack |
| Marcus Vinicius | CTO e Desenvolvedor Full-Stack |
| Vinicius Ferreira | CFO e Diretor de Marketing |

---

## Arquitetura

```
IrisFlow UI
  → Accessibility Layer (dwell, fixation, region mapper)
    → TrackingService
      → BaseGazeEngine
        → EyeTraxAdapter → EyeTrax  (produção)
        → MockGazeEngine             (desenvolvimento / mouse)
```

O EyeTrax é apenas o motor mecânico. A interface, lógica assistiva e experiência do usuário são 100% IrisFlow.

---

## Como rodar

### Frontend (desenvolvimento)

```bash
cd frontend
npm install
npm run dev        # abre no navegador em localhost:5173
```

### App desktop (Electron)

```bash
cd frontend
npm run electron:dev   # abre como aplicativo desktop
```

### Backend Python (em breve)

```bash
python -m irisflow.api.main
```

### Ambiente Python (pipeline ML e engine de tracking)

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Como testar o dwell click (modo desenvolvimento)

- O mouse simula o olhar enquanto o WebSocket não está conectado
- Mova o mouse sobre um botão e mantenha parado por **1 segundo**
- O botão é ativado automaticamente com feedback de progresso visual

---

## Stack

| Componente | Tecnologia |
|---|---|
| Frontend | React 18 + Vite + Electron |
| UI Design | Tailwind CSS + Glassmorphism (design Lumina) |
| Comunicação | WebSocket (FastAPI ↔ React) |
| Eye tracking | EyeTrax 0.4 (via adapter) / MockGazeEngine |
| ML / Gaze Estimation | MobileNetV2 (extrator) + SVR (scikit-learn) |
| TTS | pyttsx3 + SAPI (Windows) |
| Perfis | JSON local |
| Python | 3.11 |
| Empacotamento futuro | PyInstaller (.exe Windows) |

---

## Modelo de ML

O IrisFlow implementa o **IrisGazeNet** — pipeline de gaze estimation próprio treinado pela equipe:

- **Arquitetura:** MobileNetV2 (backbone congelado, extrator de 1.280 features) + SVR-X e SVR-Y (scikit-learn)
- **Inspiração:** GazeFollower (Zhu et al., ACM CGIT 2025)
- **Dataset de pré-treino:** MPIIGaze Annotation Subset — 10.654 amostras (split 9.067 / 972 / 615)
- **MAE no test set independente (p14):** 22,7px
- **Acurácia de botão:** 100% (erro < 110px — tamanho mínimo dos botões da interface)

```bash
# Treinar o modelo base
python training/pretrain.py

# Avaliar e comparar com Ridge Regression (baseline EyeTrax)
python training/evaluate.py
```

Para usar o IrisGazeNet como engine de rastreamento, configure `config.tracking_engine = "irisgazenet"`.

---

## Estrutura de pastas

```
irisflow-mvp/
├── frontend/
│   ├── src/
│   │   ├── components/    # GazeCursor, GazeButton, GlassPanel, SideNav, TopBar, EmergencyButton
│   │   ├── screens/       # Dashboard, Frases, Teclado, Calibração
│   │   ├── hooks/         # useDwell, useGazeSocket
│   │   ├── store/         # Zustand (activeMessage, dwellTime, isCalibrated)
│   │   └── theme/         # lumina.js — tokens de design (cores, tipografia, espaçamento)
│   ├── electron/          # main.js — BrowserWindow + spawn Python backend
│   └── public/
├── irisflow/
│   ├── app/           # Entrypoint e bootstrap
│   ├── core/          # Config, eventos, estado, logger
│   ├── tracking/      # BaseGazeEngine, MockGazeEngine, TrackingService
│   ├── integrations/  # EyeTraxAdapter (isolado)
│   ├── accessibility/ # Dwell click, fixation, region mapper
│   ├── speech/        # TTS e fila de fala
│   ├── profiles/      # Perfis de usuário
│   └── storage/       # Persistência local
├── docs/              # Arquitetura, roadmap, decisões
└── tests/
```

---

## Roadmap rápido

- [x] Fase 1 ✅ Base funcional
- [x] Fase 2 ✅ EyeTrax real + filtros avançados
- [x] Fase 3 ✅ Frases rápidas + teclado + perfis
- [x] Fase 4 ✅ Pipeline de ML próprio (IrisGazeNet + SVR)
- [x] Fase 5 ✅ Frontend React + Electron (design Lumina, 4 telas)
- [ ] Fase 6 ⏳ Backend FastAPI + WebSocket
- [ ] Fase 7 ⏳ Piloto clínico com AACD
- [ ] Fase 8 ⏳ Regulação ANVISA + negócio
- [ ] Fase 9 ⏳ Empacotamento .exe Windows

**Meta:** demonstração para profissionais de saúde em julho/agosto 2026.

---

## Licença

Projeto privado — IrisFlow 2026.
