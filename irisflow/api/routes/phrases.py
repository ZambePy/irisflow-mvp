"""Rotas REST para categorias e frases rápidas."""

from fastapi import APIRouter

from irisflow.storage.phrases_store import PhrasesStore

router = APIRouter()
store = PhrasesStore()

_ICON_MAP = {
    "saude":        "medical_services",
    "necessidades": "restaurant",
    "social":       "forum",
    "emocoes":      "favorite",
}


@router.get("/categories")
def get_categories() -> list[dict]:
    """Retorna categorias no formato esperado pelo frontend."""
    return [
        {
            "id":    cat["id"],
            "label": cat["nome"],
            "icon":  _ICON_MAP.get(cat["id"], "chat"),
            "count": len(cat.get("frases", [])),
        }
        for cat in store.get_categories()
    ]


@router.get("/{category_id}")
def get_phrases(category_id: str) -> list[str]:
    """Retorna as frases de uma categoria específica."""
    return store.get_phrases(category_id)


@router.post("/{category_id}")
def add_phrase(category_id: str, text: str) -> dict:
    """Adiciona uma frase a uma categoria."""
    store.add_phrase(category_id, text)
    return {"ok": True}


@router.delete("/{category_id}")
def remove_phrase(category_id: str, text: str) -> dict:
    """Remove uma frase de uma categoria."""
    store.remove_phrase(category_id, text)
    return {"ok": True}
