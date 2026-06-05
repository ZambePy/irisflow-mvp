"""Entrypoint FastAPI + WebSocket do IrisFlow.

Execução: python -m irisflow.api.main
"""

import asyncio
import json
import sys
import threading
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"  # sem display real
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
_qt_app = QApplication.instance() or QApplication(sys.argv)

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from irisflow.core.config import config
from irisflow.core.logger import logger
from irisflow.tracking.factory import create_engine
from irisflow.tracking.service import TrackingService
from irisflow.accessibility.dwell import DwellController
from irisflow.speech.tts import TTSEngine
from irisflow.profiles.profile_store import ProfileStore
from irisflow.storage.phrases_store import PhrasesStore
from irisflow.api.websocket import ConnectionManager
from irisflow.api.routes import profiles, phrases, calibration

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="IrisFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "file://",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serviços globais ──────────────────────────────────────────────────────────

manager = ConnectionManager()
tts = TTSEngine()
profile_store = ProfileStore()
phrases_store = PhrasesStore()
tracking: TrackingService | None = None
dwell: DwellController | None = None

# ── Rotas REST ────────────────────────────────────────────────────────────────

app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(phrases.router, prefix="/phrases", tags=["phrases"])
app.include_router(calibration.router, prefix="/calibration", tags=["calibration"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("[API] IrisFlow API iniciada em ws://127.0.0.1:8765/ws")
    logger.info("[API] Endpoints disponíveis:")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path    = getattr(route, "path", "")
        if methods:
            for m in sorted(methods):
                logger.info(f"[API]   {m:<6} {path}")
        else:
            logger.info(f"[API]   WS     {path}")
    await _start_tracking_engine("mock")
    # Pré-aquece a câmera em background para não bloquear o startup
    import threading
    threading.Thread(target=_warmup_camera, daemon=True).start()


def _warmup_camera() -> None:
    try:
        from irisflow.api.routes.calibration import _get_cap
        cap = _get_cap()
        if cap and cap.isOpened():
            logger.info("[API] Câmera inicializada e pronta para calibração")
        else:
            logger.warning("[API] Câmera não encontrada — calibração usará mock")
    except Exception as e:
        logger.warning(f"[API] Falha ao pré-aquecer câmera: {e}")


@app.get("/health")
async def health() -> dict:
    """Verifica o estado do servidor e do tracking."""
    return {
        "status": "ok",
        "tracking": tracking.is_running() if tracking else False,
        "engine": tracking.engine_name if tracking else None,
    }


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket principal — conecta frontend ao backend IrisFlow."""
    await manager.connect(websocket)
    # Abre câmera em background na primeira conexão WS para estar pronta na calibração
    import threading
    from irisflow.api.routes.calibration import _get_cap
    threading.Thread(target=_get_cap, daemon=True, name="cam-warmup").start()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_message(websocket, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("[API] Cliente WebSocket desconectado")


async def handle_message(websocket: WebSocket, message: dict) -> None:
    """Despacha mensagem recebida do frontend para o handler correto."""
    msg_type = message.get("type")

    if msg_type == "client_ready":
        await manager.send_to(websocket, {
            "type": "tracking_status",
            "running": tracking.is_running() if tracking else False,
            "engine": tracking.engine_name if tracking else None,
        })

    elif msg_type == "start_tracking":
        await start_tracking(websocket, message.get("engine", config.tracking_engine))

    elif msg_type == "stop_tracking":
        await stop_tracking()

    elif msg_type == "speak":
        text = message.get("text", "")
        logger.info(f"[API] TTS solicitado: {text!r}")
        if text:
            tts.speak(text)
            logger.info(f"[API] TTS chamado com sucesso: {text!r}")

    elif msg_type == "emergency":
        tts.speak("Emergência! Preciso de ajuda!")
        await manager.broadcast({"type": "emergency_activated"})

    elif msg_type == "set_dwell_time":
        ms = int(message.get("ms", config.dwell_time_ms))
        if dwell:
            dwell.set_dwell_time(ms)
            logger.info(f"[API] DwellTime atualizado: {ms}ms")

    elif msg_type == "dwell_regions":
        await update_dwell_regions(message.get("regions", []))


# ── Tracking ──────────────────────────────────────────────────────────────────

async def _start_tracking_engine(engine_name: str) -> None:
    """Inicializa ou reinicializa o engine de rastreamento (sem broadcast)."""
    global tracking, dwell
    loop = asyncio.get_running_loop()

    gaze_engine = create_engine(engine_name)
    next_tracking = TrackingService(gaze_engine)
    next_dwell = DwellController(
        dwell_time_ms=config.dwell_time_ms,
        radius_px=config.dwell_radius_px,
    )

    def on_gaze(point) -> None:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "gaze",
                "x": point.x,
                "y": point.y,
                "raw_x": point.raw_x,
                "raw_y": point.raw_y,
                "confidence": point.confidence,
                "left_eye_openness": point.left_eye_openness,
                "right_eye_openness": point.right_eye_openness,
                "blink": point.blink,
                "tracking_state": point.tracking_state,
                "timestamp": point.timestamp,
            }),
            loop,
        )

    # DirectConnection: slot chamado diretamente na thread que emitiu o sinal.
    # Necessário porque o Qt event loop não está rodando (sem exec()), então
    # QueuedConnection (padrão cross-thread) nunca processaria os eventos.
    next_dwell.dwell_progress.connect(
        lambda rid, p: asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "dwell_progress",
                "region_id": rid,
                "progress": p,
            }),
            loop,
        ),
        Qt.ConnectionType.DirectConnection,
    )

    next_dwell.dwell_completed.connect(
        lambda rid: asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "dwell_completed",
                "region_id": rid,
            }),
            loop,
        ),
        Qt.ConnectionType.DirectConnection,
    )

    next_dwell.dwell_cancelled.connect(
        lambda rid: asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "dwell_cancelled",
                "region_id": rid,
            }),
            loop,
        ),
        Qt.ConnectionType.DirectConnection,
    )

    next_tracking.add_listener(on_gaze)
    next_tracking.add_listener(next_dwell.on_gaze)
    next_tracking.start()

    previous_tracking = tracking
    tracking = next_tracking
    dwell = next_dwell

    if previous_tracking and previous_tracking.is_running():
        previous_tracking.stop()

    logger.info(f"[API] Tracking iniciado: {tracking.engine_name}")


async def start_tracking(websocket: WebSocket, engine_name: str) -> None:
    """Reinicializa o engine de rastreamento sob demanda e notifica clientes."""
    global tracking

    if tracking and tracking.is_running() and tracking.engine_name == engine_name:
        logger.info(f"[API] Tracking já ativo ({engine_name}) — confirmando para novo cliente")
        await manager.send_to(websocket, {
            "type": "tracking_status",
            "running": True,
            "engine": engine_name,
        })
        return

    try:
        await _start_tracking_engine(engine_name)
        await manager.broadcast({
            "type": "tracking_status",
            "running": True,
            "engine": engine_name,
        })
    except Exception as e:
        await manager.broadcast({"type": "error", "message": str(e)})
        logger.error(f"[API] Erro ao iniciar tracking: {e}")


async def stop_tracking() -> None:
    """Para o tracking ativo e notifica o frontend."""
    global tracking
    if tracking:
        tracking.stop()
        await manager.broadcast({
            "type": "tracking_status",
            "running": False,
            "engine": None,
        })


async def update_dwell_regions(regions: list[dict]) -> None:
    """Registra novas regiões de dwell recebidas do frontend."""
    if not dwell:
        return
    from PyQt6.QtCore import QRect
    dwell.clear_regions()
    for r in regions:
        dwell.register_region(r["id"], QRect(r["x"], r["y"], r["w"], r["h"]))


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "irisflow.api.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
        log_level="info",
    )
