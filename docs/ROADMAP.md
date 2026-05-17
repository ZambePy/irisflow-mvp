# Roadmap IrisFlow MVP

**Meta:** demonstração para profissionais de saúde em julho/agosto de 2026.

---

## Fase 1 — Base funcional ✅

- [x] Estrutura de projeto
- [x] MockGazeEngine (mouse como olhar)
- [x] TrackingService
- [x] UI base: Sim/Não, Frases, Teclado, Emergência
- [x] Dwell click com feedback visual
- [x] TTS básico PT-BR (pyttsx3)

## Fase 2 — Integração EyeTrax real ✅

- [x] EyeTraxAdapter implementado (EyeTrax 0.4)
- [x] Troca mock ↔ eyetrax via config
- [x] Tela de calibração (usando calibração do EyeTrax)
- [x] Cursor visual de gaze (GazeCursor)
- [x] Botão de emergência estável
- [x] TTS via SAPI no Windows (voz nativa, offline)

## Fase 3 — Funcionalidades assistivas ✅

- [x] Frases rápidas por contexto editáveis em JSON (dois níveis: contexto → frases)
- [x] Teclado virtual completo com botão FALAR
- [x] Perfis de usuário (nome, dwell, frases favoritas) com último perfil carregado automaticamente
- [x] Modo cuidador via F10 (acesso por teclado físico, sem senha)
- [x] Cursor de gaze vermelho limpo (sem artefatos visuais)
- [x] Filtro kalman_ema para suavização do olhar
- [x] Calibração dense grid 7×7 como padrão

## Fase 4 — Polimento para demonstração

- [ ] Calibração própria IrisFlow (independente do EyeTrax)
- [ ] Ajustes de acessibilidade configuráveis (tamanho de botão, contraste)
- [ ] Modo noturno
- [ ] Log de sessão

## Fase 5 — Empacotamento Windows

- [ ] PyInstaller → .exe Windows
- [ ] Instalador simples para cuidadores
- [ ] Documentação para cuidadores (sem conhecimento técnico)
