import os

from src import main as main_module
from features import pdf_to_pptx as p2p


def test_maybe_bootstrap_libreoffice_launches_when_missing(monkeypatch):
    monkeypatch.setenv("PDF_TOOLS_AUTO_SETUP_LIBREOFFICE", "1")
    monkeypatch.setattr(main_module.sys, "platform", "win32")
    monkeypatch.setattr(p2p, "find_libreoffice", lambda: None)

    fake_setup = "C:/tmp/setup_libreoffice.py"
    monkeypatch.setattr(main_module, "resource_path", lambda _rel: fake_setup)

    original_exists = os.path.exists
    monkeypatch.setattr(main_module.os.path, "exists", lambda path: True if path == fake_setup else original_exists(path))

    calls = []

    class _FakeProcess:
        pass

    def _fake_popen(cmd, creationflags=0):
        calls.append((cmd, creationflags))
        return _FakeProcess()

    monkeypatch.setattr(main_module.subprocess, "Popen", _fake_popen)

    launched = main_module.maybe_bootstrap_libreoffice()

    assert launched is True
    assert len(calls) == 1
    assert calls[0][0][0] == main_module.sys.executable
    assert calls[0][0][1] == fake_setup


def test_maybe_bootstrap_libreoffice_respects_disable_env(monkeypatch):
    monkeypatch.setenv("PDF_TOOLS_AUTO_SETUP_LIBREOFFICE", "0")
    launched = main_module.maybe_bootstrap_libreoffice()
    assert launched is False
