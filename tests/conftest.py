"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication for UI tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    yield application
