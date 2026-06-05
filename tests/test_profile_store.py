import pytest

from irisflow.profiles.profile_store import ProfileStore


def test_store_vazio_retorna_lista_vazia(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    assert store.get_all() == []


def test_criar_perfil(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    store.create(name="João", dwell_time_ms=1000, tracking_engine="mock")

    todos = store.get_all()
    assert len(todos) == 1
    assert todos[0].name == "João"
    assert todos[0].dwell_time_ms == 1000
    assert todos[0].id is not None


def test_perfil_persiste_entre_instancias(tmp_profiles_dir):
    path = tmp_profiles_dir / "profiles.json"
    store1 = ProfileStore(path=path)
    store1.create(name="Maria", dwell_time_ms=1500, tracking_engine="eyetrax")

    store2 = ProfileStore(path=path)
    assert len(store2.get_all()) == 1
    assert store2.get_all()[0].name == "Maria"


def test_get_perfil_por_id(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    perfil = store.create(name="Ana", dwell_time_ms=1000, tracking_engine="mock")

    encontrado = store.get(perfil.id)
    assert encontrado is not None
    assert encontrado.name == "Ana"
    assert store.get("id_inexistente") is None


def test_ultimo_usado(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    store.create(name="A", dwell_time_ms=1000, tracking_engine="mock")
    p2 = store.create(name="B", dwell_time_ms=1000, tracking_engine="mock")

    store.set_last_used(p2.id)

    assert store.get_last_used().id == p2.id


def test_deletar_perfil(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    p1 = store.create(name="A", dwell_time_ms=1000, tracking_engine="mock")
    store.create(name="B", dwell_time_ms=1000, tracking_engine="mock")

    store.delete(p1.id)

    assert len(store.get_all()) == 1
    assert store.get(p1.id) is None


def test_atualizar_perfil(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    perfil = store.create(name="X", dwell_time_ms=1000, tracking_engine="mock")

    perfil.dwell_time_ms = 1500
    store.update(perfil)

    assert store.get(perfil.id).dwell_time_ms == 1500


def test_marcar_perfil_como_calibrado(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    perfil = store.create(name="Cal", dwell_time_ms=1000, tracking_engine="iris-gaze-net")

    store.mark_calibrated(
        perfil.id,
        "models/irisflow_base_model.pkl",
        {"accuracy": 0.91, "mae_total": 18.2},
    )

    store2 = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    persisted = store2.get(perfil.id)
    assert persisted.is_calibrated is True
    assert persisted.calibration_model_path == "models/irisflow_base_model.pkl"
    assert persisted.calibration_metrics["accuracy"] == 0.91
    assert persisted.calibrated_at is not None


def test_perfil_sem_last_used_retorna_none(tmp_profiles_dir):
    store = ProfileStore(path=tmp_profiles_dir / "profiles.json")
    assert store.get_last_used() is None
