# WireAtlas GUI Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first functional WireAtlas PySide6 vertical slice: launch the application, add a validated device, place it on the topology canvas, and inspect its full details.

**Architecture:** `MainWindow` owns the current `NetworkMap` and coordinates the UI. `DeviceDialog` validates technician input and creates `Device` objects, `TopologyView` renders/selects device nodes and assigns deterministic positions, and `DeviceDetailsPanel` renders selected-device details read-only. Existing core models and validation functions remain the source of truth.

**Tech Stack:** Python 3.14, PySide6 6.11.2, pytest 9.1.1, Qt Widgets / Qt Graphics View Framework.

**Spec:** `docs/specs/2026-09-15-wireatlas-gui-milestone-1-design.md`

## Global Constraints

- Start with `NetworkMap(site_name="Untitled Network")`.
- Use `QMainWindow` with a horizontal `QSplitter`.
- Only **Add Device** is enabled in milestone one; New, Open, Save, Add Connection, and Export PDF remain visible but disabled.
- Device Type starts unselected.
- Name and Device Type are required.
- IP and MAC are optional, but nonblank values must use the existing core validators.
- Every nonblank technician-entered field receives `field_sources[field_name] = "manual"`.
- Blank optional fields receive no provenance entry.
- Canvas nodes display only device name and device type.
- Device details are read-only in milestone one.
- The canvas assigns deterministic positions and stores them in `Device.x` / `Device.y`.
- If no root exists and the added device is `Firewall / Router`, set it as `NetworkMap.root_device_id`.
- Manual data must remain compatible with later discovery and must not be silently overwritten by discovery.
- No save/open wiring, editing, deletion, connections, dragging, zoom, discovery, icons, or PDF export in this milestone.
- Existing core tests must continue to pass.

---

## File Map

### Existing files to modify

- `wireatlas/main.py` — application entry point.
- `wireatlas/ui/main_window.py` — main application window and GUI orchestration.
- `wireatlas/ui/device_dialog.py` — Add Device form, validation, and `Device` creation.
- `wireatlas/ui/topology_view.py` — topology scene, device nodes, deterministic placement, and selection signal.

### New files to create

- `wireatlas/ui/device_details.py` — read-only selected-device details panel.
- `tests/conftest.py` — shared `QApplication` fixture for GUI tests.
- `tests/test_main_window.py` — shell, toolbar, site-name synchronization, root logic, and dialog integration tests.
- `tests/test_device_dialog.py` — Add Device validation and provenance tests.
- `tests/test_topology_view.py` — node text, placement, and selection tests.
- `tests/test_device_details.py` — details-panel rendering and read-only behavior tests.

---

### Task 1: Main Window Shell and Application Entry Point

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_main_window.py`
- Create: `wireatlas/ui/device_details.py`
- Modify: `wireatlas/ui/topology_view.py`
- Modify: `wireatlas/ui/main_window.py`
- Modify: `wireatlas/main.py`

**Interfaces:**
- Produces: `MainWindow.network_map: NetworkMap`
- Produces: `MainWindow.site_name_input: QLineEdit`
- Produces: `MainWindow.topology_view: TopologyView`
- Produces: `MainWindow.details_panel: DeviceDetailsPanel`
- Produces actions: `new_action`, `open_action`, `save_action`, `add_device_action`, `add_connection_action`, `export_pdf_action`
- Produces: `main() -> int`

- [ ] **Step 1: Create the shared Qt application fixture**

Create `tests/conftest.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app
```

- [ ] **Step 2: Write failing shell tests**

Create `tests/test_main_window.py`:

```python
from wireatlas.ui.main_window import MainWindow


def test_main_window_starts_with_untitled_network(qapp):
    window = MainWindow()

    assert window.network_map.site_name == "Untitled Network"
    assert window.site_name_input.text() == "Untitled Network"


