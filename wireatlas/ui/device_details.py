from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DeviceDetailsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.empty_label = QLabel("No device selected")

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addStretch()