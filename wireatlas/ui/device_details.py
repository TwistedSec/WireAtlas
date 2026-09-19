from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from wireatlas.models.device import Device


def _display(value: str) -> str:
    return value if value else "—"


class DeviceDetailsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.empty_label = QLabel("No device selected")

        self.form_widget = QWidget()
        form_layout = QFormLayout(self.form_widget)

        self.name_value = QLabel("—")
        self.hostname_value = QLabel("—")
        self.type_value = QLabel("—")
        self.ip_value = QLabel("—")
        self.subnet_mask_value = QLabel("—")
        self.subnet_value = QLabel("—")
        self.vlan_value = QLabel("—")
        self.mac_value = QLabel("—")
        self.vendor_value = QLabel("—")
        self.root_value = QLabel("No")

        self.notes_value = QPlainTextEdit()
        self.notes_value.setReadOnly(True)
        self.notes_value.setMaximumHeight(120)

        form_layout.addRow("Name:", self.name_value)
        form_layout.addRow("Hostname:", self.hostname_value)
        form_layout.addRow("Device Type:", self.type_value)
        form_layout.addRow("IP Address:", self.ip_value)
        form_layout.addRow("Subnet Mask:", self.subnet_mask_value)
        form_layout.addRow("Subnet:", self.subnet_value)
        form_layout.addRow("VLAN:", self.vlan_value)
        form_layout.addRow("MAC Address:", self.mac_value)
        form_layout.addRow("Vendor:", self.vendor_value)
        form_layout.addRow("Root Device:", self.root_value)
        form_layout.addRow("Notes:", self.notes_value)

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.form_widget)
        layout.addStretch()

        self.clear()

    def clear(self) -> None:
        self.empty_label.show()
        self.form_widget.hide()

    def show_device(
        self,
        device: Device,
        is_root: bool = False,
    ) -> None:
        self.name_value.setText(device.name)
        self.hostname_value.setText(_display(device.hostname))
        self.type_value.setText(device.device_type.value)
        self.ip_value.setText(_display(device.ip_address))
        self.subnet_mask_value.setText(
            _display(device.subnet_mask)
        )
        self.subnet_value.setText(_display(device.subnet))
        self.vlan_value.setText(_display(device.vlan_id))
        self.mac_value.setText(_display(device.mac_address))
        self.vendor_value.setText(_display(device.vendor))
        self.notes_value.setPlainText(_display(device.notes))
        self.root_value.setText("Yes" if is_root else "No")

        self.empty_label.hide()
        self.form_widget.show()