def test_main_window_toolbar_enables_only_add_device(qapp):
    window = MainWindow()

    assert window.add_device_action.isEnabled()

    assert not window.new_action.isEnabled()
    assert not window.open_action.isEnabled()
    assert not window.save_action.isEnabled()
    assert not window.add_connection_action.isEnabled()
    assert not window.export_pdf_action.isEnabled()


def test_site_name_edit_updates_network_map(qapp):
    window = MainWindow()

    window.site_name_input.setText("Company X")

    assert window.network_map.site_name == "Company X"
```

- [ ] **Step 3: Run the shell tests and verify RED**

Run:

```powershell
pytest tests\test_main_window.py -v
```

Expected: collection/import or attribute failures because the milestone-one window structure does not exist yet.

- [ ] **Step 4: Implement the empty topology view**

Replace `wireatlas/ui/topology_view.py` with:

```python
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView


class TopologyView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)
```

- [ ] **Step 5: Implement the initial read-only details panel**

Create `wireatlas/ui/device_details.py`:

```python
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DeviceDetailsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.empty_label = QLabel("No device selected")

        layout = QVBoxLayout(self)
        layout.addWidget(self.empty_label)
        layout.addStretch()
```

- [ ] **Step 6: Implement the main-window shell**

Replace `wireatlas/ui/main_window.py` with:

```python
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

        self.network_map = NetworkMap(site_name="Untitled Network")

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
        self.add_connection_action = toolbar.addAction("Add Connection")
        self.export_pdf_action = toolbar.addAction("Export PDF")

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

        self.site_name_input = QLineEdit(self.network_map.site_name)
        self.site_name_input.textChanged.connect(self._update_site_name)
        site_layout.addWidget(self.site_name_input)

        outer_layout.addLayout(site_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

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
```

- [ ] **Step 7: Implement the application entry point**

Replace `wireatlas/main.py` with:

```python
import sys

from PySide6.QtWidgets import QApplication

from wireatlas.ui.main_window import MainWindow


def main() -> int:
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1200, 700)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 8: Run the shell tests and verify GREEN**

Run:

```powershell
pytest tests\test_main_window.py -v
```

Expected: 3 passed.

- [ ] **Step 9: Run the existing suite**

Run:

```powershell
pytest -v
```

Expected: all existing tests plus the new shell tests pass.

- [ ] **Step 10: Commit**

```powershell
git add tests\conftest.py tests\test_main_window.py wireatlas\main.py wireatlas\ui\main_window.py wireatlas\ui\topology_view.py wireatlas\ui\device_details.py
git commit -m "Add WireAtlas GUI shell"
```

---

### Task 2: Add Device Dialog Validation and Provenance

**Files:**
- Create: `tests/test_device_dialog.py`
- Modify: `wireatlas/ui/device_dialog.py`

**Interfaces:**
- Consumes: `is_valid_ip(value: str) -> bool`
- Consumes: `is_valid_mac(value: str) -> bool`
- Consumes: `DeviceType`
- Produces: `DeviceDialog.build_device() -> Device`
- Produces widgets used by tests and later integration:
  - `name_input`
  - `type_combo`
  - `ip_input`
  - `mac_input`
  - `vlan_input`
  - `subnet_input`
  - `notes_input`
  - `ip_error`
  - `mac_error`
  - `add_button`

- [ ] **Step 1: Write failing dialog tests**

Create `tests/test_device_dialog.py`:

