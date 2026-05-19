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

## ADR-014 — Arquitetura canônica v1.0: MediaPipe + Ridge Regression

**Contexto:** A apresentação de validação técnica apontou contradição entre slides que citavam CNN e LSTM como modelos principais e a implementação real do MVP.  
**Decisão:** A arquitetura canônica do MVP é MediaPipe Face Mesh → extração de features oculares → Ridge Regression → Deadzone → Kalman EMA.  
**Motivo:** Funcional, validado, inference <30ms em hardware comum (Intel i3 + 8GB RAM). CNN/MobileNetV2 e LSTM requerem dados rotulados de ELA que ainda não existem.  
**Consequência:** CNN e LSTM são planejados para v2.0 após coleta de dados reais com parceiros clínicos (AACD). Todos os materiais do projeto devem referenciar esta decisão.

## ADR-015 — Filtro Deadzone para microtremores oculares (Fase 2)

**Contexto:** Pacientes com ELA apresentam tremor ocular involuntário que causava ativações acidentais de botões mesmo sem intenção de seleção.  
**Decisão:** Inserir filtro Deadzone antes do Kalman EMA na cadeia de processamento. Raio de 12px e limiar de 25 frames parado antes de liberar o cursor.  
**Cadeia final:** raw → Deadzone (12px, 25 frames) → Kalman EMA (α=0.2) → GazePoint.  
**Motivo:** Cursor travado durante microtremores elimina ativações acidentais sem prejudicar fixações intencionais prolongadas (>25 frames ≈ 0,8s a 30fps).

## ADR-016 — Detecção de qualidade de frame por luminância (Fase 2)

**Contexto:** Iluminação ruim degrada silenciosamente a acurácia do modelo sem nenhum aviso ao usuário ou cuidador.  
**Decisão:** Verificar luminância média do frame a cada 30 frames (~1s). Faixa aceitável: 40–220. Valores fora da faixa emitem aviso na status bar por 4 segundos.  
**Motivo:** Emitir aviso sem interromper o tracking mantém a experiência fluida enquanto permite ao cuidador corrigir a iluminação. Verificar a cada 30 frames garante performance adequada (sem overhead por frame).

## ADR-017 — Modelo próprio IrisGazeNet — MobileNetV2 + MLP

**Contexto:** O orientador do projeto exige que o IrisFlow implemente e treine um algoritmo de ML próprio, não podendo depender exclusivamente de bibliotecas de terceiros (EyeTrax) para a estimativa de olhar.  
**Decisão:** Implementar o **IrisGazeNet**: backbone MobileNetV2 (pré-treinado em ImageNet) + MLP de 3 camadas `[1283 → 256 → 64 → 2]` para mapear features visuais do olho + pose da cabeça em coordenadas de tela normalizadas `(x_norm, y_norm)`.  
**Fluxo:** Pré-treino offline nos datasets MPIIGaze (213.658 amostras) e OpenEDS (12.759 imagens) → fine-tuning por paciente durante a calibração (~200 amostras, ~20 epochs, on-device).  
**Inspiração:** GazeFollower (Zhu et al., ACM CGIT 2025) — implementação inteiramente própria, sem uso de código do paper.  
**Fallback:** EyeTraxAdapter permanece como engine padrão durante o desenvolvimento do IrisGazeNet. A troca é feita via `tracking_engine` no perfil do paciente, sem alterar código de UI.  
**Modelo salvo por perfil:** `irisflow/profiles/{profile_id}/gaze_model.pt`  
**Documentação:** `docs/ML_ARCHITECTURE.md` e `docs/TRAINING_SETUP.md`

## ADR-018 — Separação treino/inferência (offline vs. on-device)

**Contexto:** O pré-treino do IrisGazeNet requer GPU e datasets que somam ~5GB — inviável de executar nos dispositivos dos pacientes (hardware doméstico, sem GPU dedicada).  
**Decisão:** Os scripts de treino ficam isolados em `/training/` e são executados em ambiente separado com GPU (Google Colab T4 ou estação local). Apenas o arquivo `irisflow_base_model.pt` gerado é distribuído com o produto.  
**Fine-tuning on-device:** A calibração por paciente (~200 amostras, 20 epochs, backbone congelado) roda on-device pois opera exclusivamente sobre a MLP — custo computacional estimado em < 30 segundos em Intel i5 sem GPU.  
**Separação de dependências:** O ambiente de produção (`irisflow/`) não importa `torch.cuda` nem requer CUDA — inferência e fine-tuning de calibração usam apenas CPU via PyTorch CPU-only.
