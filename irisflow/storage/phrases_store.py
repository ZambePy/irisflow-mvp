"""Armazenamento e acesso às frases rápidas por contexto."""
import json
from pathlib import Path

from irisflow.core.logger import logger

_DEFAULT_DATA: dict = {
    "categorias": [
        {
            "id": "saude",
            "nome": "Saúde",
            "icone": "🏥",
            "frases": [
                "Estou com dor",
                "Preciso de medicação",
                "Chame o médico",
                "Estou com falta de ar",
                "Preciso me mexer",
                "Estou com febre",
            ],
        },
        {
            "id": "necessidades",
            "nome": "Necessidades",
            "icone": "🍽️",
            "frases": [
                "Estou com fome",
                "Estou com sede",
                "Preciso ir ao banheiro",
                "Estou com frio",
                "Estou com calor",
                "Quero descansar",
            ],
        },
        {
            "id": "social",
            "nome": "Social",
            "icone": "💬",
            "frases": [
                "Bom dia",
                "Boa tarde",
                "Boa noite",
                "Obrigado",
                "Por favor",
                "Eu te amo",
            ],
        },
        {
            "id": "emocoes",
            "nome": "Emoções",
            "icone": "😊",
            "frases": [
                "Estou bem",
                "Estou cansado",
                "Estou com medo",
                "Estou feliz",
                "Estou triste",
                "Preciso de ajuda",
            ],
        },
    ]
}


class PhrasesStore:
    _PATH: Path = Path(__file__).parent / "phrases.json"

    def __init__(self) -> None:
        self._data = self.load()

    def load(self) -> dict:
        if not self._PATH.exists():
            self._PATH.write_text(
                json.dumps(_DEFAULT_DATA, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("[PhrasesStore] phrases.json criado com dados padrão")
            return _DEFAULT_DATA
        with open(self._PATH, encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"[PhrasesStore] Carregado: {len(data.get('categorias', []))} categorias")
        return data

    def _save(self) -> None:
        self._PATH.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_categories(self) -> list[dict]:
        return self._data.get("categorias", [])

    def get_phrases(self, category_id: str) -> list[str]:
        for cat in self._data.get("categorias", []):
            if cat["id"] == category_id:
                return cat.get("frases", [])
        logger.warning(f"[PhrasesStore] Categoria '{category_id}' não encontrada")
        return []

    def add_phrase(self, category_id: str, text: str) -> None:
        for cat in self._data.get("categorias", []):
            if cat["id"] == category_id:
                cat["frases"].append(text)
                self._save()
                logger.info(f"[PhrasesStore] Frase adicionada em '{category_id}': {text}")
                return
        logger.warning(f"[PhrasesStore] Categoria '{category_id}' não encontrada")

    def remove_phrase(self, category_id: str, text: str) -> None:
        for cat in self._data.get("categorias", []):
            if cat["id"] == category_id:
                cat["frases"] = [f for f in cat["frases"] if f != text]
                self._save()
                logger.info(f"[PhrasesStore] Frase removida de '{category_id}': {text}")
                return
        logger.warning(f"[PhrasesStore] Categoria '{category_id}' não encontrada")
