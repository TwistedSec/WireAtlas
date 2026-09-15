from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from wireatlas.core.validation import is_valid_ip, is_valid_mac
from wireatlas.models.device import Device, DeviceType


class DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Device")

        self.name_input = QLineEdit()

        self.type_combo = QComboBox()
        self.type_combo.addItem("Select device type…", None)

        for device_type in DeviceType:
            self.type_combo.addItem(
                device_type.value,
                device_type,
            )

        self.ip_input = QLineEdit()
        self.mac_input = QLineEdit()
        self.vlan_input = QLineEdit()
        self.subnet_input = QLineEdit()
        self.notes_input = QPlainTextEdit()

        self.ip_error = QLabel("")
        self.mac_error = QLabel("")

        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Device Type:", self.type_combo)
        form_layout.addRow("IP Address:", self.ip_input)
        form_layout.addRow("", self.ip_error)
        form_layout.addRow("MAC Address:", self.mac_input)
        form_layout.addRow("", self.mac_error)
        form_layout.addRow("VLAN:", self.vlan_input)
        form_layout.addRow("Subnet:", self.subnet_input)
        form_layout.addRow("Notes:", self.notes_input)

        self.cancel_button = QPushButton("Cancel")
        self.add_button = QPushButton("Add")
        self.add_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.add_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)

        self.name_input.textChanged.connect(
            self._update_validation
        )
        self.type_combo.currentIndexChanged.connect(
            self._update_validation
        )
        self.ip_input.textChanged.connect(
            self._update_validation
        )
        self.mac_input.textChanged.connect(
            self._update_validation
        )

        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self.accept)

        self._update_validation()

    def _update_validation(self) -> None:
        name_valid = bool(
            self.name_input.text().strip()
        )
        type_valid = (
            self.type_combo.currentData() is not None
        )

        ip_value = self.ip_input.text().strip()
        mac_value = self.mac_input.text().strip()

        ip_valid = is_valid_ip(ip_value)
        mac_valid = is_valid_mac(mac_value)

        self.ip_error.setText(
            "" if ip_valid
            else "Enter a valid IP address."
        )

        self.mac_error.setText(
            "" if mac_valid
            else "Enter a valid MAC address."
        )

        self.add_button.setEnabled(
            name_valid
            and type_valid
            and ip_valid
            and mac_valid
        )

    def build_device(self) -> Device:
        values = {
            "name": self.name_input.text().strip(),
            "device_type": self.type_combo.currentData(),
            "ip_address": self.ip_input.text().strip(),
            "mac_address": self.mac_input.text().strip(),
            "vlan_id": self.vlan_input.text().strip(),
            "subnet": self.subnet_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

        field_sources = {
            field_name: "manual"
            for field_name, value in values.items()
            if value not in ("", None)
        }

        return Device(
            name=values["name"],
            device_type=values["device_type"],
            ip_address=values["ip_address"],
            mac_address=values["mac_address"],
            vlan_id=values["vlan_id"],
            subnet=values["subnet"],
            notes=values["notes"],
            field_sources=field_sources,
        )