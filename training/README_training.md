# IrisFlow — Guia de Treinamento e Benchmark

## Como medir a acurácia do sistema atual

### Pré-requisito: calibração concluída

O benchmark usa o modelo gerado pela calibração do IrisFlow. Antes de rodar o benchmark, o arquivo `irisflow_gaze_model.pkl` deve existir na raiz do projeto.

Se ainda não calibrou:
```bash
python -m irisflow.app.main
```
Siga o fluxo normal de calibração (EyeTrax 9 pontos). O modelo é salvo automaticamente ao final.

### Rodar o benchmark

A partir da **raiz do projeto** (não de dentro de `training/`):

```bash
python training/evaluate_accuracy.py
```

O script:
1. Detecta a tela automaticamente
2. Abre a webcam
3. Exibe instruções — pressione **ENTER** para começar ou **ESC** para cancelar
4. Mostra 9 pontos em sequência (grid 3×3 com margem de 10% das bordas)
5. Para cada ponto: 1 segundo de fixação, depois coleta de 30 amostras
6. Exibe o resultado na tela por 5 segundos
7. Salva o relatório completo em `models/accuracy_report.json`

**Duração estimada:** ~2 minutos (9 pontos × ~12 segundos cada)

---

## Como interpretar os resultados

### MAE em pixels (erro médio absoluto)

Distância média entre onde o sistema estimou que você estava olhando e o ponto real.

| MAE | Nota | Interpretação |
|-----|------|---------------|
| < 30px | Excelente | Precisão alta — adequado para qualquer uso |
| 30–60px | Bom | Adequado para botões do IrisFlow (mínimo 110px de altura) |
| 60–100px | Aceitável | Funciona, mas recalibração melhora a experiência |
| ≥ 100px | Insuficiente | Recalibrar antes de usar em sessão real |

### Acurácia de grid

Porcentagem de predições que caíram dentro de 1 célula do grid ao redor do ponto alvo.

- **Grid 4×4:** critério mais exigente — cada célula tem ~480×270px (em 1920×1080)
- **Grid 3×3:** critério mais relaxado — cada célula tem ~640×360px

Meta para uso assistivo com ELA: **acurácia 4×4 ≥ 88%**

### MAE por eixo

- `mae_x` alto → erro predominantemente horizontal → ajustar posição horizontal da webcam ou recalibrar
- `mae_y` alto → erro predominantemente vertical → ajustar altura da webcam ou inclinação da cabeça

### Melhor e pior ponto

O pior ponto é normalmente um dos cantos da tela. Se o erro nos cantos for muito alto, considere:
1. Aumentar a densidade da calibração
2. Manter a cabeça mais estável durante a calibração
3. Melhorar a iluminação da cena

---

## Onde fica o relatório

```
models/accuracy_report.json
```

Estrutura:
```json
{
  "timestamp": "2026-05-18T21:00:00",
  "model_path": "irisflow_gaze_model.pkl",
  "screen_size": [1920, 1080],
  "system": {
    "engine": "EyeTrax 0.4 + Ridge Regression",
    "filter": "Kalman EMA alpha=0.2 + Deadzone 12px"
  },
  "points": [...],
  "metrics": {
    "mae_pixels": 48.3,
    "std_pixels": 15.1,
    "mae_x": 22.1,
    "mae_y": 31.4,
    "accuracy_grid_4x4": 87.5,
    "accuracy_grid_3x3": 72.2,
    "best_point": 1,
    "worst_point": 7,
    "total_samples": 270
  },
  "interpretation": {
    "rating": "Bom",
    "description": "MAE < 60px — adequado para botões IrisFlow (mín 110px altura)"
  }
}
```

---

## Dependências necessárias para o benchmark

Todas já instaladas no ambiente do IrisFlow:
- `opencv-python` — captura e exibição
- `numpy` — cálculo de métricas
- `eyetrax` — modelo e extração de features

Opcional (para detecção automática de resolução):
- `screeninfo` — `pip install screeninfo`

---

## Dicas para um benchmark confiável

1. **Iluminação:** use a mesma iluminação da calibração
2. **Posição:** sente-se na mesma posição que usou durante a calibração
3. **Distância:** mantenha a mesma distância da tela (~60cm)
4. **Fixação real:** olhe diretamente para o centro do ponto verde, não ao redor dele
5. **Repetir:** rode o benchmark 2–3 vezes e compare os resultados

---

## Estrutura dos scripts de treinamento (futuro)

```
training/
├── evaluate_accuracy.py    ← benchmark do sistema atual (pronto)
├── pretrain.py             ← pré-treino do IrisGazeNet (planejado — ADR-017)
├── finetune.py             ← fine-tuning offline (planejado)
├── evaluate.py             ← avaliação do IrisGazeNet (planejado)
├── dataset.py              ← DataLoader MPIIGaze + OpenEDS (planejado)
├── augmentation.py         ← pipeline Albumentations (planejado)
├── model.py                ← IrisGazeNet MobileNetV2 + MLP (planejado)
└── config.yaml             ← hiperparâmetros (planejado)
```

Ver `docs/ML_ARCHITECTURE.md` e `docs/TRAINING_SETUP.md` para detalhes do IrisGazeNet.
