"""Application entry point for the speedreader GUI."""

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from speedreader.paths import app_icon_path
from speedreader.ui.main_window import MainWindow


def main() -> None:
    """Launch the speedreader desktop application."""
    app = QApplication([])
    icon_path = app_icon_path()
    if icon_path.is_file():
        icon = QIcon(str(icon_path))
        app.setWindowIcon(icon)
    window = MainWindow()
    if icon_path.is_file():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    app.exec()