```python
from wireatlas.models.device import DeviceType
from wireatlas.ui.device_dialog import DeviceDialog


def test_device_dialog_starts_without_selected_type(qapp):
    dialog = DeviceDialog()

    assert dialog.type_combo.currentData() is None
    assert not dialog.add_button.isEnabled()


def test_device_dialog_requires_name_and_type(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")

    assert not dialog.add_button.isEnabled()

    dialog.type_combo.setCurrentIndex(1)

    assert dialog.add_button.isEnabled()


def test_device_dialog_rejects_invalid_nonblank_ip(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")
    dialog.type_combo.setCurrentIndex(1)
    dialog.ip_input.setText("192.168.1.999")

    assert not dialog.add_button.isEnabled()
    assert dialog.ip_error.text() == "Enter a valid IP address."


def test_device_dialog_rejects_invalid_nonblank_mac(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Office Printer")
    dialog.type_combo.setCurrentIndex(1)
    dialog.mac_input.setText("ZZ:12:34:56:78:90")

    assert not dialog.add_button.isEnabled()
    assert dialog.mac_error.text() == "Enter a valid MAC address."


def test_device_dialog_builds_device_with_manual_provenance(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")
    dialog.type_combo.setCurrentIndex(
        dialog.type_combo.findData(DeviceType.FIREWALL_ROUTER)
    )
    dialog.ip_input.setText("192.168.1.1")
    dialog.notes_input.setPlainText("Primary gateway")

    device = dialog.build_device()

    assert device.name == "Main Router"
    assert device.device_type == DeviceType.FIREWALL_ROUTER
    assert device.ip_address == "192.168.1.1"
    assert device.notes == "Primary gateway"

    assert device.field_sources == {
        "name": "manual",
        "device_type": "manual",
        "ip_address": "manual",
        "notes": "manual",
    }
```

- [ ] **Step 2: Run dialog tests and verify RED**

Run:

```powershell
pytest tests\test_device_dialog.py -v
```

Expected: failures because `DeviceDialog` does not yet expose this behavior.

- [ ] **Step 3: Implement the Add Device dialog**

Replace `wireatlas/ui/device_dialog.py` with:

```python
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
            self.type_combo.addItem(device_type.value, device_type)

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

        self.name_input.textChanged.connect(self._update_validation)
        self.type_combo.currentIndexChanged.connect(self._update_validation)
        self.ip_input.textChanged.connect(self._update_validation)
        self.mac_input.textChanged.connect(self._update_validation)

        self.cancel_button.clicked.connect(self.reject)
        self.add_button.clicked.connect(self.accept)

        self._update_validation()

    def _update_validation(self) -> None:
        name_valid = bool(self.name_input.text().strip())
        type_valid = self.type_combo.currentData() is not None

        ip_value = self.ip_input.text().strip()
        mac_value = self.mac_input.text().strip()

        ip_valid = is_valid_ip(ip_value)
        mac_valid = is_valid_mac(mac_value)

        self.ip_error.setText(
            "" if ip_valid else "Enter a valid IP address."
        )
        self.mac_error.setText(
            "" if mac_valid else "Enter a valid MAC address."
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
```

- [ ] **Step 4: Run dialog tests and verify GREEN**

Run:

```powershell
pytest tests\test_device_dialog.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run the full suite**

Run:

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add wireatlas\ui\device_dialog.py tests\test_device_dialog.py
git commit -m "Add validated device dialog"
```

---

### Task 3: Topology Nodes, Deterministic Placement, and Selection

**Files:**
- Create: `tests/test_topology_view.py`
- Modify: `wireatlas/ui/topology_view.py`

**Interfaces:**
- Consumes: `Device`
- Produces: `DeviceNode`
- Produces: `TopologyView.add_device(device: Device) -> DeviceNode`
- Produces: `TopologyView.node_for_device(device_id: str) -> DeviceNode | None`
- Produces signal: `TopologyView.device_selected(str)`
- Produces deterministic `Device.x` / `Device.y`

- [ ] **Step 1: Write failing topology-view tests**

Create `tests/test_topology_view.py`:

```python
from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.topology_view import TopologyView


def test_topology_node_shows_only_name_and_type(qapp):
    view = TopologyView()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    node = view.add_device(device)

    assert node.display_text() == "Main Router\nFirewall / Router"
    assert "192.168.1.1" not in node.display_text()
    assert "AA:BB:CC:DD:EE:FF" not in node.display_text()


def test_topology_view_assigns_deterministic_positions(qapp):
    view = TopologyView()

    first = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    second = Device(
        name="Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(first)
    view.add_device(second)

    assert (first.x, first.y) == (40.0, 40.0)
    assert (second.x, second.y) == (230.0, 40.0)


def test_topology_view_emits_selected_device_id(qapp):
    view = TopologyView()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    node = view.add_device(device)

    selected_ids = []
    view.device_selected.connect(selected_ids.append)

    node.setSelected(True)
    qapp.processEvents()

    assert selected_ids == [device.id]
```

