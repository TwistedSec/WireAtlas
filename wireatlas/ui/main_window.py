from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from wireatlas.models.network_map import NetworkMap
from wireatlas.ui.device_details import DeviceDetailsPanel
from wireatlas.ui.topology_view import TopologyView


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.network_map = NetworkMap(
            site_name="Untitled Network"
        )

        self.setWindowTitle("WireAtlas")

        self._build_toolbar()
        self._build_central_widget()

        self.statusBar().showMessage("Ready")

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

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        self.topology_view = TopologyView()
        self.details_panel = DeviceDetailsPanel()

        splitter.addWidget(self.topology_view)
        splitter.addWidget(self.details_panel)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        outer_layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

    def _update_site_name(self, value: str) -> None:
        self.network_map.site_name = value