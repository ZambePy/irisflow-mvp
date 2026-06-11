import pytest

from irisflow.tracking.factory import create_engine
from irisflow.tracking.mock_engine import MockGazeEngine


def test_cria_mock_engine(app_qt):
    engine = create_engine("mock")
    assert engine.engine_name == "mock"
    assert isinstance(engine, MockGazeEngine)


def test_engine_invalido_levanta_erro(app_qt):
    with pytest.raises(ValueError):
        create_engine("engine_que_nao_existe")


def test_mock_engine_nao_esta_rodando_ao_criar(app_qt):
    engine = create_engine("mock")
    assert engine.is_running() is False


def test_mock_engine_inicia_e_para(app_qt):
    engine = create_engine("mock")

    engine.start()
    assert engine.is_running() is True

    engine.stop()
    assert engine.is_running() is False
