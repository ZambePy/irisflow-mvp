"""
TTSEngine — Text-to-Speech em português usando pyttsx3.
Roda em thread separada para não bloquear a UI.
"""
import threading
from irisflow.core.logger import logger


class TTSEngine:
    """Sintetizador de voz offline para PT-BR."""

    def __init__(self, rate: int = 160) -> None:
        self._rate = rate
        self._engine = None
        self._lock = threading.Lock()
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            # Tentar selecionar voz PT-BR
            voices = self._engine.getProperty("voices")
            for voice in voices:
                if "brazil" in voice.name.lower() or "portuguese" in voice.id.lower():
                    self._engine.setProperty("voice", voice.id)
                    break
            logger.info("[TTS] pyttsx3 inicializado")
        except Exception as e:
            logger.warning(f"[TTS] pyttsx3 não disponível: {e}. TTS desabilitado.")
            self._engine = None

    def speak(self, text: str) -> None:
        """Fala o texto em thread separada (não bloqueia a UI)."""
        if not self._engine:
            logger.info(f"[TTS] (sem engine) Texto: {text!r}")
            return
        thread = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
        thread.start()

    def _speak_sync(self, text: str) -> None:
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                logger.error(f"[TTS] Erro ao falar: {e}")
