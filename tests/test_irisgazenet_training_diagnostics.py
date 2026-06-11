import numpy as np

from training.model import IrisGazeEstimator


def test_calibrate_records_diagnostics_and_varied_predictions():
    rng = np.random.default_rng(7)
    n = 36
    features = rng.normal(size=(n, 12)).astype(np.float32)
    targets = np.column_stack(
        [
            np.linspace(100.0, 900.0, n),
            np.linspace(200.0, 700.0, n),
        ]
    ).astype(np.float32)

    estimator = IrisGazeEstimator(pretrained=False)
    metrics = estimator.calibrate(
        face_images=None,
        left_images=None,
        right_images=None,
        rects=None,
        targets=targets,
        features=features,
        svr_kernel="linear",
    )

    diagnostics = metrics["diagnostics"]
    assert diagnostics["n_samples"] == n
    assert diagnostics["unique_target_points"] == n
    assert diagnostics["screen_x"]["std"] > 0
    assert diagnostics["screen_y"]["std"] > 0
    assert diagnostics["features"]["std"] > 0
    assert len(diagnostics["first_5_labels"]) == 5
    assert len(diagnostics["first_5_predictions_before_smoothing"]) == 5
    assert len(diagnostics["train_loss_progression"]) == 3
    assert metrics["prediction_span_x"] > 24.0
    assert metrics["prediction_span_y"] > 24.0
