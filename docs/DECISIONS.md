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

## ADR-010 — Frases rápidas em dois níveis: contexto → frases (Fase 3)

**Decisão:** O banco de frases rápidas é organizado em dois níveis — primeiro o usuário seleciona um contexto (ex.: "Saúde", "Conforto") e depois escolhe a frase dentro daquele contexto. Tudo salvo em JSON editável.  
**Motivo:** Um único nível com muitas frases exige scroll ou botões minúsculos — inviável com gaze. Dois níveis mantêm no máximo ~6 opções visíveis por vez, dentro da zona confortável de dwell.

## ADR-011 — Perfis em JSON local com último perfil carregado automaticamente (Fase 3)

**Decisão:** Cada perfil de usuário é salvo como um objeto JSON em `profiles/`. Na inicialização, o sistema carrega automaticamente o último perfil ativo sem exigir seleção manual.  
**Motivo:** Pacientes com ELA usam o dispositivo com o mesmo cuidador diariamente. Forçar seleção de perfil a cada abertura é fricção desnecessária. JSON local evita dependência de banco de dados no MVP.

## ADR-012 — Modo cuidador via F10 sem senha (Fase 3)

**Decisão:** O modo cuidador (edição de frases, perfis, configurações) é ativado pela tecla F10 no teclado físico, sem autenticação por senha.  
**Motivo:** Senhas digitadas via gaze são lentas e frustrantes. O modelo de ameaça do MVP é doméstico: o cuidador está fisicamente presente e tem acesso ao teclado. F10 é suficiente como barreira de acesso acidental pelo usuário.

## ADR-013 — Calibração dense grid 7×7 como padrão (Fase 3)

**Decisão:** A grade de calibração padrão usa 49 pontos (7 colunas × 7 linhas) cobrindo toda a tela.  
**Motivo:** Grades menores (3×3, 5×5) deixam cantos e bordas com erro de predição alto — exatamente onde ficam botões de emergência e navegação. 7×7 oferece cobertura espacial densa o suficiente para compensar variações de postura do usuário ao longo da sessão.
