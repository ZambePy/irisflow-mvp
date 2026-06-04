"""
ProfileStore — persistência de perfis em JSON local.
"""
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from irisflow.profiles.profile import Profile
from irisflow.core.logger import logger

_STORE_PATH = Path(__file__).parent / "profiles.json"


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        self._store_path = path if path is not None else _STORE_PATH
        self._profiles: dict[str, Profile] = {}
        self.load()

    # ── Persistência ──────────────────────────────────────────────────────

    def load(self) -> None:
        if not self._store_path.exists():
            self._store_path.write_text("[]", encoding="utf-8")
            return
        try:
            data = json.loads(self._store_path.read_text(encoding="utf-8"))
            self._profiles = {d["id"]: self._from_dict(d) for d in data}
            logger.debug(f"[ProfileStore] {len(self._profiles)} perfis carregados")
        except Exception as e:
            logger.error(f"[ProfileStore] Erro ao carregar perfis: {e}")
            self._profiles = {}

    def save(self) -> None:
        try:
            data = [asdict(p) for p in self._profiles.values()]
            self._store_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"[ProfileStore] Erro ao salvar perfis: {e}")

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_all(self) -> list[Profile]:
        return list(self._profiles.values())

    def get(self, profile_id: str) -> Profile | None:
        return self._profiles.get(profile_id)

    def get_last_used(self) -> Profile | None:
        if not self._profiles:
            return None
        return max(self._profiles.values(), key=lambda p: p.last_used_at)

    # ── Mutações ─────────────────────────────────────────────────────────

    def create(
        self,
        name: str,
        dwell_time_ms: int = 1000,
        tracking_engine: str = "mock",
    ) -> Profile:
        profile = Profile(
            name=name,
            dwell_time_ms=dwell_time_ms,
            tracking_engine=tracking_engine,
        )
        self._profiles[profile.id] = profile
        self.save()
        logger.info(f"[ProfileStore] Perfil criado: {profile.name} ({profile.id})")
        return profile

    def update(self, profile: Profile) -> Profile:
        self._profiles[profile.id] = profile
        self.save()
        return profile

    def delete(self, profile_id: str) -> None:
        if profile_id in self._profiles:
            name = self._profiles[profile_id].name
            del self._profiles[profile_id]
            self.save()
            logger.info(f"[ProfileStore] Perfil excluído: {name} ({profile_id})")

    def set_last_used(self, profile_id: str) -> None:
        profile = self._profiles.get(profile_id)
        if profile:
            profile.last_used_at = datetime.now(timezone.utc).isoformat()
            self.save()

    # ── Helper ────────────────────────────────────────────────────────────

    @staticmethod
    def _from_dict(d: dict) -> Profile:
        now = datetime.now(timezone.utc).isoformat()
        return Profile(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", ""),
            dwell_time_ms=d.get("dwell_time_ms", 1000),
            tracking_engine=d.get("tracking_engine", "mock"),
            favorite_phrases=d.get("favorite_phrases", []),
            created_at=d.get("created_at", now),
            last_used_at=d.get("last_used_at", now),
        )
