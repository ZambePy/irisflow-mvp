import pytest
from dataclasses import FrozenInstanceError

from irisflow.tracking.types import GazePoint


def test_gaze_point_valido():
    assert GazePoint(x=100, y=200, confidence=0.9).is_valid() is True


def test_gaze_point_invalido_baixa_confianca():
    assert GazePoint(x=100, y=200, confidence=0.3).is_valid() is False


def test_gaze_point_no_limite_valido():
    assert GazePoint(x=0, y=0, confidence=0.4).is_valid() is True


def test_distancia_mesma_posicao():
    p = GazePoint(x=100, y=100)
    assert p.distance_to(p) == 0.0


def test_distancia_conhecida():
    p1 = GazePoint(x=0, y=0)
    p2 = GazePoint(x=3, y=4)
    assert p1.distance_to(p2) == 5.0


def test_gaze_point_imutavel():
    p = GazePoint(x=100, y=200, confidence=0.9)
    with pytest.raises(FrozenInstanceError):
        p.x = 999


def test_repr_legivel():
    r = repr(GazePoint(x=100, y=200, confidence=0.9))
    assert "100" in r
    assert "200" in r


def test_timestamp_gerado_automaticamente():
    assert GazePoint(x=0, y=0).timestamp > 0
