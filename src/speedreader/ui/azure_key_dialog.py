"""Modal dialog for entering the Azure Speech subscription key + region."""

from __future__ import annotations

import threading

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from speedreader.settings import (
    get_azure_key,
    get_azure_region,
    set_azure_key,
    set_azure_region,
)


class AzureKeyDialog(QDialog):
    """Collect the Azure Speech subscription key and region.

    The test button runs in a worker thread to avoid blocking the UI. The
    Save button persists the values via ``keyring`` (never ``QSettings``).
    """

    _test_finished = Signal(bool, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Voces TTS — Azure")
        self.setModal(True)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Pega tu key de Azure Speech Service y la región (ej. eastus).\n"
            "La key se guarda en el keyring del sistema, no en disco plano."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        region_row = QHBoxLayout()
        region_row.addWidget(QLabel("Región:"))
        self._region_edit = QLineEdit(get_azure_region())
        self._region_edit.setPlaceholderText("eastus")
        region_row.addWidget(self._region_edit)
        layout.addLayout(region_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("Key:"))
        self._key_edit = QLineEdit(get_azure_key() or "")
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_row.addWidget(self._key_edit)
        layout.addLayout(key_row)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        buttons = QDialogButtonBox(self)
        self._test_button = QPushButton("Test")
        self._save_button = buttons.addButton(
            "Save", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._clear_button = QPushButton("Clear")
        buttons.addButton(
            self._clear_button, QDialogButtonBox.ButtonRole.ActionRole
        )
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)

        self._test_button.clicked.connect(self._on_test_clicked)
        self._save_button.clicked.connect(self._on_save_clicked)
        self._clear_button.clicked.connect(self._on_clear_clicked)
        buttons.rejected.connect(self.reject)

        self._test_finished.connect(self._on_test_finished)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_test_clicked(self) -> None:
        region = self._region_edit.text().strip() or "eastus"
        key = self._key_edit.text().strip()
        if not key:
            self._status_label.setText("Ingresa una key primero.")
            return
        self._test_button.setEnabled(False)
        self._status_label.setText("Probando…")

        def worker() -> None:
            ok = False
            message = ""
            try:
                import azure.cognitiveservices.speech as speechsdk  # type: ignore

                config = speechsdk.SpeechConfig(subscription=key, region=region)
                synth = speechsdk.SpeechSynthesizer(speech_config=config)
                voices = synth.get_voices_async().get(timeout=5)
                ok = bool(voices)
                message = (
                    f"OK — {len(voices)} voces disponibles." if ok else "Sin voces."
                )
            except Exception as exc:
                message = f"Error: {exc}"
            self._test_finished.emit(ok, message)

        threading.Thread(target=worker, daemon=True).start()

    def _on_test_finished(self, ok: bool, message: str) -> None:
        self._test_button.setEnabled(True)
        self._status_label.setText(message)

    def _on_save_clicked(self) -> None:
        key = self._key_edit.text().strip()
        region = self._region_edit.text().strip() or "eastus"
        if not key:
            QMessageBox.warning(
                self,
                "Falta key",
                "Ingresa una key antes de guardar.",
            )
            return
        try:
            set_azure_key(key)
            set_azure_region(region)
        except Exception as exc:
            QMessageBox.critical(
                self, "No se pudo guardar", f"Error al escribir keyring: {exc}"
            )
            return
        self.accept()

    def _on_clear_clicked(self) -> None:
        try:
            set_azure_key(None)
            set_azure_region("eastus")
        except Exception:
            pass
        self._key_edit.clear()
        self._region_edit.setText("eastus")
        self._status_label.setText("Key borrada del keyring.")

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @staticmethod
    def _alert_alignment() -> Qt.AlignmentFlag:
        return Qt.AlignmentFlag.AlignLeft