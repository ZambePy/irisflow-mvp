import sys
import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def app_qt():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    yield app


@pytest.fixture
def tmp_profiles_dir(tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    return d


@pytest.fixture
def tmp_phrases_dir(tmp_path):
    d = tmp_path / "phrases"
    d.mkdir()
    return d
