# Estratégia de Dados — IrisFlow

## Visão Geral

O IrisFlow usa uma estratégia de três camadas para lidar com o gap
entre datasets públicos (pessoas saudáveis) e o público-alvo real
(pacientes com ELA em estágios variados):

- Camada 1: Pré-treino geral com dataset público (MPIIGaze)
- Camada 2: Augmentation específico para ELA
- Camada 3: Fine-tuning individual por paciente na calibração

Nenhum dataset público cobre pacientes com ELA. Nossa resposta
arquitetural para isso é o fine-tuning individual — o modelo aprende
especificamente para aquele olho, naquele estágio da doença, naquela
condição de iluminação.

---

## Camada 1 — Pré-treino Geral

### MPIIGaze (Max Planck Institute)

**STATUS: ✅ Baixado e integrado**

**Por que escolhemos:**
- Capturado em laptops no dia a dia — mesmo cenário do IrisFlow
- Maior diversidade de condições reais (iluminação, ângulo, distância)
- Não requer aprovação — download direto
- Mais citado em literatura de gaze estimation com webcam comum

**Características:**
- 213.658 imagens totais; **10.654 amostras no Annotation Subset** (com anotações de gaze utilizáveis)
- 15 participantes, coleta ao longo de 25 dias cada
- Formato: imagens RGB, redimensionadas para **224×224px** antes do MobileNetV2
- Anotações: pose da cabeça (yaw, pitch, roll) + vetor de olhar (gaze direction)
- Condições reais: variação de iluminação, ângulo de cabeça, distância

**Limitações para ELA:**
- Participantes saudáveis — movimento ocular normal
- Piscada normal — EAR (Eye Aspect Ratio) alto
- Range de movimento completo — sem restrição de sacadas
- Sem fadiga ocular

**Uso no pipeline:**
Treino offline dos modelos SVR base (SVR-X e SVR-Y) do IrisGazeNet —
9.067 amostras de treino do Annotation Subset. O MobileNetV2 extrai
features de cada imagem (congelado); o SVR aprende o mapeamento
features → coordenada de tela. Não é usado no retreino por paciente
(este usa os ~200 pontos da calibração individual).

**Download:**
https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/research/gaze-based-human-computer-interaction/appearance-based-gaze-estimation-in-the-wild

**Estrutura esperada em disco:**

```
datasets/MPIIGaze/
├── Data/
│   ├── Original/
│   │   ├── p00/   ← participante 0
│   │   ├── p01/
│   │   └── ...p14/
│   └── Normalized/
└── Evaluation Subset/
```

**Split utilizado (Annotation Subset — 10.654 amostras):**
- Treino: 9.067 amostras
- Validação: 972 amostras
- Teste: 615 amostras — nunca visto durante treino

---

### Por que NÃO usamos outros datasets como principal

**OpenEDS (Meta AI) — STATUS: ⏳ Planejado — requer aprovação da Meta AI:**
- Capturado em headset de realidade virtual
- Condições artificiais e controladas — nada a ver com webcam
- Requer aprovação da Meta (demora semanas) — aprovação ainda não obtida
- Headset é inutilizável para paciente acamado com ELA
- Uso potencial: segmentação de íris como pré-treino auxiliar, se aprovação for obtida
- **Status: ⏳ Planejado — não integrado ao pipeline atual do IrisFlow**

**GazeCapture (MIT):**
- 1.5M imagens — maior que MPIIGaze
- Capturado em smartphones/tablets — diferente de webcam
- Boa diversidade de participantes
- Considerado para versão 2.0 se MPIIGaze mostrar limitações

**UnityEyes / SynthesisEyes:**
- Dados 100% sintéticos gerados por computador
- Cobre posições extremas de olho
- Útil como augmentation complementar (Camada 2)
- Não substitui dados reais para pré-treino

---

## Camada 2 — Augmentation Específico para ELA

### O que muda no olho com ELA progressiva

**Estágio inicial/médio:**
- Movimento ocular preservado (última função motora a deteriorar)
- Piscada reduzida — olho resseca, EAR cronicamente baixo
- Tremor leve (nistagmo em alguns casos)
- Fadiga ocular mais rápida

**Estágio avançado:**
- Sacadas (movimentos rápidos) mais lentas
- Range de movimento reduzido — dificuldade nas extremidades
- EAR muito baixo — olho quase fechado
- Fixação instável — não mantém olhar parado por muito tempo

**Estágio final:**
- Oftalmoplegia — paralisia parcial dos músculos oculares
- Movimento restrito ao centro da tela
- Alguns pacientes perdem eye tracking completamente

### Pipeline de augmentation para ELA

Aplicado sobre imagens do MPIIGaze durante treino:

