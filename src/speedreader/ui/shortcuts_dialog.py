"""Keyboard shortcuts help dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

_SHORTCUTS_HTML = """
<h3>Atajos de teclado</h3>
<table cellspacing="8">
  <tr><td><b>Espacio</b></td><td>Play / Pause</td></tr>
  <tr><td><b>Ctrl+O</b></td><td>Abrir archivo</td></tr>
  <tr><td><b>Ctrl+V</b></td><td>Pegar</td></tr>
  <tr><td><b>← / →</b></td><td>Palabra anterior / siguiente</td></tr>
  <tr><td><b>R</b></td><td>Reiniciar lectura</td></tr>
  <tr><td><b>F11</b></td><td>Pantalla completa</td></tr>
  <tr><td><b>Esc</b></td><td>Salir de pantalla completa</td></tr>
  <tr><td><b>?</b></td><td>Mostrar esta ayuda</td></tr>
</table>
<p>Activa <b>TTS</b> para que la voz marque el ritmo. Con <b>Piper</b> se lee frase a frase con RSVP sincronizado; con Qt, palabra a palabra. El perfil ajusta el ritmo en títulos, párrafos y código.</p>
<p>Arrastra un archivo <code>.txt</code> o <code>.md</code> a la ventana para abrirlo.</p>
"""


class ShortcutsDialog(QDialog):
    """Modal dialog listing keyboard shortcuts."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Atajos de teclado")
        self.setModal(True)
        self.resize(420, 320)

        label = QLabel(_SHORTCUTS_HTML)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
