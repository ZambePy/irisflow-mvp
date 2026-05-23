"""Rotas REST para controle de calibração do engine de rastreamento."""

import threading

from fastapi import APIRouter

router = APIRouter()
_calibrating = False


@router.get("/status")
def calibration_status() -> dict:
    """Retorna se a calibração está em andamento."""
    return {"calibrating": _calibrating}


@router.post("/start")
def start_calibration(engine: str = "eyetrax") -> dict:
    """Inicia a calibração em thread separada (não bloqueante)."""
    global _calibrating
    if _calibrating:
        return {"error": "Calibração já em andamento"}

    def _run() -> None:
        global _calibrating
        _calibrating = True
        try:
            from irisflow.tracking.factory import create_engine
            eng = create_engine(engine)
            if hasattr(eng, "calibrate"):
                eng.calibrate()
        finally:
            _calibrating = False

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "message": "Calibração iniciada"}