**Simulação de piscada reduzida:**
- Filtrar frames com EAR < 0.15 (olho mais fechado que normal)
- RandomCrop vertical para simular pálpebra semi-fechada
- Objetivo: modelo aprende a funcionar com olho parcialmente fechado

**Simulação de tremor ocular:**
- Ruído gaussiano nas coordenadas de gaze: σ = 2–8px
- Jitter periódico nas coordenadas (nistagmo simulado)
- Objetivo: modelo aprende a filtrar tremor involuntário

**Simulação de range reduzido:**
- Mascarar amostras com gaze nas bordas extremas (>80% da tela)
- Dar mais peso a amostras do centro durante treino
- Objetivo: modelo mais preciso no range real de uso

**Simulação de condições ambientais:**
- RandomBrightnessContrast(limit=(-0.5, 0.2)) — quarto escuro
- GaussNoise(var_limit=(10, 60)) — webcam de baixo custo
- RandomShadow(p=0.3) — luz lateral (janela, abajur)
- MotionBlur(blur_limit=3, p=0.2) — tremor leve de câmera

**Augmentation padrão:**
- HorizontalFlip(p=0.5) — espelha olho esquerdo ↔ direito
- Rotate(limit=15, p=0.6) — inclinação da cabeça
- Multiplicador: 10x sobre cada imagem original

### Limitações do augmentation

O augmentation simula condições de ELA mas NÃO substitui dados reais.
Pacientes reais têm variações anatômicas (formato do olho, íris, pálpebra)
que não podem ser simuladas. Por isso a Camada 3 é a mais importante
clinicamente.

---

## Camada 3 — Fine-tuning Individual por Paciente (Calibração)

### Por que é a camada mais importante para ELA

Cada paciente com ELA é único:
- Estágio diferente da doença
- Anatomia ocular diferente
- Setup físico diferente (distância da webcam, ângulo da cama)
- Condição de iluminação diferente
- Velocidade de movimento ocular diferente

O fine-tuning individual resolve tudo isso em 60 segundos.

### Como funciona

1. Paciente olha para 9 pontos na tela (grade 3×3)
2. Sistema coleta ~200 amostras (imagem + pose + coordenada real)
3. IrisGazeNet extrai features de cada frame (backbone congelado)
4. Dois SVR são treinados: um para X, um para Y
5. Modelo personalizado salvo em profiles/{id}/gaze_model.pt
6. Inferência em tempo real usa backbone geral + SVR personalizado

### Parâmetros de calibração para ELA

Ajustes necessários vs. usuário saudável:
- Tempo por ponto: 3s (vs. 2s padrão) — sacadas mais lentas
- Descartar primeiros 10 frames por ponto — tempo de fixação maior
- Ponto central (960, 540) com peso 2x — range reduzido
- Recalibração automática sugerida a cada 7 dias — doença progressiva

---

## Plano de Coleta de Dados Próprios (Fase 6)

### Parceria AACD / AME

Após aprovação ética (CAAE obrigatório):
- 5–10 pacientes voluntários com ELA em estágios variados
- Protocolo: vídeo do olho + coordenadas ground-truth (9 pontos) +
  diagnóstico e estágio da doença
- Dataset: IrisFlow-ELA-v1
- Uso: fine-tuning do backbone + validação clínica real

### Métricas de avaliação clínica

Além do MAE em pixels, coletar:
- Taxa de acerto de botão (% de ativações corretas)
- Tempo médio para ativar um botão (latência de comunicação)
- Fadiga ocular subjetiva (escala 1–5 reportada pelo paciente)
- NPS do cuidador (Net Promoter Score)

---

## Resumo da Estratégia

| Camada | Dataset | Quando | Para quê |
|---|---|---|---|
| 1 | MPIIGaze | Offline, uma vez | Pré-treino geral do backbone |
| 2 | MPIIGaze + augmentation ELA | Durante treino | Robustez para condições ELA |
| 3 | Dados do próprio paciente | Na calibração (60s) | Personalização individual |
| Futuro | IrisFlow-ELA-v1 (AACD) | Fase 6 | Validação clínica real |

**Argumento central:** datasets públicos não cobrem ELA.
Nossa resposta é o fine-tuning individual por paciente —
o modelo aprende para aquele olho, naquele estágio, naquele ambiente.

---

## Referências

- Zhang et al. (2015). Appearance-based Gaze Estimation in the Wild.
  CVPR 2015. (MPIIGaze)
- Zhu et al. (2025). GazeFollower: An open-source system for
  deep learning-based gaze tracking. ACM CGIT 2025.
- Garbin et al. (2019). OpenEDS: Open Eye Dataset. Meta AI.
- Sandler et al. (2018). MobileNetV2. CVPR 2018.
