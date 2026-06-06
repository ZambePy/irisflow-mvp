import numpy as np
import pytest

from irisflow.integrations.irisgazenet.adapter import IrisGazeNetAdapter
from irisflow.integrations.irisgazenet.config import IrisGazeNetConfig
from irisflow.tracking.factory import create_engine


class _StaticSvr:
    support_vectors_ = np.zeros((4, 3), dtype=np.float32)

    def predict(self, values):
        return np.full(len(values), 100.0)


class _DynamicSvr:
    support_vectors_ = np.arange(12, dtype=np.float32).reshape(4, 3)

    def predict(self, values):
        return np.linspace(100.0, 180.0, len(values))


class _Estimator:
    is_calibrated = True
    scaler = object()
    svr_x = _DynamicSvr()
    svr_y = _DynamicSvr()
    training_diagnostics = {
        "validation_prediction_span": {"x": 80.0, "y": 80.0}
    }


def test_mock_engine_still_created():
    assert create_engine("mock").engine_name == "mock"


def test_irisgazenet_rejects_missing_model(tmp_path):
    adapter = IrisGazeNetAdapter(
        IrisGazeNetConfig(model_path=str(tmp_path / "missing.pkl"))
    )

    with pytest.raises(RuntimeError, match="modelo nao encontrado"):
        adapter.start()


def test_irisgazenet_rejects_static_model():
    adapter = IrisGazeNetAdapter(IrisGazeNetConfig(min_prediction_span_px=24.0))
    adapter._estimator = type(
        "Estimator",
        (),
        {
            "is_calibrated": True,
            "scaler": object(),
            "svr_x": _StaticSvr(),
            "svr_y": _DynamicSvr(),
        },
    )()

    with pytest.raises(RuntimeError, match="cursor estatico"):
        adapter._validate_loaded_model()


def test_irisgazenet_accepts_dynamic_model():
    adapter = IrisGazeNetAdapter(IrisGazeNetConfig(min_prediction_span_px=24.0))
    adapter._estimator = _Estimator()

    adapter._validate_loaded_model()


def test_irisgazenet_rejects_legacy_model_without_saved_validation():
    adapter = IrisGazeNetAdapter(IrisGazeNetConfig(min_prediction_span_px=24.0))
    adapter._estimator = type(
        "Estimator",
        (),
        {
            "is_calibrated": True,
            "scaler": object(),
            "svr_x": _DynamicSvr(),
            "svr_y": _DynamicSvr(),
            "training_diagnostics": {},
        },
    )()

    with pytest.raises(RuntimeError, match="modelo legado"):
        adapter._validate_loaded_model()


def test_irisgazenet_rejects_saved_static_calibration_validation():
    adapter = IrisGazeNetAdapter(IrisGazeNetConfig(min_prediction_span_px=24.0))
    adapter._estimator = type(
        "Estimator",
        (),
        {
            "is_calibrated": True,
            "scaler": object(),
            "svr_x": _DynamicSvr(),
            "svr_y": _DynamicSvr(),
            "training_diagnostics": {
                "validation_prediction_span": {"x": 0.0, "y": 80.0}
            },
        },
    )()

    with pytest.raises(RuntimeError, match="validacao de calibracao"):
        adapter._validate_loaded_model()