- [ ] **Step 2: Run topology-view tests and verify RED**

Run:

```powershell
pytest tests\test_topology_view.py -v
```

Expected: failures because nodes, placement, and selection signals are not implemented.

- [ ] **Step 3: Implement device nodes and placement**

Replace `wireatlas/ui/topology_view.py` with:

```python
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from wireatlas.models.device import Device


NODE_WIDTH = 160.0
NODE_HEIGHT = 70.0
START_X = 40.0
START_Y = 40.0
X_SPACING = 190.0
Y_SPACING = 110.0
COLUMNS = 4


class DeviceNode(QGraphicsRectItem):
    def __init__(self, device: Device):
        super().__init__(0.0, 0.0, NODE_WIDTH, NODE_HEIGHT)

        self.device_id = device.id

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.label = QGraphicsTextItem(
            f"{device.name}\n{device.device_type.value}",
            self,
        )
        self.label.setPos(8.0, 8.0)

    def display_text(self) -> str:
        return self.label.toPlainText()


class TopologyView(QGraphicsView):
    device_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)

        self._nodes: dict[str, DeviceNode] = {}

        self.graphics_scene.selectionChanged.connect(
            self._emit_selected_device
        )

    @staticmethod
    def position_for_index(index: int) -> tuple[float, float]:
        column = index % COLUMNS
        row = index // COLUMNS

        x = START_X + column * X_SPACING
        y = START_Y + row * Y_SPACING

        return x, y

    def add_device(self, device: Device) -> DeviceNode:
        x, y = self.position_for_index(len(self._nodes))

        device.x = x
        device.y = y

        node = DeviceNode(device)
        node.setPos(x, y)

        self.graphics_scene.addItem(node)
        self._nodes[device.id] = node

        return node

    def node_for_device(self, device_id: str) -> DeviceNode | None:
        return self._nodes.get(device_id)

    def _emit_selected_device(self) -> None:
        for item in self.graphics_scene.selectedItems():
            if isinstance(item, DeviceNode):
                self.device_selected.emit(item.device_id)
                return
```

- [ ] **Step 4: Run topology-view tests and verify GREEN**

Run:

```powershell
pytest tests\test_topology_view.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run:

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add wireatlas\ui\topology_view.py tests\test_topology_view.py
git commit -m "Add topology device nodes"
```

---

### Task 4: Read-Only Device Details Panel

**Files:**
- Create: `tests/test_device_details.py`
- Modify: `wireatlas/ui/device_details.py`

**Interfaces:**
- Consumes: `Device`
- Produces: `DeviceDetailsPanel.clear() -> None`
- Produces: `DeviceDetailsPanel.show_device(device: Device, is_root: bool = False) -> None`

- [ ] **Step 1: Write failing details-panel tests**

Create `tests/test_device_details.py`:

```python
from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.device_details import DeviceDetailsPanel


def test_details_panel_starts_empty(qapp):
    panel = DeviceDetailsPanel()

    assert panel.empty_label.text() == "No device selected"
    assert panel.empty_label.isVisible()


def test_details_panel_shows_device_values(qapp):
    panel = DeviceDetailsPanel()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
        vlan_id="10",
        subnet="192.168.1.0/24",
        notes="Primary gateway",
    )

    panel.show()
    panel.show_device(device, is_root=True)
    qapp.processEvents()

    assert panel.name_value.text() == "Main Router"
    assert panel.type_value.text() == "Firewall / Router"
    assert panel.ip_value.text() == "192.168.1.1"
    assert panel.mac_value.text() == "AA:BB:CC:DD:EE:FF"
    assert panel.vlan_value.text() == "10"
    assert panel.subnet_value.text() == "192.168.1.0/24"
    assert panel.notes_value.toPlainText() == "Primary gateway"
    assert panel.root_value.text() == "Yes"
    assert panel.notes_value.isReadOnly()


def test_details_panel_uses_placeholder_for_blank_values(qapp):
    panel = DeviceDetailsPanel()

    device = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )

    panel.show_device(device)

    assert panel.ip_value.text() == "—"
    assert panel.mac_value.text() == "—"
    assert panel.vlan_value.text() == "—"
    assert panel.subnet_value.text() == "—"
    assert panel.notes_value.toPlainText() == "—"
    assert panel.root_value.text() == "No"
```

