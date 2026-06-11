"""Rotas REST para gerenciamento de perfis de usuário."""

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from irisflow.profiles.profile_store import ProfileStore

router = APIRouter()
store = ProfileStore()


class CreateProfileBody(BaseModel):
    name: str
    dwell_time_ms: int = 1000
    tracking_engine: str = "mock"


@router.get("/")
def list_profiles() -> list[dict]:
    """Retorna todos os perfis cadastrados."""
    return [asdict(p) for p in store.get_all()]


@router.get("/last-used")
def get_last_used() -> dict | None:
    """Retorna o perfil utilizado mais recentemente."""
    p = store.get_last_used()
    return asdict(p) if p else None


@router.post("/")
def create_profile(body: CreateProfileBody) -> dict:
    """Cria e persiste um novo perfil."""
    p = store.create(
        name=body.name,
        dwell_time_ms=body.dwell_time_ms,
        tracking_engine=body.tracking_engine,
    )
    return asdict(p)


@router.put("/{profile_id}/last-used")
def set_last_used(profile_id: str) -> dict:
    """Atualiza o timestamp de último uso do perfil."""
    store.set_last_used(profile_id)
    return {"ok": True}


@router.delete("/{profile_id}")
def delete_profile(profile_id: str) -> dict:
    """Remove um perfil pelo ID."""
    store.delete(profile_id)
    return {"ok": True}
