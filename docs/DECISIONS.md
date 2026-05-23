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
**Motivo:** Funcional, validado, inference <30ms em hardware comum (Intel i3 + 8GB RAM). Backbone CNN treinado do zero ou LSTM requeriam dados rotulados de ELA que ainda não existiam; MobileNetV2 pré-treinado + SVR foi adotado como solução própria sem essa dependência (ver ADR-017).  
**Consequência:** CNN treinada do zero e LSTM não fazem parte do roadmap do IrisFlow. O modelo próprio adotado é o IrisGazeNet (MobileNetV2 pré-treinado como extrator de features + SVR treinado pela equipe) — ver ADR-017 e ADR-019. Todos os materiais do projeto devem referenciar esta decisão.

## ADR-015 — Filtro Deadzone para microtremores oculares (Fase 2)

**Contexto:** Pacientes com ELA apresentam tremor ocular involuntário que causava ativações acidentais de botões mesmo sem intenção de seleção.  
**Decisão:** Inserir filtro Deadzone antes do Kalman EMA na cadeia de processamento. Raio de 12px e limiar de 25 frames parado antes de liberar o cursor.  
**Cadeia final:** raw → Deadzone (12px, 25 frames) → Kalman EMA (α=0.2) → GazePoint.  
**Motivo:** Cursor travado durante microtremores elimina ativações acidentais sem prejudicar fixações intencionais prolongadas (>25 frames ≈ 0,8s a 30fps).

## ADR-016 — Detecção de qualidade de frame por luminância (Fase 2)

**Contexto:** Iluminação ruim degrada silenciosamente a acurácia do modelo sem nenhum aviso ao usuário ou cuidador.  
**Decisão:** Verificar luminância média do frame a cada 30 frames (~1s). Faixa aceitável: 40–220. Valores fora da faixa emitem aviso na status bar por 4 segundos.  
**Motivo:** Emitir aviso sem interromper o tracking mantém a experiência fluida enquanto permite ao cuidador corrigir a iluminação. Verificar a cada 30 frames garante performance adequada (sem overhead por frame).

## ADR-017 — Modelo próprio IrisGazeNet — MobileNetV2 (extrator) + SVR (calibração)

**Contexto:** O orientador do projeto exige que o IrisFlow implemente e treine um algoritmo de ML próprio, não podendo depender exclusivamente de bibliotecas de terceiros (EyeTrax) para a estimativa de olhar.  
**Decisão:** Implementar o **IrisGazeNet**: backbone MobileNetV2 (pré-treinado em ImageNet, congelado — não treinado pela equipe) como extrator de features + **dois modelos SVR (SVR-X e SVR-Y)** como algoritmo de ML treinado pela equipe, mapeando o vetor de features `[1.280 dimensões]` para coordenadas de tela normalizadas `(x_norm, y_norm)`.  
**Fluxo:** Pré-treino offline no MPIIGaze Annotation Subset (10.654 amostras, split 9.067/972/615) → retreino do SVR por paciente durante a calibração (~200 amostras, on-device, < 5 segundos).  
**Inspiração:** GazeFollower (Zhu et al., ACM CGIT 2025) — implementação inteiramente própria, sem uso de código do paper. Ver ADR-019.  
**Fallback:** EyeTraxAdapter permanece como engine padrão durante o desenvolvimento do IrisGazeNet. A troca é feita via `tracking_engine` no perfil do paciente, sem alterar código de UI.  
**Modelos salvos por perfil:** `irisflow/profiles/{profile_id}/svr_x.pkl` e `svr_y.pkl`  
**Documentação:** `docs/ML_ARCHITECTURE.md`

## ADR-018 — Separação treino/inferência (offline vs. on-device)

**Contexto:** O pré-treino do IrisGazeNet usa datasets que somam ~5GB — inviável de executar nos dispositivos dos pacientes (hardware doméstico, sem GPU dedicada).  
**Decisão:** Os scripts de treino ficam isolados em `/training/` e são executados em ambiente separado com CPU ou GPU (Google Colab ou estação local). Os arquivos `svr_x_base.pkl` e `svr_y_base.pkl` gerados são distribuídos com o produto.  
**Calibração on-device:** O retreino dos modelos SVR por paciente (~200 amostras, backbone congelado) roda on-device. SVR não usa GPU — treina em segundos em CPU Intel i5 sem overhead de retropropagação.  
**Separação de dependências:** O ambiente de produção (`irisflow/`) não importa `torch.cuda` nem requer CUDA — inferência usa apenas CPU via PyTorch CPU-only. Os modelos SVR são serializados com `joblib` (`.pkl`).

## ADR-019 — SVR como algoritmo de ML central do IrisFlow