- [ ] **Step 2: Run details-panel tests and verify RED**

Run:

```powershell
pytest tests\test_device_details.py -v
```

Expected: failures because the detailed read-only fields do not exist yet.

- [ ] **Step 3: Implement the read-only details panel**

Replace `wireatlas/ui/device_details.py` with:

```python
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
        self.type_value = QLabel("—")
        self.ip_value = QLabel("—")
        self.mac_value = QLabel("—")
        self.vlan_value = QLabel("—")
        self.subnet_value = QLabel("—")
        self.root_value = QLabel("No")

        self.notes_value = QPlainTextEdit()
        self.notes_value.setReadOnly(True)
        self.notes_value.setMaximumHeight(120)

        form_layout.addRow("Name:", self.name_value)
        form_layout.addRow("Device Type:", self.type_value)
        form_layout.addRow("IP Address:", self.ip_value)
        form_layout.addRow("MAC Address:", self.mac_value)
        form_layout.addRow("VLAN:", self.vlan_value)
        form_layout.addRow("Subnet:", self.subnet_value)
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
        self.type_value.setText(device.device_type.value)
        self.ip_value.setText(_display(device.ip_address))
        self.mac_value.setText(_display(device.mac_address))
        self.vlan_value.setText(_display(device.vlan_id))
        self.subnet_value.setText(_display(device.subnet))
        self.notes_value.setPlainText(_display(device.notes))
        self.root_value.setText("Yes" if is_root else "No")

        self.empty_label.hide()
        self.form_widget.show()
```

- [ ] **Step 4: Run details-panel tests and verify GREEN**

Run:

```powershell
pytest tests\test_device_details.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Run the full suite**

Run:

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add wireatlas\ui\device_details.py tests\test_device_details.py
git commit -m "Add device details panel"
```

---

### Task 5: Integrate Add Device, Root Assignment, Canvas, and Details

**Files:**
- Modify: `tests/test_main_window.py`
- Modify: `wireatlas/ui/main_window.py`

**Interfaces:**
- Consumes: `DeviceDialog.build_device() -> Device`
- Consumes: `TopologyView.add_device(device: Device) -> DeviceNode`
- Consumes signal: `TopologyView.device_selected(str)`
- Consumes: `DeviceDetailsPanel.show_device(device: Device, is_root: bool = False) -> None`
- Produces: `MainWindow.add_device(device: Device) -> None`

- [ ] **Step 1: Append failing integration tests**

Append to `tests/test_main_window.py`:

```python
from PySide6.QtWidgets import QDialog

from wireatlas.models.device import Device, DeviceType
import wireatlas.ui.main_window as main_window_module


def test_add_device_adds_model_node_and_root(qapp):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(router)

    assert window.network_map.devices == [router]
    assert window.network_map.root_device_id == router.id
    assert window.topology_view.node_for_device(router.id) is not None
    assert (router.x, router.y) == (40.0, 40.0)


def test_non_router_does_not_become_root(qapp):
    window = MainWindow()

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(switch)

    assert window.network_map.root_device_id == ""


def test_selecting_node_populates_details_panel(qapp):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
    )

    window.add_device(router)

    node = window.topology_view.node_for_device(router.id)
    node.setSelected(True)
    qapp.processEvents()

    assert window.details_panel.name_value.text() == "Main Router"
    assert window.details_panel.ip_value.text() == "192.168.1.1"
    assert window.details_panel.root_value.text() == "Yes"


def test_add_device_action_uses_device_dialog(qapp, monkeypatch):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    class FakeDeviceDialog:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def build_device(self):
            return router

    monkeypatch.setattr(
        main_window_module,
        "DeviceDialog",
        FakeDeviceDialog,
    )

    window.add_device_action.trigger()

    assert window.network_map.devices == [router]
```

