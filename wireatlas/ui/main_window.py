from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from wireatlas.core.document import MapDocument
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap
from wireatlas.ui.device_details import DeviceDetailsPanel
from wireatlas.ui.device_dialog import DeviceDialog
from wireatlas.ui.topology_view import TopologyView


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.document = MapDocument()

        self._build_toolbar()
        self._build_central_widget()

        self.add_device_action.triggered.connect(
            self._open_add_device_dialog
        )

        self.topology_view.device_selected.connect(
            self._show_device_details
        )

        self.statusBar().showMessage("Ready")
        self._update_window_title()

    @property
    def network_map(self) -> NetworkMap:
        return self.document.network_map

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        self.new_action = toolbar.addAction("New")
        self.open_action = toolbar.addAction("Open")
        self.save_action = toolbar.addAction("Save")
        self.add_device_action = toolbar.addAction("Add Device")
        self.add_connection_action = toolbar.addAction(
            "Add Connection"
        )
        self.export_pdf_action = toolbar.addAction(
            "Export PDF"
        )

        self.new_action.setEnabled(False)
        self.open_action.setEnabled(False)
        self.save_action.setEnabled(False)
        self.add_connection_action.setEnabled(False)
        self.export_pdf_action.setEnabled(False)

    def _build_central_widget(self) -> None:
        central_widget = QWidget()
        outer_layout = QVBoxLayout(central_widget)

        site_layout = QHBoxLayout()
        site_layout.addWidget(QLabel("Site:"))

        self.site_name_input = QLineEdit(
            self.network_map.site_name
        )
        self.site_name_input.textChanged.connect(
            self._update_site_name
        )
        site_layout.addWidget(self.site_name_input)

        outer_layout.addLayout(site_layout)

        self.main_splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.topology_view = TopologyView()
        self.details_panel = DeviceDetailsPanel()

        self.main_splitter.addWidget(self.topology_view)
        self.main_splitter.addWidget(self.details_panel)

        self.main_splitter.setStretchFactor(0, 4)
        self.main_splitter.setStretchFactor(1, 1)

        self.main_splitter.setSizes([900, 300])

        outer_layout.addWidget(self.main_splitter)

        self.setCentralWidget(central_widget)

    def _update_window_title(self) -> None:
        marker = " *" if self.document.dirty else ""
        self.setWindowTitle(
            f"WireAtlas — {self.network_map.site_name}{marker}"
        )

    def _mark_dirty(self) -> None:
        self.document.mark_dirty()
        self._update_window_title()

    def _update_site_name(self, value: str) -> None:
        self.network_map.site_name = value
        self._mark_dirty()

    def add_device(self, device: Device) -> None:
        if (
            not self.network_map.root_device_id
            and device.device_type
            == DeviceType.FIREWALL_ROUTER
        ):
            self.network_map.root_device_id = device.id

        self.network_map.devices.append(device)
        self.topology_view.add_device(device)
        self._mark_dirty()

    def _open_add_device_dialog(self) -> None:
        dialog = DeviceDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_device(dialog.build_device())

    def _show_device_details(
        self,
        device_id: str,
    ) -> None:
        device = next(
            (
                device
                for device in self.network_map.devices
                if device.id == device_id
            ),
            None,
        )

        if device is None:
            self.details_panel.clear()
            return

        self.details_panel.show_device(
            device,
            is_root=(
                device.id
                == self.network_map.root_device_id
            ),
        )
