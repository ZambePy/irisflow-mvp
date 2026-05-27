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
    allow_origins=["http://localhost:5173", "http://localhost:5174","http://localhost:*", "http://localhost:5175", "file://"],
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
    logger.info("[API]   WS  /ws")
    logger.info("[API]   GET /health")
    logger.info("[API]   GET /profiles/")
    logger.info("[API]   GET /phrases/categories")


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

    if msg_type == "start_tracking":
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

async def start_tracking(websocket: WebSocket, engine_name: str) -> None:
    """Inicializa o engine de rastreamento e conecta ao DwellController."""
    global tracking, dwell

    # Se já está rodando com o mesmo engine, apenas confirma para este cliente
    if tracking and tracking.is_running() and tracking.engine_name == engine_name:
        logger.info(f"[API] Tracking já ativo ({engine_name}) — confirmando para novo cliente")
        await manager.send_to(websocket, {
            "type": "tracking_status",
            "running": True,
            "engine": engine_name,
        })
        return

    # Captura o loop enquanto estamos em contexto assíncrono
    loop = asyncio.get_running_loop()

    try:
        if tracking and tracking.is_running():
            tracking.stop()

        gaze_engine = create_engine(engine_name)
        tracking = TrackingService(gaze_engine)
        dwell = DwellController(
            dwell_time_ms=config.dwell_time_ms,
            radius_px=config.dwell_radius_px,
        )

        def on_gaze(point) -> None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "gaze",
                    "x": point.x,
                    "y": point.y,
                    "confidence": point.confidence,
                    "timestamp": point.timestamp,
                }),
                loop,
            )

        # DirectConnection: slot chamado diretamente na thread que emitiu o sinal.
        # Necessário porque o Qt event loop não está rodando (sem exec()), então
        # QueuedConnection (padrão cross-thread) nunca processaria os eventos.
        dwell.dwell_progress.connect(
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

        dwell.dwell_completed.connect(
            lambda rid: asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "dwell_completed",
                    "region_id": rid,
                }),
                loop,
            ),
            Qt.ConnectionType.DirectConnection,
        )

        dwell.dwell_cancelled.connect(
            lambda rid: asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "type": "dwell_cancelled",
                    "region_id": rid,
                }),
                loop,
            ),
            Qt.ConnectionType.DirectConnection,
        )

        tracking.add_listener(on_gaze)
        tracking.add_listener(dwell.on_gaze)
        tracking.start()

        await manager.broadcast({
            "type": "tracking_status",
            "running": True,
            "engine": engine_name,
        })
        logger.info(f"[API] Tracking iniciado: {engine_name}")

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
