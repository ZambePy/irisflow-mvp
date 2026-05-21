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

## Próximas fases

### Fase 4 — Polimento para demonstração
- Calibração própria IrisFlow em PyQt6 (sem janela OpenCV separada)
- Ajustes de acessibilidade configuráveis por perfil (tamanho de botão,
  contraste, tempo de dwell)
- Alerta de recalibração quando acurácia cair
- Log de sessão por paciente (metadados anônimos — LGPD)

### Fase 5 — Qualidade técnica e modelo
- Comparativo formal de modelos: SVR (IrisGazeNet) vs Ridge Regression (EyeTrax baseline)
- Exportação ONNX Runtime + quantização INT8 (latência <30ms
  garantida em hardware básico — Intel i3 + 8GB RAM)
- Base sintética com augmentation para ELA (piscar reduzido,
  microtremores, baixa iluminação)
- Documentar model_comparison.md em /docs

### Fase 6 — Piloto clínico
- Parceria com AACD ou AME para 5-10 pacientes com ELA
- Protocolo de coleta com aprovação ética (CAAE)
- Fine-tuning com dados reais de ELA
- Dataset "IrisFlow-ELA-v1" documentado
- Recalibração automática semanal

### Fase 7 — Regulação e negócio
- Consultor regulatório ANVISA RDC 657/2022 (SaMD Classe I)
- Log de auditoria imutável de sessões
- Política de Privacidade e Termos de Uso (LGPD Art. 11)
- TAM/SAM/SOM formalizado com dados do piloto
- CAC/LTV calculado com primeiros 10 clientes

### Fase 8 — Empacotamento e lançamento
- PyInstaller → .exe Windows com instalador simples
- Landing page de vendas
- Submissão FAPESP PIPE
- Pitch com métricas reais de 5+ pacientes

## Matriz de riscos prioritários

| Risco | Nível | Mitigação |
|---|---|---|
| Modelo não atinge 92% em ELA real | 🔴 P1 | Dados reais AACD + augmentation ELA |
| Latência >30ms em hardware básico | 🟠 P2 | ONNX + INT8 antes do beta |
| Exigência ANVISA antes de clínicas | 🟠 P3 | Consultor desde Fase 7 |
| Concorrente lança antes do MVP | 🟡 P4 | Acelerar beta + fortalecer AACD |
| ELA progressiva — modelo não acompanha | 🟡 P6 | Recalibração semanal automática |
