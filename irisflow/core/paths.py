"""
paths.py — Utilitário de caminhos para empacotamento com PyInstaller.
"""
import os
import sys
from pathlib import Path


def get_user_data_dir() -> Path:
    """
    Retorna o diretório persistente para gravar dados do usuário.
    Garante que persista fora do diretório temporário do PyInstaller (_MEIPASS).
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"

    data_dir = base / "IrisFlow"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_resource_path(relative_path: str) -> Path:
    """
    Resolve caminhos de arquivos estáticos/leitura.
    Suporta o empacotamento de recursos via PyInstaller (_MEIPASS).
    """
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        # Raiz do projeto (irisflow-mvp)
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path
