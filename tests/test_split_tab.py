import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QMessageBox

from src.tabs.split_tab import SplitTab


def test_on_split_finished_resets_file_label_and_state(qtbot, monkeypatch):
    tab = SplitTab()
    qtbot.addWidget(tab)

    tab.selected_split_file = "input.pdf"
    tab.file_label.setText("input.pdf")
    tab.split_button.setEnabled(False)

    tab.progress_dialog = SimpleNamespace(close=lambda: None)
    tab.preview = SimpleNamespace(clear=lambda: None)

    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    tab.on_split_finished("output.pdf")

    assert tab.file_label.text() == "No file selected."
    assert tab.selected_split_file is None
    assert tab.split_button.isEnabled()