**Contexto:** A documentação anterior do projeto misturava CNN treinada do zero, LSTM e MLP como possíveis modelos de gaze estimation, gerando inconsistência apontada na avaliação dos orientadores. Era necessário definir com precisão qual algoritmo de ML é treinado e avaliado pela equipe.  
**Decisão:** O algoritmo de ML treinado pela equipe é o **SVR (Support Vector Regression)**, com dois modelos separados: **SVR-X** (eixo horizontal) e **SVR-Y** (eixo vertical). O MobileNetV2 é utilizado apenas como extrator de features pré-treinado (pesos ImageNet, congelados) — não é treinado pela equipe e não é o algoritmo de ML do projeto.  
**Inspiração:** GazeFollower (Zhu et al., ACM CGIT 2025), que usa a mesma separação backbone CNN (extração) + SVR (calibração personalizada).  
**Treinamento:** O SVR é treinado em duas etapas: (1) offline no MPIIGaze Annotation Subset (9.067 amostras de treino), gerando modelos base (MAE 22,7px no test set independente); (2) on-device durante a calibração (~200 amostras do paciente), gerando modelos personalizados por perfil.  
**Baseline de comparação:** Ridge Regression do EyeTrax — mesma família de modelos lineares, comparação direta e significativa academicamente. Resultado medido: SVR 22,7px vs Ridge 20,2px (diferença de 2,5px no test set).  
**Substitui:** qualquer menção anterior a CNN treinada do zero, LSTM ou MLP como algoritmo principal de gaze estimation no IrisFlow. Ver ADR-021 — a MLP foi removida do pipeline.  
**Documentação:** `docs/ML_ARCHITECTURE.md`, `docs/model_comparison.md`

## ADR-021 — Remoção da MLP do pipeline principal

**Contexto:** O pipeline original (`IrisGazeNet`) tinha uma MLP acoplada ao backbone (1280→256→64→2) usada como fallback quando nenhuma calibração estava disponível. O GazeFollower (Zhu et al., ACM CGIT 2025) não usa MLP — vai diretamente de features do backbone para SVR.  
**Decisão:** Remover a MLP completamente. O pipeline passa a ter duas classes com responsabilidade única: `IrisFeatureExtractor` (backbone congelado, extração de 1280 features) e `IrisGazeEstimator` (extrator + SVR-X + SVR-Y), espelhando a arquitetura do GazeFollower.  
**`IrisFeatureExtractor` tem 0 parâmetros treináveis** — backbone MobileNetV2 completamente congelado, nunca atualizado em nenhuma etapa.  
**Sem fallback sem calibração:** `predict()` levanta `RuntimeError` explícito se chamado antes de `calibrate()`. A operação sem calibração não é suportada — é um erro de uso, não um estado válido.  
**Substitui:** `IrisGazeNet` (com MLP) e `IrisGazeNetCalibrated` (wrapper separado). A API pública agora é `IrisFeatureExtractor` e `IrisGazeEstimator`.  
**Impacto:** `training/model.py` reescrito; `dataset.py` não alterado.

## ADR-022 — Migração de PyQt6 para React + Electron

**Contexto:** PyQt6 limitava o design e dificultava iteração visual; design profissional criado no Stitch.ai com glassmorphism exigia componentes web modernos.  
**Decisão:** Frontend React 18 + Vite; shell desktop Electron; comunicação via WebSocket com backend FastAPI Python.  
**Consequências:**
- Frontend e backend completamente desacoplados
- Permite atualizar ML, tracking e lógica Python sem recompilar frontend
- PyQt6 removido como dependência de produção

## ADR-023 — Design System Lumina (Stitch.ai)

**Contexto:** Necessidade de UI clínica profissional com alto contraste, glassmorphism e botões grandes para eye tracking.  
**Decisão:** Usar design system Lumina exportado do Stitch.ai.  
**Consequências:**
- Tokens centralizados em `frontend/src/theme/lumina.js`
- Cores, tipografia e espaçamento facilmente customizáveis por clínica

## ADR-020 — Remoção da pose explícita do pipeline de features

**Contexto:** O MPIIGaze Annotation Subset não fornece ângulos de pitch/yaw em radianos — apenas landmarks faciais em coordenadas de pixel. A tentativa de estimar pose via MediaPipe falhou com 100% de taxa de zeros, pois os crops do olho (sem rosto completo) não são suportados pelo MediaPipe Face Mesh.  
**Decisão:** O pipeline usa apenas as **1.280 features do MobileNetV2**, sem concatenar ângulos de pose. MLP simplifica de 1283→256→64→2 para 1280→256→64→2. `extract_features()` retorna array (B, 1280).  
**Motivo:** Dados de pose não estão disponíveis no dataset escolhido. A calibração individual por paciente (~200 amostras on-device) captura implicitamente a pose típica do usuário no seu setup físico — sem necessidade de ângulos explícitos.  
**Impacto:** Remoção de `pose` em `forward()`, `extract_features()` e `predict()` de `model.py`. Remoção do tensor de pose de `__getitem__()` e `get_stats()` em `dataset.py`.  
**Alternativa futura:** MPIIFaceGaze (subconjunto normalizado do MPIIGaze) fornece pose real com câmera calibrada + IMU — pode ser integrado se pose explícita for necessária para melhorar acurácia.
