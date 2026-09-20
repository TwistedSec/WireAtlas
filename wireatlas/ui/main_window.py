from pathlib import Path
from PySide6.QtCore import QSignalBlocker, QRectF, Qt
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

from PySide6.QtGui import (
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
)

from wireatlas.models.connection import Connection
from wireatlas.core.document import MapDocument
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap
from wireatlas.ui.device_details import DeviceDetailsPanel
from wireatlas.ui.device_dialog import DeviceDialog
from wireatlas.ui.topology_view import TopologyView
from wireatlas.ui.connection_dialog import ConnectionDialog
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

        self.new_action.triggered.connect(
            lambda: self._request_new_document()
        )

        self.open_action.triggered.connect(
            lambda: self._request_open_document()
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

        self.add_connection_action.triggered.connect(
            lambda: self._open_add_connection_dialog()
        )

        self.export_pdf_action.triggered.connect(
            lambda: self._export_pdf()
        )

        self.delete_connection_action.triggered.connect(
        self._delete_selected_connection
)

        self.topology_view.connection_selected.connect(
            self._select_connection
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

        self.delete_connection_action = toolbar.addAction(
            "Delete Connection"
        )

        self.export_pdf_action = toolbar.addAction(
            "Export PDF"
        )

        self.add_connection_action.setEnabled(False)
        self.delete_connection_action.setEnabled(False)
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

    @staticmethod
    def _ensure_pdf_extension(path: Path) -> Path:
        if path.suffix.lower() == ".pdf":
            return path

        return path.with_name(
            f"{path.name}.pdf"
        )

    def _suggested_filename(self) -> str:
        site_name = self.network_map.site_name.strip()

        if not site_name:
            site_name = "Untitled Network"

        return f"{site_name}.wireatlas"

    def _suggested_pdf_filename(self) -> str:
        site_name = self.network_map.site_name.strip()

        if not site_name:
            site_name = "Untitled Network"

        return f"{site_name} Network Map.pdf"

    @staticmethod
    def _topology_fit_scale(
        source_width: float,
        source_height: float,
        target_width: float,
        target_height: float,
    ) -> float:
        return min(
            target_width / source_width,
            target_height / source_height,
        )

    def _topology_fits_single_page(
        self,
        source_width: float,
        source_height: float,
        target_width: float,
        target_height: float,
    ) -> bool:
        scale = self._topology_fit_scale(
            source_width,
            source_height,
            target_width,
            target_height,
        )

        return scale >= 0.75

    def _topology_render_rect(
        self,
        source_rect: QRectF,
        target_rect: QRectF,
    ) -> QRectF:
        scale = min(
            1.0,
            self._topology_fit_scale(
                source_width=source_rect.width(),
                source_height=source_rect.height(),
                target_width=target_rect.width(),
                target_height=target_rect.height(),
            ),
        )

        render_rect = QRectF(
            0.0,
            0.0,
            source_rect.width() * scale,
            source_rect.height() * scale,
        )

        render_rect.moveCenter(
            target_rect.center()
        )

        return render_rect

    @staticmethod
    def _connection_belongs_on_topology_page(
        source_device_id: str,
        destination_device_id: str,
        page_device_ids: set[str],
    ) -> bool:
        return (
            source_device_id in page_device_ids
            and destination_device_id in page_device_ids
        )

    def _plan_topology_pages(
        self,
        target_width: float,
        target_height: float,
    ) -> list[list[str]]:
        if not self.network_map.devices:
            return []

        source_rect = (
            self.topology_view.graphics_scene.itemsBoundingRect()
        )

        if source_rect.isEmpty():
            return []

        if self._topology_fits_single_page(
            source_width=source_rect.width(),
            source_height=source_rect.height(),
            target_width=target_width,
            target_height=target_height,
        ):
            return [
                [
                    device.id
                    for device in self.network_map.devices
                ]
            ]

        adjacency = {
            device.id: []
            for device in self.network_map.devices
        }

        for connection in self.network_map.connections:
            adjacency[connection.source_device_id].append(
                connection.destination_device_id
            )
            adjacency[connection.destination_device_id].append(
                connection.source_device_id
            )

        root_id = self.network_map.root_device_id

        if root_id not in adjacency:
            root_id = self.network_map.devices[0].id

        ordered_ids = []
        parent_by_id = {}
        visited = set()
        stack = [(root_id, None)]

        while stack:
            device_id, parent_id = stack.pop()

            if device_id in visited:
                continue

            visited.add(device_id)
            ordered_ids.append(device_id)
            parent_by_id[device_id] = parent_id

            neighbors = adjacency.get(device_id, [])

            for neighbor_id in reversed(neighbors):
                if neighbor_id not in visited:
                    stack.append(
                        (neighbor_id, device_id)
                    )

        for device in self.network_map.devices:
            if device.id not in visited:
                ordered_ids.append(device.id)
                parent_by_id[device.id] = None

        def page_fits(device_ids: list[str]) -> bool:
            page_rect = None

            for device_id in device_ids:
                node = self.topology_view.node_for_device(
                    device_id
                )

                if node is None:
                    continue

                node_rect = node.sceneBoundingRect()

                if page_rect is None:
                    page_rect = node_rect
                else:
                    page_rect = page_rect.united(
                        node_rect
                    )

            if page_rect is None:
                return True

            return self._topology_fits_single_page(
                source_width=page_rect.width(),
                source_height=page_rect.height(),
                target_width=target_width,
                target_height=target_height,
            )

        pages = []
        current_page = []

        for device_id in ordered_ids:
            candidate = current_page + [device_id]

            if not current_page or page_fits(candidate):
                current_page = candidate
                continue

            pages.append(current_page)

            parent_id = parent_by_id.get(device_id)

            current_page = []

            if parent_id is not None:
                current_page.append(parent_id)

            if device_id not in current_page:
                current_page.append(device_id)

        if current_page:
            pages.append(current_page)

        return pages

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

    def _export_pdf(self) -> bool:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Network Map as PDF",
            self._suggested_pdf_filename(),
            "PDF Files (*.pdf)",
        )

        if not filename:
            return False

        path = self._ensure_pdf_extension(
            Path(filename)
        )

        try:
            self._write_pdf(path)
        except Exception as error:
            self._show_export_error(error)
            return False

        return True

    def _draw_device_reference(
        self,
        writer: QPdfWriter,
        painter: QPainter,
    ) -> None:
        writer.newPage()

        title_font = painter.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        painter.setFont(title_font)

        painter.drawText(
            36,
            42,
            "Device Reference",
        )

        headers = [
            "Device Name",
            "Hostname",
            "Device Type",
            "IP Address",
            "Subnet Mask",
            "Subnet / Network",
            "VLAN",
            "MAC Address",
            "Vendor",
        ]

        widths = [
            90.0,
            90.0,
            85.0,
            75.0,
            80.0,
            95.0,
            35.0,
            95.0,
            75.0,
        ]

        x_start = 36.0
        y = 70.0
        row_height = 28.0
        page_bottom = 576.0

        table_font = painter.font()
        table_font.setPointSize(7)
        table_font.setBold(True)
        painter.setFont(table_font)

        x = x_start

        for header, width in zip(headers, widths):
            cell = QRectF(
                x,
                y,
                width,
                row_height,
            )

            painter.drawRect(cell)
            painter.drawText(
                cell.adjusted(3.0, 0.0, -3.0, 0.0),
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
                header,
            )

            x += width

        y += row_height

        table_font.setBold(False)
        painter.setFont(table_font)

        for device in self.network_map.devices:
            if y + row_height > page_bottom:
                writer.newPage()

                title_font.setBold(True)
                painter.setFont(title_font)

                painter.drawText(
                    36,
                    42,
                    "Device Reference",
                )

                y = 70.0

                table_font.setBold(True)
                painter.setFont(table_font)

                x = x_start

                for header, width in zip(headers, widths):
                    cell = QRectF(
                        x,
                        y,
                        width,
                        row_height,
                    )

                    painter.drawRect(cell)
                    painter.drawText(
                        cell.adjusted(
                            3.0,
                            0.0,
                            -3.0,
                            0.0,
                        ),
                        Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter,
                        header,
                    )

                    x += width

                y += row_height

                table_font.setBold(False)
                painter.setFont(table_font)

            values = [
                device.name,
                device.hostname,
                device.device_type.value,
                device.ip_address,
                device.subnet_mask,
                device.subnet,
                device.vlan_id,
                device.mac_address,
                device.vendor,
            ]

            x = x_start

            for value, width in zip(values, widths):
                cell = QRectF(
                    x,
                    y,
                    width,
                    row_height,
                )

                painter.drawRect(cell)
                painter.drawText(
                    cell.adjusted(
                        3.0,
                        0.0,
                        -3.0,
                        0.0,
                    ),
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignVCenter,
                    value or "—",
                )

                x += width

            y += row_height

    def _write_pdf(self, path: Path) -> None:
        writer = QPdfWriter(str(path))

        writer.setResolution(72)

        writer.setPageSize(
            QPageSize(QPageSize.PageSizeId.Letter)
        )
        writer.setPageOrientation(
            QPageLayout.Orientation.Landscape
        )

        painter = QPainter()

        if not painter.begin(writer):
            raise OSError(
                "Could not create PDF file."
            )

        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)

        site_name = self.network_map.site_name.strip()

        if not site_name:
            site_name = "Untitled Network"

        painter.drawText(
            36,
            42,
            site_name,
        )

        topology_rect = QRectF(
            36.0,
            72.0,
            720.0,
            504.0,
        )

        pages = self._plan_topology_pages(
            target_width=topology_rect.width(),
            target_height=topology_rect.height(),
        )

        for page_index, device_ids in enumerate(pages):
            if page_index > 0:
                writer.newPage()

                painter.drawText(
                    36,
                    42,
                    site_name,
                )

            source_rect = None

            for device_id in device_ids:
                node = self.topology_view.node_for_device(
                    device_id
                )

                if node is None:
                    continue

                node_rect = node.sceneBoundingRect()

                if source_rect is None:
                    source_rect = node_rect
                else:
                    source_rect = source_rect.united(
                        node_rect
                    )

            if source_rect is None:
                continue

            source_rect = source_rect.adjusted(
                -12.0,
                -12.0,
                12.0,
                12.0,
            )

            render_rect = self._topology_render_rect(
                source_rect,
                topology_rect,
            )

            scene = self.topology_view.graphics_scene
            selected_items = scene.selectedItems()
            page_device_ids = set(device_ids)

            edge_visibility = []

            for edge in self.topology_view._edges.values():
                edge_visibility.append(
                    (
                        edge,
                        edge.isVisible(),
                        edge.label.isVisible(),
                    )
                )

                belongs_on_page = (
                    self._connection_belongs_on_topology_page(
                        edge.source_node.device_id,
                        edge.destination_node.device_id,
                        page_device_ids,
                    )
                )

                edge.setVisible(belongs_on_page)
                edge.label.setVisible(belongs_on_page)

            scene.clearSelection()

            try:
                scene.render(
                    painter,
                    render_rect,
                    source_rect,
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            finally:
                for edge, edge_visible, label_visible in edge_visibility:
                    edge.setVisible(edge_visible)
                    edge.label.setVisible(label_visible)

                for item in selected_items:
                    item.setSelected(True)

        self._draw_device_reference(
            writer,
            painter,
        )

        painter.end()

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

    def _show_export_error(
        self,
        error: Exception,
    ) -> None:
        QMessageBox.critical(
            self,
            "Export Failed",
            "Could not export the network map as PDF.\n\n"
            f"{error}",
        )

    def _rebuild_from_document(self) -> None:
        self.selected_connection_id = None
        self.delete_connection_action.setEnabled(False)

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

        for connection in self.network_map.connections:
            self.topology_view.add_connection(
                connection
            )

        self.add_connection_action.setEnabled(
            len(self.network_map.devices) >= 2
        )

        self.export_pdf_action.setEnabled(
            len(self.network_map.devices) > 0
        )

        self._update_window_title()

    def _ask_unsaved_changes(
        self,
    ) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "Unsaved Changes",
            f"Save changes to "
            f"{self.network_map.site_name}?\n\n"
            "Your changes will be lost if "
            "you don’t save them.",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

    def _confirm_discard_or_save(self) -> bool:
        if not self.document.dirty:
            return True

        choice = self._ask_unsaved_changes()

        if choice == QMessageBox.StandardButton.Cancel:
            return False

        if choice == QMessageBox.StandardButton.Discard:
            return True

        if choice == QMessageBox.StandardButton.Save:
            return self._save()

        return False

    def _new_document(self) -> None:
        self.document.new_map()
        self._rebuild_from_document()

    def _request_new_document(self) -> None:
        if not self._confirm_discard_or_save():
            return

        self._new_document()

    def _request_open_document(self) -> bool:
        if not self._confirm_discard_or_save():
            return False

        return self._open_document_from_dialog()

    def closeEvent(self, event) -> None:
        if self._confirm_discard_or_save():
            event.accept()
        else:
            event.ignore()

    def _open_document_from_dialog(self) -> bool:
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

        self.add_connection_action.setEnabled(
            len(self.network_map.devices) >= 2
        )

        self.export_pdf_action.setEnabled(
            len(self.network_map.devices) > 0
        )

    def add_connection(self, connection: Connection) -> None:
        duplicate = any(
        (
            (
                existing.source_device_id
                == connection.source_device_id
                and existing.destination_device_id
                == connection.destination_device_id
                and existing.source_interface
                == connection.source_interface
                and existing.destination_interface
                == connection.destination_interface
            )
            or
            (
                existing.source_device_id
                == connection.destination_device_id
                and existing.destination_device_id
                == connection.source_device_id
                and existing.source_interface
                == connection.destination_interface
                and existing.destination_interface
                == connection.source_interface
            )
        )
        and existing.link_type
        == connection.link_type
        for existing in self.network_map.connections
    )

        if duplicate:
            return

        self.network_map.connections.append(connection)

        self.topology_view.add_connection(
        connection
        )

        self._mark_dirty()

    def _select_connection(
        self,
        connection_id: str,
    ) -> None:
        if not connection_id:
            self.selected_connection_id = None
            self.delete_connection_action.setEnabled(False)
            return

        self.selected_connection_id = connection_id
        self.delete_connection_action.setEnabled(True)

    def _delete_selected_connection(self) -> None:
        connection_id = getattr(
            self,
            "selected_connection_id",
            None,
        )

        if connection_id is None:
            return

        self.network_map.connections = [
            connection
            for connection in self.network_map.connections
            if connection.id != connection_id
        ]

        self.topology_view.remove_connection(
            connection_id
        )

        self.selected_connection_id = None
        self.delete_connection_action.setEnabled(False)

        self._mark_dirty()

    def _open_add_device_dialog(self) -> None:
        dialog = DeviceDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_device(dialog.build_device())

    def _open_add_connection_dialog(self) -> None:
        dialog = ConnectionDialog(
            self.network_map.devices,
            self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_connection(
                dialog.build_connection()
        )

    def _show_device_details(
        self,
        device_id: str,
    ) -> None:
        self.selected_connection_id = None
        self.delete_connection_action.setEnabled(False)

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
