import pytest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from src.main import MainWindow, resource_path
from src.widgets.feature_tab import ElidedFileLabel

def test_main_window_creation(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "PDF Tools Desktop"


def test_file_label_elides_long_filename_when_narrow(qtbot):
    label = ElidedFileLabel()
    qtbot.addWidget(label)
    label.resize(140, 28)

    long_name = "c16b9c7a-29cf-4596-9a73-4131540910d893b312af69b3da2c0b6f89a-report.xlsx"
    label.setText(long_name)

    assert label.text() != long_name
    assert label.toolTip() == long_name


def test_resource_path_resolves_stylesheet_from_src_cwd(monkeypatch):
    tests_dir = Path(__file__).resolve().parent
    project_root = tests_dir.parent
    src_dir = project_root / "src"
    monkeypatch.chdir(src_dir)

    stylesheet_path = Path(resource_path("src/style.qss"))
    assert stylesheet_path.exists()
