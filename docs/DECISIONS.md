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