- [ ] **Step 2: Run integration tests and verify RED**

Run:

```powershell
pytest tests\test_main_window.py -v
```

Expected: the original shell tests pass; the new integration tests fail because `add_device`, selection integration, and dialog wiring are not implemented.

- [ ] **Step 3: Integrate the dialog and topology workflow**

Update `wireatlas/ui/main_window.py`.

Add these imports:

```python
from PySide6.QtWidgets import QDialog

from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.device_dialog import DeviceDialog
```

In `MainWindow.__init__`, after building the UI, add:

```python
self.add_device_action.triggered.connect(
    self._open_add_device_dialog
)
self.topology_view.device_selected.connect(
    self._show_device_details
)
```

Add these methods to `MainWindow`:

```python
def add_device(self, device: Device) -> None:
    if (
        not self.network_map.root_device_id
        and device.device_type == DeviceType.FIREWALL_ROUTER
    ):
        self.network_map.root_device_id = device.id

    self.network_map.devices.append(device)
    self.topology_view.add_device(device)

def _open_add_device_dialog(self) -> None:
    dialog = DeviceDialog(self)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        self.add_device(dialog.build_device())

def _show_device_details(self, device_id: str) -> None:
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
            device.id == self.network_map.root_device_id
        ),
    )
```

- [ ] **Step 4: Run integration tests and verify GREEN**

Run:

```powershell
pytest tests\test_main_window.py -v
```

Expected: all main-window tests pass.

- [ ] **Step 5: Run all GUI tests together**

Run:

```powershell
pytest tests\test_main_window.py tests\test_device_dialog.py tests\test_topology_view.py tests\test_device_details.py -v
```

Expected: all GUI tests pass.

- [ ] **Step 6: Run the complete project suite**

Run:

```powershell
pytest -v
```

Expected: all core and GUI tests pass with zero failures.

- [ ] **Step 7: Manually launch WireAtlas**

Run:

```powershell
python -m wireatlas.main
```

Verify manually:

1. Window title is `WireAtlas`.
2. Site field shows `Untitled Network`.
3. Only Add Device is enabled.
4. Add Device opens the dialog.
5. Device Type starts unselected.
6. Invalid IP/MAC values block Add and show inline messages.
7. Enter:
   - Name: `Main Router`
   - Device Type: `Firewall / Router`
   - IP: `192.168.1.1`
   - Notes: `Primary gateway`
8. Click Add.
9. A node appears with only:
   - `Main Router`
   - `Firewall / Router`
10. Click the node.
11. The right panel shows the full device details and `Root Device: Yes`.
12. Change the site name and confirm the field remains responsive.

Close the window normally.

- [ ] **Step 8: Commit**

```powershell
git add wireatlas\ui\main_window.py tests\test_main_window.py
git commit -m "Integrate Add Device GUI workflow"
```

---

## Final Verification

After all tasks are committed, run:

```powershell
pytest -v
git status
```

Required result:

- Pytest exits successfully with zero failures.
- `git status` shows no unexpected modified or untracked implementation files.

Then run the GUI one final time:

```powershell
python -m wireatlas.main
```

Confirm the milestone success criteria from the spec:

- WireAtlas launches.
- `Untitled Network` is editable.
- Add Device is functional.
- Valid device data creates a real `Device`.
- The first Firewall / Router becomes root when appropriate.
- The topology canvas shows only name and type.
- Selecting the node shows full read-only details.
- Future toolbar actions remain disabled.
