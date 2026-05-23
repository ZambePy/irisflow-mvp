"""Gerenciador de conexões WebSocket do IrisFlow."""

import json
from fastapi import WebSocket

from irisflow.core.logger import logger


class ConnectionManager:
    """Gerencia todas as conexões WebSocket ativas."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita e registra nova conexão WebSocket."""
        await websocket.accept()
        self._active.append(websocket)
        logger.info(f"[WS] Cliente conectado — total: {len(self._active)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove conexão encerrada da lista de ativos."""
        if websocket in self._active:
            self._active.remove(websocket)
        logger.info(f"[WS] Cliente desconectado — total: {len(self._active)}")

    async def broadcast(self, message: dict) -> None:
        """Envia mensagem JSON para todos os clientes conectados."""
        if not self._active:
            return
        payload = json.dumps(message, ensure_ascii=False)
        mortos: list[WebSocket] = []
        for ws in list(self._active):
            try:
                await ws.send_text(payload)
            except Exception:
                mortos.append(ws)
        for ws in mortos:
            self.disconnect(ws)

    async def send_to(self, websocket: WebSocket, message: dict) -> None:
        """Envia mensagem JSON para um cliente específico."""
        payload = json.dumps(message, ensure_ascii=False)
        try:
            await websocket.send_text(payload)
        except Exception as e:
            logger.error(f"[WS] Erro ao enviar para cliente: {e}")
            self.disconnect(websocket)
