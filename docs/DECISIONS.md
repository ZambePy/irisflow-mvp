# Decisões técnicas

## ADR-001 — PyQt6 como framework de UI

**Decisão:** Usar PyQt6 para interface desktop.  
**Motivo:** Maturidade, suporte a Windows, empacotamento com PyInstaller, controle total de layout para acessibilidade.

## ADR-002 — EyeTrax via Adapter, nunca direto na UI

**Decisão:** EyeTrax é isolado em `integrations/eyetrax/adapter.py`.  
**Motivo:** Evitar acoplamento. Permite trocar o motor de rastreamento no futuro sem tocar na UI.

## ADR-003 — MockGazeEngine para desenvolvimento

**Decisão:** Em modo "mock", a posição do mouse substitui o olhar.  
**Motivo:** Permite desenvolver e testar toda a UI e dwell click sem precisar de webcam.

## ADR-004 — pyttsx3 para TTS inicial

**Decisão:** Usar pyttsx3 como motor TTS offline.  
**Motivo:** Funciona sem internet, suporta PT-BR, leve. Edge-TTS pode ser adicionado depois como opção de qualidade superior.

## ADR-005 — JSON local para perfis

**Decisão:** Perfis salvos em JSON local.  
**Motivo:** Sem dependência de banco de dados no MVP. SQLite pode ser adicionado depois.

## ADR-006 — Dwell click como método de seleção primário

**Decisão:** Seleção por permanência do olhar (1 segundo padrão).  
**Motivo:** Método mais acessível e confiável para ELA/tetraplegia. Sem necessidade de piscar.

## ADR-007 — SAPI como backend TTS no Windows (Fase 2)

**Decisão:** No Windows, TTS usa SAPI via `win32com` em vez de pyttsx3.  
**Motivo:** SAPI acessa diretamente as vozes instaladas no Windows, incluindo vozes PT-BR de alta qualidade, sem dependência extra. pyttsx3 permanece como fallback multiplataforma.

## ADR-008 — Calibração delegada ao EyeTrax na Fase 2

**Decisão:** A tela de calibração do MVP chama a rotina de calibração nativa do EyeTrax 0.4.  
**Motivo:** Implementar calibração própria é complexo. Delegar ao EyeTrax desbloqueia o hardware real mais rápido. Calibração própria IrisFlow fica para a Fase 4.

## ADR-009 — GazeCursor como overlay visual (Fase 2)

**Decisão:** Um widget `GazeCursor` sobreposto à janela principal exibe a posição atual do olhar em tempo real.  
**Motivo:** Feedback visual imediato aumenta a confiança do usuário e facilita calibração e debug sem ferramentas externas.

## ADR-010 — Configuração do EyeTrax em arquivo separado

**Decisão:** Parâmetros específicos do EyeTrax (device_id, fps, resolução) ficam em `integrations/eyetrax/config.py`, separados do config central.  
**Motivo:** Isolar configuração de hardware do restante da aplicação. Facilita troca de motor de rastreamento no futuro.
