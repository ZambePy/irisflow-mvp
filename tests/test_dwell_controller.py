import time
import pytest
from PyQt6.QtCore import QRect

from irisflow.accessibility.dwell import DwellController
from irisflow.tracking.types import GazePoint


def test_dwell_completa_apos_tempo(app_qt):
    dwell = DwellController(dwell_time_ms=100)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    completed = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))

    dwell.on_gaze(GazePoint(x=100, y=80))
    time.sleep(0.15)
    dwell.on_gaze(GazePoint(x=100, y=80))

    assert "sim" in completed, "dwell deve completar após tempo suficiente"


def test_dwell_nao_completa_antes_tempo(app_qt):
    dwell = DwellController(dwell_time_ms=500)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    completed = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))

    dwell.on_gaze(GazePoint(x=100, y=80))
    time.sleep(0.1)
    dwell.on_gaze(GazePoint(x=100, y=80))

    assert completed == [], "dwell não deve completar antes do tempo mínimo"


def test_dwell_cancela_ao_sair_da_regiao(app_qt):
    dwell = DwellController(dwell_time_ms=500)
    dwell.register_region("sim", QRect(0, 0, 200, 100))

    completed = []
    cancelled = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))
    dwell.dwell_cancelled.connect(lambda rid: cancelled.append(rid))

    dwell.on_gaze(GazePoint(x=100, y=50))
    time.sleep(0.05)
    dwell.on_gaze(GazePoint(x=100, y=50))
    dwell.on_gaze(GazePoint(x=500, y=500))  # fora da região

    assert "sim" in cancelled, "dwell deve ser cancelado ao sair da região"
    assert "sim" not in completed, "dwell não deve completar após cancelamento"


def test_gaze_invalido_nao_inicia_dwell(app_qt):
    dwell = DwellController(dwell_time_ms=100)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    completed = []
    progress_events = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))
    dwell.dwell_progress.connect(lambda rid, p: progress_events.append((rid, p)))

    for _ in range(5):
        dwell.on_gaze(GazePoint(x=100, y=80, confidence=0.1))
        time.sleep(0.05)

    assert completed == [], "gaze inválido não deve acionar dwell"
    assert progress_events == [], "gaze inválido não deve emitir progresso"


def test_multiplas_regioes_independentes(app_qt):
    dwell = DwellController(dwell_time_ms=100)
    dwell.register_region("sim", QRect(0, 0, 200, 100))
    dwell.register_region("nao", QRect(300, 0, 200, 100))

    completed = []
    cancelled = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))
    dwell.dwell_cancelled.connect(lambda rid: cancelled.append(rid))

    dwell.on_gaze(GazePoint(x=100, y=50))   # inicia "sim"
    time.sleep(0.05)
    dwell.on_gaze(GazePoint(x=400, y=50))   # cancela "sim", inicia "nao"
    time.sleep(0.15)
    dwell.on_gaze(GazePoint(x=400, y=50))   # completa "nao"

    assert "nao" in completed, "dwell de 'nao' deve completar"
    assert "sim" not in completed, "'sim' não deve ter completado"


def test_reset_limpa_estado(app_qt):
    dwell = DwellController(dwell_time_ms=100)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    completed = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))

    dwell.on_gaze(GazePoint(x=100, y=80))
    time.sleep(0.08)  # 80ms de 100ms — ainda não completou
    dwell.reset()     # reinicia o timer

    dwell.on_gaze(GazePoint(x=100, y=80))  # recomeça do zero
    time.sleep(0.05)                        # apenas 50ms desde o reset
    dwell.on_gaze(GazePoint(x=100, y=80))

    assert completed == [], "dwell não deve completar se o timer foi reiniciado"


def test_clear_regions_cancela_dwell_ativo(app_qt):
    dwell = DwellController(dwell_time_ms=500)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    dwell.on_gaze(GazePoint(x=100, y=80))
    dwell.clear_regions()

    assert dwell._active_region is None, "clear_regions deve limpar a região ativa"


def test_progresso_entre_0_e_1(app_qt):
    dwell = DwellController(dwell_time_ms=150)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    progress_events = []
    dwell.dwell_progress.connect(lambda rid, p: progress_events.append((rid, p)))
    dwell.dwell_completed.connect(lambda rid: None)  # evita assert failure por sinal não conectado

    dwell.on_gaze(GazePoint(x=100, y=80))
    time.sleep(0.2)
    dwell.on_gaze(GazePoint(x=100, y=80))

    assert progress_events, "deve haver eventos de progresso"
    assert all(0.0 <= p <= 1.0 for _, p in progress_events), "todo progresso deve estar entre 0.0 e 1.0"
    last_progress = progress_events[-1][1]
    assert last_progress >= 0.9, f"último progresso deve ser >= 0.9, obtido: {last_progress}"


def test_dwell_nao_reativa_imediatamente(app_qt):
    dwell = DwellController(dwell_time_ms=100)
    dwell.register_region("sim", QRect(0, 0, 300, 150))

    completed = []
    progress_events = []
    dwell.dwell_completed.connect(lambda rid: completed.append(rid))
    dwell.dwell_progress.connect(lambda rid, p: progress_events.append((rid, p)))

    # Completar o primeiro dwell
    dwell.on_gaze(GazePoint(x=100, y=80))
    time.sleep(0.15)
    dwell.on_gaze(GazePoint(x=100, y=80))
    assert "sim" in completed, "primeiro dwell deve completar"

    progress_events.clear()

    # Gaze imediato na mesma região — novo dwell recomeça do zero
    dwell.on_gaze(GazePoint(x=100, y=80))

    assert progress_events, "novo dwell deve emitir progresso"
    first_progress = progress_events[0][1]
    assert first_progress < 0.5, f"novo dwell deve iniciar próximo de 0, obtido: {first_progress}"
