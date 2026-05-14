# IrisFlow MVP

> Plataforma assistiva de comunicação por rastreamento ocular para pessoas com ELA, tetraplegia e limitações motoras severas.

---

## O que é o IrisFlow?

O IrisFlow permite que pessoas com mobilidade extremamente reduzida se comuniquem usando apenas o olhar — via webcam comum, sem hardware especializado.

O foco do MVP é:
- Seleção confiável por olhar (dwell click)
- Botões grandes e de alto contraste
- Painel Sim/Não instantâneo
- Frases rápidas
- Teclado virtual básico
- Text-to-speech em português
- Botão de emergência
- Perfis locais por usuário
- Baixa fadiga ocular

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

## Primeiros passos

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Rodar o MVP (modo mock — mouse simula o olhar)

```bash
cd irisflow-mvp
python -m irisflow.app.main
```

### 3. Como testar o dwell click

- Mova o mouse sobre um botão
- Mantenha o cursor parado por **1 segundo**
- O botão será ativado automaticamente com feedback de progresso

---

## Stack

| Componente | Tecnologia |
|---|---|
| Interface desktop | PyQt6 |
| Eye tracking | EyeTrax (via adapter) / MockGazeEngine |
| TTS | pyttsx3 |
| Perfis | JSON local |
| Python | 3.11+ |
| Empacotamento futuro | PyInstaller (.exe Windows) |

---

## Estrutura de pastas

```
irisflow-mvp/
├── irisflow/
│   ├── app/           # Entrypoint e bootstrap
│   ├── core/          # Config, eventos, estado, logger
│   ├── tracking/      # BaseGazeEngine, MockGazeEngine, TrackingService
│   ├── integrations/  # EyeTraxAdapter (isolado)
│   ├── accessibility/ # Dwell click, fixation, region mapper
│   ├── ui/            # Janelas, telas, componentes PyQt6
│   ├── speech/        # TTS e fila de fala
│   ├── profiles/      # Perfis de usuário
│   └── storage/       # Persistência local
├── docs/              # Arquitetura, roadmap, decisões
└── tests/
```

---

## Roadmap rápido

- [x] Fase 1 — MockGazeEngine + UI base + dwell click
- [ ] Fase 2 — Integração EyeTrax real
- [ ] Fase 3 — Calibração própria IrisFlow
- [ ] Fase 4 — Perfis de usuário + configurações
- [ ] Fase 5 — Empacotamento Windows (.exe)

---

## Licença

Projeto privado — IrisFlow 2026.
