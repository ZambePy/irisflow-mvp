# IrisFlow MVP

> Plataforma assistiva de comunicação por rastreamento ocular para pessoas com ELA, tetraplegia e limitações motoras severas.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![PyQt6](https://img.shields.io/badge/UI-PyQt6-green) ![EyeTrax](https://img.shields.io/badge/EyeTrax-0.4-orange) ![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows)

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

## Primeiros passos

### 1. Criar e ativar o ambiente virtual

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Rodar o MVP

```bash
python -m irisflow.app.main
```

> Por padrão inicia em modo **mock** (mouse simula o olhar). Para usar o EyeTrax real, configure `engine: eyetrax` em `irisflow/integrations/eyetrax/config.py`.

### 4. Como testar o dwell click

- Mova o mouse sobre um botão
- Mantenha o cursor parado por **1 segundo**
- O botão será ativado automaticamente com feedback de progresso

---

## Stack

| Componente | Tecnologia |
|---|---|
| Interface desktop | PyQt6 |
| Eye tracking | EyeTrax 0.4 (via adapter) / MockGazeEngine |
| TTS | pyttsx3 + SAPI (Windows) |
| Perfis | JSON local |
| Python | 3.11 |
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

- [x] Fase 1 ✅ Base funcional
- [x] Fase 2 ✅ EyeTrax real + filtros avançados
- [x] Fase 3 ✅ Frases rápidas + teclado + perfis
- [ ] Fase 4 ⏳ Polimento para demonstração
- [ ] Fase 5 ⏳ Modelo e qualidade técnica
- [ ] Fase 6 ⏳ Piloto clínico com AACD
- [ ] Fase 7 ⏳ Regulação ANVISA + negócio
- [ ] Fase 8 ⏳ Empacotamento + lançamento

**Meta:** demonstração para profissionais de saúde em julho/agosto 2026.

---

## Licença

Projeto privado — IrisFlow 2026.
