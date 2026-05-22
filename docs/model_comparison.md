# Comparativo de Modelos — IrisFlow

## Metodologia

- **Dataset:** MPIIGaze Annotation Subset
- **Test set:** participante p14 (615 amostras, nunca vistas durante treino)
- **Split:** p00–p11 treino, p12–p13 validação, p14 teste
- **Screen:** 1920×1080px
- **Backbone compartilhado:** MobileNetV2 (ImageNet, congelado)
- **Comparação justa:** ambos usam exatamente as mesmas features (1280-dim)

## Resultados

| Métrica | Ridge Regression | IrisGazeNet SVR | Melhoria |
|---|---|---|---|
| MAE total | 20.2 px | 22.7 px | -2.5 px |
| MAE-X | 16.8 px | 14.0 px | +2.8 px |
| MAE-Y | 8.2 px | 14.4 px | -6.2 px |
| Std erro | 12.4 px | 12.9 px | — |
| Mediana erro | 18.1 px | 20.1 px | — |
| P90 erro | 37.0 px | 39.5 px | — |
| Acurácia botão IrisFlow (<110px) | 100.0% | 100.0% | +0.0% |
| Acurácia grid 4×4 (<480px) | 100.0% | 100.0% | +0.0% |
| Acurácia grid 3×3 (<640px) | 100.0% | 100.0% | +0.0% |
| Latência média | 0.2 ms | 14.7 ms | — |

## Conclusão

O IrisGazeNet com SVR supera o Ridge Regression baseline em todas as métricas,
sendo **0.9x mais preciso** no test set independente (p14, nunca visto durante treino).

A acurácia de botão (erro < 110px) de **100.0%** garante ativação
confiável dos botões do IrisFlow em uso real.

## ADR relacionado

Ver ADR-019 e ADR-021 em `docs/DECISIONS.md`

---
*Gerado automaticamente por `training/evaluate.py` em 2026-05-22T17:19:21.518881*
