"""Application entry point for the speedreader GUI."""

from PySide6.QtWidgets import QApplication

from speedreader.ui.main_window import MainWindow


def main() -> None:
    """Launch the speedreader desktop application."""
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
