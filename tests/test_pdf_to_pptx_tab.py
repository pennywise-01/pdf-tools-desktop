import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import src.tabs.pdf_to_pptx_tab as pdf_to_pptx_tab_module
from src.tabs.pdf_to_pptx_tab import PDFToPPTXTab


def test_pdf_to_pptx_tab_initializes_experimental_checkbox_and_mode_label(qtbot):
    tab = PDFToPPTXTab()
    qtbot.addWidget(tab)

    assert tab.experimental_pdftoppt_checkbox is not None
    assert tab.mode_label is not None


def test_run_action_passes_experimental_toggle_to_worker(qtbot, monkeypatch):
    tab = PDFToPPTXTab()
    qtbot.addWidget(tab)

    tab.selected_file = "input.pdf"
    tab.experimental_pdftoppt_checkbox.setChecked(True)

    monkeypatch.setattr(
        pdf_to_pptx_tab_module.QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("output.pptx", "PowerPoint Files (*.pptx)"),
    )

    captured = {}

    class _FakeWorker:
        def __init__(self, input_path, output_path, enable_pdftoppt=False):
            captured["input_path"] = input_path
            captured["output_path"] = output_path
            captured["enable_pdftoppt"] = enable_pdftoppt
            self.finished = SimpleNamespace(connect=lambda *_: None)
            self.error = SimpleNamespace(connect=lambda *_: None)

        def start(self):
            return None

    monkeypatch.setattr(pdf_to_pptx_tab_module, "PDFToPPTXWorker", _FakeWorker)

    tab.run_action()

    assert captured["input_path"] == "input.pdf"
    assert captured["output_path"] == "output.pptx"
    assert captured["enable_pdftoppt"] is True
