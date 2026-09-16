from pathlib import Path
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from wireatlas.core.document import MapDocument
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap
from wireatlas.ui.device_details import DeviceDetailsPanel
from wireatlas.ui.device_dialog import DeviceDialog
from wireatlas.ui.topology_view import TopologyView
from wireatlas.core.storage import (
    load_network_map,
    save_network_map,
)
from wireatlas.core.validation import validate_network_map_data

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.document = MapDocument()

        self._build_toolbar()
        self._build_central_widget()
        self.open_action.triggered.connect(
            self._open_document
        )

        self.save_action.triggered.connect(
            self._save
        )

        self.save_as_action.triggered.connect(
            lambda: self._save_as()
        )

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
        self.save_as_action = toolbar.addAction("Save As")
        self.add_device_action = toolbar.addAction("Add Device")
        self.add_connection_action = toolbar.addAction(
            "Add Connection"
    )
        self.export_pdf_action = toolbar.addAction(
            "Export PDF"
    )

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

    @staticmethod
    def _ensure_wireatlas_extension(path: Path) -> Path:
        if path.suffix.lower() == ".wireatlas":
            return path

        return path.with_name(
            f"{path.name}.wireatlas"
        )

    def _suggested_filename(self) -> str:
        site_name = self.network_map.site_name.strip()

        if not site_name:
            site_name = "Untitled Network"

        return f"{site_name}.wireatlas"

    def _save(self) -> bool:
        if self.document.current_path is None:
            return self._save_as()

        try:
            save_network_map(
                self.network_map,
                self.document.current_path,
            )
        except Exception as error:
            self._show_save_error(error)
            return False

        self.document.mark_saved(
            self.document.current_path
        )
        self._update_window_title()
        return True

    def _save_as(self) -> bool:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save WireAtlas Network Map",
            self._suggested_filename(),
            "WireAtlas Network Maps (*.wireatlas)",
        )

        if not filename:
            return False

        path = self._ensure_wireatlas_extension(
            Path(filename)
        )

        try:
            save_network_map(
                self.network_map,
                path,
            )
        except Exception as error:
            self._show_save_error(error)
            return False

        self.document.mark_saved(path)
        self._update_window_title()
        return True

    def _show_save_error(
        self,
        error: Exception,
    ) -> None:
        QMessageBox.critical(
            self,
            "Save Failed",
            "Could not save the network map.\n\n"
            f"{error}",
        )

    def _rebuild_from_document(self) -> None:
        self.topology_view.clear_devices()
        self.details_panel.clear()

        blocker = QSignalBlocker(
            self.site_name_input
        )

        self.site_name_input.setText(
            self.network_map.site_name
        )

        del blocker

        for device in self.network_map.devices:
            self.topology_view.add_device_at_saved_position(
                device
            )

        self._update_window_title()

    def _new_document(self) -> None:
        self.document.new_map()
        self._rebuild_from_document() 

    def _open_document(self) -> bool:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open WireAtlas Network Map",
            "",
            "WireAtlas Network Maps (*.wireatlas)",
        )

        if not filename:
            return False

        path = Path(filename)

        try:
            loaded_map = load_network_map(path)
        except Exception as error:
            self._show_open_error(error)
            return False

        warnings = validate_network_map_data(
            loaded_map
        )

        if warnings and not self._confirm_open_warnings(
            warnings
        ):
            return False

        self.document.replace_map(
            loaded_map,
            path,
        )
        self._rebuild_from_document()

        return True

    def _confirm_open_warnings(
        self,
        warnings: list[str],
    ) -> bool:
        message = QMessageBox(self)

        message.setIcon(
            QMessageBox.Icon.Warning
        )

        message.setWindowTitle(
            "Network Map Warnings"
        )

        message.setText(
            "WireAtlas found issues in this network map."
        )

        message.setInformativeText(
            "The file opened successfully, but some "
            "network data may need attention:\n\n"
            + "\n".join(
                f"• {warning}"
                for warning in warnings
            )
            + "\n\nYou can continue working with the map, "
            "but affected items should be reviewed."
        )

        open_button = message.addButton(
            "Open Anyway",
            QMessageBox.ButtonRole.AcceptRole,
        )

        message.addButton(
            "Cancel",
            QMessageBox.ButtonRole.RejectRole,
        )

        message.exec()

        return message.clickedButton() is open_button

    def _show_open_error(
        self,
        error: Exception,
    ) -> None:
        QMessageBox.critical(
            self,
            "Open Failed",
            "Could not open the network map.\n\n"
            f"{error}",
        )
    
    def _update_window_title(self) -> None:
        marker = " *" if self.document.dirty else ""
        self.setWindowTitle(
            f"WireAtlas — {self.network_map.site_name}{marker}"
        )
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
