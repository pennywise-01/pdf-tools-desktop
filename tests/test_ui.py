import pytest
from PyQt6.QtWidgets import QApplication
from src.main import MainWindow

def test_main_window_creation(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "PDF Tools Desktop"
