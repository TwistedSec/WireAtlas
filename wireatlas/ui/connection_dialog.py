from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from wireatlas.models.connection import Connection, LinkType
from wireatlas.models.device import Device


class ConnectionDialog(QDialog):
    def __init__(
        self,
        devices: list[Device],
        parent=None,
    ):
        super().__init__(parent)

        self.source_combo = QComboBox()
        self.destination_combo = QComboBox()

        self.source_interface_input = QLineEdit()
        self.destination_interface_input = QLineEdit()
        self.link_type_combo = QComboBox()
        self.notes_input = QLineEdit()
        self.cancel_button = QPushButton("Cancel")
        self.add_button = QPushButton("Add")
        self.add_button.setEnabled(False)

        for device in devices:
            label = device.name

            if device.ip_address:
                label = (
                    f"{device.name} — "
                    f"{device.ip_address}"
                )

            self.source_combo.addItem(
                label,
                device.id,
            )

            self.destination_combo.addItem(
                label,
                device.id,
            )

        for link_type in LinkType:
            self.link_type_combo.addItem(
                link_type.value,
                link_type,
            )

        form_layout = QFormLayout()

        form_layout.addRow(
            "Source",
            self.source_combo,
        )

        form_layout.addRow(
            "Source Interface",
            self.source_interface_input,
        )

        form_layout.addRow(
            "Destination",
            self.destination_combo,
        )

        form_layout.addRow(
            "Destination Interface",
            self.destination_interface_input,
        )

        form_layout.addRow(
            "Link Type",
            self.link_type_combo,
        )

        form_layout.addRow(
            "Notes",
            self.notes_input,
        )

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.add_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.source_combo.currentIndexChanged.connect(
            self._update_validation
        )

        self.destination_combo.currentIndexChanged.connect(
            self._update_validation
        )

        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self.accept)

        self._update_validation()

    def build_connection(self) -> Connection:
        return Connection(
            source_device_id=self.source_combo.currentData(),
            destination_device_id=self.destination_combo.currentData(),
            source_interface=self.source_interface_input.text(),
            destination_interface=self.destination_interface_input.text(),
            link_type=self.link_type_combo.currentData(),
            notes=self.notes_input.text(),
        )

    def is_valid(self) -> bool:
        return (
            self.source_combo.currentData()
            != self.destination_combo.currentData()
        )

    def _update_validation(self) -> None:
        self.add_button.setEnabled(
            self.is_valid()
        )