"""
TTSEngine — Text-to-Speech em português.
No Windows usa PowerShell + SAPI (thread-safe); em outros SOs usa pyttsx3.
Roda em thread separada para não bloquear a UI.
"""
import subprocess
import sys
import threading
from irisflow.core.logger import logger

# Taxa SAPI: -10 (lento) a 10 (rápido); 1 = ligeiramente acima do padrão
_SAPI_RATE = 1


class TTSEngine:
    """Sintetizador de voz offline para PT-BR."""

    def __init__(self, rate: int = 160) -> None:
        self._pyttsx3_rate = rate
        self._lock = threading.Lock()
        self._engine = None

        if sys.platform == "win32":
            logger.info("[TTS] Windows detectado — usando SAPI via PowerShell")
        else:
            self._init_pyttsx3()

    def _init_pyttsx3(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._pyttsx3_rate)
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
        logger.info(f"[TTS] speak({text!r})")
        threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def _speak_sync(self, text: str) -> None:
        with self._lock:
            if sys.platform == "win32":
                self._speak_sapi(text)
            else:
                self._speak_pyttsx3(text)

    def _speak_sapi(self, text: str) -> None:
        safe = text.replace("'", "''")
        ps_cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate = {_SAPI_RATE}; "
            f"$s.Speak('{safe}')"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                timeout=15,
            )
            if result.returncode != 0:
                err = result.stderr.decode(errors="replace").strip()
                logger.error(f"[TTS] SAPI falhou (rc={result.returncode}): {err}")
        except Exception as e:
            logger.error(f"[TTS] Erro ao chamar PowerShell: {e}")

    def _speak_pyttsx3(self, text: str) -> None:
        if not self._engine:
            logger.info(f"[TTS] (sem engine) Texto: {text!r}")
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            logger.error(f"[TTS] pyttsx3 erro: {e}")
