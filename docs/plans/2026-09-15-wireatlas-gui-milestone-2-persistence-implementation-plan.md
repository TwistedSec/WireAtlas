# WireAtlas GUI Milestone 2 Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent `.wireatlas` document workflows so a technician can create, save, reopen, and safely continue a WireAtlas network map without losing work.

**Architecture:** Introduce a focused `MapDocument` state object that owns the current `NetworkMap`, current file path, and dirty flag. Keep file dialogs, prompts, warning/error dialogs, and GUI rebuilding in `MainWindow`, while continuing to delegate serialization to `wireatlas.core.storage` and data warnings to `wireatlas.core.validation`.

**Tech Stack:** Python 3.14.7, PySide6 6.11.2, pytest 9.1.1, standard-library `pathlib`.

**Spec:** `docs/specs/2026-09-15-wireatlas-gui-milestone-2-persistence-design.md`

## Global Constraints

- `.wireatlas` remains the only WireAtlas map-file extension in this milestone.
- Existing `save_network_map()` and `load_network_map()` remain the serialization boundary.
- Structural file errors reject Open and leave the current document untouched.
- Data warnings use **Open Anyway / Cancel** only; there is no read-only mode.
- Failed or canceled file operations must not destroy or replace current work.
- A successful Save, Save As, Open, or New leaves the document clean.
- Adding a device or changing the site name marks the document dirty.
- Loaded devices must retain their saved `x` and `y` coordinates.
- New, Open, and application Close must protect dirty work with Save / Discard / Cancel.
- Save with no current path behaves as Save As.
- Save As automatically appends `.wireatlas` if omitted.
- Save As should suggest a filename derived from the current site name.
- Existing Add Device behavior must continue to work.
- Add Connection and Export PDF remain disabled.
- No autosave, recent files, read-only mode, file locking, cloud/database storage, edit/delete, drag-and-drop, connections, PDF export, or discovery in this milestone.
- Follow TDD for every behavior change: RED first, then minimal GREEN implementation, then regression run.
- Do not implement directly on `master`; work on `gui-milestone-2-persistence`.

---

## File Map

### Create

- `wireatlas/core/document.py`
  - Owns current `NetworkMap`
  - Owns `current_path`
  - Owns `dirty`
  - Provides small state-transition methods only; no dialogs and no JSON I/O

- `tests/test_document.py`
  - Unit tests for `MapDocument`

### Modify

- `wireatlas/ui/topology_view.py`
  - Add scene reset support
  - Add a way to restore a device node at saved coordinates without overwriting them

- `tests/test_topology_view.py`
  - Cover clear and restore-position behavior

- `wireatlas/ui/main_window.py`
  - Replace direct top-level map ownership with `MapDocument`
  - Enable New/Open/Save and expose Save As
  - Dirty-state/title updates
  - Save and Save As workflows
  - Open workflow and map rebuild
  - New workflow
  - Save / Discard / Cancel protection
  - Close-event protection
  - Warning and error dialogs

- `tests/test_main_window.py`
  - Add GUI workflow coverage using monkeypatches instead of real interactive dialogs/files wherever practical

No changes are expected in:

- `wireatlas/models/device.py`
- `wireatlas/models/connection.py`
- `wireatlas/models/network_map.py`
- `wireatlas/core/storage.py`
- `wireatlas/core/validation.py`
- `wireatlas/core/topology.py`

unless a test exposes a genuine defect in those existing boundaries.

---

### Task 1: Add `MapDocument` State Model

**Files:**
- Create: `wireatlas/core/document.py`
- Create: `tests/test_document.py`

**Interfaces:**
- Produces:
  - `class MapDocument`
  - `MapDocument.network_map: NetworkMap`
  - `MapDocument.current_path: Path | None`
  - `MapDocument.dirty: bool`
  - `MapDocument.mark_dirty() -> None`
  - `MapDocument.mark_saved(path: Path) -> None`
  - `MapDocument.replace_map(network_map: NetworkMap, path: Path | None = None) -> None`
  - `MapDocument.new_map() -> None`

- [ ] **Step 1: Write failing tests for default state**

Create `tests/test_document.py`:

```python
from pathlib import Path

from wireatlas.core.document import MapDocument
from wireatlas.models.network_map import NetworkMap


def test_document_starts_with_untitled_clean_map():
    document = MapDocument()

    assert document.network_map.site_name == "Untitled Network"
    assert document.current_path is None
    assert document.dirty is False


def test_mark_dirty_sets_dirty_state():
    document = MapDocument()

    document.mark_dirty()

    assert document.dirty is True
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
pytest tests/test_document.py -v
```

Expected: collection/import failure because `wireatlas.core.document` does not yet exist.

- [ ] **Step 3: Implement the minimal document object**

Create `wireatlas/core/document.py`:

```python
from pathlib import Path

from wireatlas.models.network_map import NetworkMap


class MapDocument:
    def __init__(self) -> None:
        self.network_map = NetworkMap(
            site_name="Untitled Network"
        )
        self.current_path: Path | None = None
        self.dirty = False

    def mark_dirty(self) -> None:
        self.dirty = True
```

- [ ] **Step 4: Run document tests and verify GREEN**

Run:

```powershell
pytest tests/test_document.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Add failing tests for saved/replaced/new transitions**

Append to `tests/test_document.py`:

```python
def test_mark_saved_records_path_and_clears_dirty(tmp_path):
    document = MapDocument()
    document.mark_dirty()

    path = tmp_path / "office.wireatlas"
    document.mark_saved(path)

    assert document.current_path == path
    assert document.dirty is False


def test_replace_map_replaces_map_path_and_clears_dirty(tmp_path):
    document = MapDocument()
    document.mark_dirty()

    network_map = NetworkMap(site_name="Loaded Site")
    path = tmp_path / "loaded.wireatlas"

    document.replace_map(network_map, path)

    assert document.network_map is network_map
    assert document.current_path == path
    assert document.dirty is False


def test_new_map_resets_to_clean_untitled_document(tmp_path):
    document = MapDocument()
    document.network_map.site_name = "Old Site"
    document.current_path = tmp_path / "old.wireatlas"
    document.mark_dirty()

    document.new_map()

    assert document.network_map.site_name == "Untitled Network"
    assert document.current_path is None
    assert document.dirty is False
```

- [ ] **Step 6: Run the new transition tests and verify RED**

Run:

```powershell
pytest tests/test_document.py -v
```

Expected: failures because `mark_saved`, `replace_map`, and `new_map` are not defined.

- [ ] **Step 7: Implement the state transitions**

Extend `MapDocument`:

```python
    def mark_saved(self, path: Path) -> None:
        self.current_path = path
        self.dirty = False

    def replace_map(
        self,
        network_map: NetworkMap,
        path: Path | None = None,
    ) -> None:
        self.network_map = network_map
        self.current_path = path
        self.dirty = False

    def new_map(self) -> None:
        self.replace_map(
            NetworkMap(site_name="Untitled Network")
        )
```

- [ ] **Step 8: Verify Task 1 GREEN**

Run:

```powershell
pytest tests/test_document.py -v
```

Expected: all document tests pass.

- [ ] **Step 9: Run the full suite**

Run:

```powershell
pytest -v
```

Expected: all previous tests plus the new document tests pass.

- [ ] **Step 10: Commit Task 1**

```powershell
git add wireatlas/core/document.py tests/test_document.py
git commit -m "Add map document state model"
```

---

### Task 2: Support Topology Reset and Saved-Position Restoration

**Files:**
- Modify: `wireatlas/ui/topology_view.py`
- Modify: `tests/test_topology_view.py`

**Interfaces:**
- Consumes:
  - existing `TopologyView.add_device(device: Device) -> DeviceNode`
- Produces:
  - `TopologyView.add_device_at_saved_position(device: Device) -> DeviceNode`
  - `TopologyView.clear_devices() -> None`

- [ ] **Step 1: Add failing tests for restoring saved coordinates**

Append to `tests/test_topology_view.py`:

```python
def test_add_device_at_saved_position_preserves_coordinates(qapp):
    view = TopologyView()
    device = Device(
        name="Loaded Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=515.0,
        y=225.0,
    )

    node = view.add_device_at_saved_position(device)

    assert device.x == 515.0
    assert device.y == 225.0
    assert node.pos().x() == 515.0
    assert node.pos().y() == 225.0
    assert view.node_for_device(device.id) is node
```

Ensure `Device` and `DeviceType` are imported from `wireatlas.models.device`.

- [ ] **Step 2: Add failing test for clearing nodes**

Append:

```python
def test_clear_devices_removes_nodes_and_lookup_entries(qapp):
    view = TopologyView()
    device = Device(
        name="Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(device)
    assert view.node_for_device(device.id) is not None

    view.clear_devices()

    assert view.node_for_device(device.id) is None
    assert view.graphics_scene.items() == []
```

- [ ] **Step 3: Run targeted topology tests and verify RED**

Run:

```powershell
pytest tests/test_topology_view.py -v
```

Expected: failures because the two new methods do not exist.

- [ ] **Step 4: Implement saved-position insertion without mutating coordinates**

In `wireatlas/ui/topology_view.py`, add:

```python
    def add_device_at_saved_position(
        self,
        device: Device,
    ) -> DeviceNode:
        node = DeviceNode(device)
        node.setPos(device.x, device.y)

        self.graphics_scene.addItem(node)
        self._nodes[device.id] = node

        return node
```

- [ ] **Step 5: Implement topology reset**

Add:

```python
    def clear_devices(self) -> None:
        self.graphics_scene.clear()
        self._nodes.clear()
```

- [ ] **Step 6: Verify Task 2 GREEN**

Run:

```powershell
pytest tests/test_topology_view.py -v
```

Expected: all topology-view tests pass.

- [ ] **Step 7: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit Task 2**

```powershell
git add wireatlas/ui/topology_view.py tests/test_topology_view.py
git commit -m "Support topology map restoration"
```

---

### Task 3: Integrate `MapDocument`, Dirty State, and Window Title

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Consumes:
  - `MapDocument`
- Produces:
  - `MainWindow.document: MapDocument`
  - compatibility property or usage path for `network_map`
  - `MainWindow._mark_dirty() -> None`
  - `MainWindow._update_window_title() -> None`

The existing tests currently access `window.network_map`. Preserve that public attribute behavior with a property rather than rewriting unrelated tests.

- [ ] **Step 1: Add failing tests for initial document/title state**

Append to `tests/test_main_window.py`:

```python
def test_main_window_starts_clean_with_site_in_title(qapp):
    window = MainWindow()

    assert window.document.dirty is False
    assert window.windowTitle() == "WireAtlas — Untitled Network"
```

- [ ] **Step 2: Add failing test for site edit dirty state**

Append:

```python
def test_site_name_change_marks_document_dirty_and_updates_title(qapp):
    window = MainWindow()

    window.site_name_input.setText("Dental Office")

    assert window.network_map.site_name == "Dental Office"
    assert window.document.dirty is True
    assert window.windowTitle() == "WireAtlas — Dental Office *"
```

- [ ] **Step 3: Add failing test that adding a device marks dirty**

Append:

```python
def test_add_device_marks_document_dirty(qapp):
    window = MainWindow()
    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(device)

    assert window.document.dirty is True
    assert window.windowTitle() == "WireAtlas — Untitled Network *"
```

- [ ] **Step 4: Run targeted tests and verify RED**

Run:

```powershell
pytest tests/test_main_window.py -k "clean_with_site_in_title or site_name_change_marks or add_device_marks" -v
```

Expected: failures because `document` and new title behavior do not exist.

- [ ] **Step 5: Integrate `MapDocument` into `MainWindow`**

In `wireatlas/ui/main_window.py`, import:

```python
from wireatlas.core.document import MapDocument
```

Replace direct initial map construction with:

```python
self.document = MapDocument()
```

Add:

```python
@property
def network_map(self) -> NetworkMap:
    return self.document.network_map
```

Remove the old assignment:

```python
self.network_map = NetworkMap(...)
```

- [ ] **Step 6: Add title and dirty helpers**

Add:

```python
    def _update_window_title(self) -> None:
        marker = " *" if self.document.dirty else ""
        self.setWindowTitle(
            f"WireAtlas — {self.network_map.site_name}{marker}"
        )

    def _mark_dirty(self) -> None:
        self.document.mark_dirty()
        self._update_window_title()
```

Call `_update_window_title()` once at the end of `__init__`.

- [ ] **Step 7: Mark site-name edits dirty**

Update `_update_site_name`:

```python
    def _update_site_name(self, value: str) -> None:
        self.network_map.site_name = value
        self._mark_dirty()
```

- [ ] **Step 8: Mark added devices dirty**

At the end of `add_device`:

```python
self._mark_dirty()
```

- [ ] **Step 9: Verify targeted tests GREEN**

Run:

```powershell
pytest tests/test_main_window.py -k "clean_with_site_in_title or site_name_change_marks or add_device_marks" -v
```

Expected: pass.

- [ ] **Step 10: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 11: Commit Task 3**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Track dirty map state in main window"
```

---

### Task 4: Enable File Actions and Implement Save / Save As

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Produces:
  - `MainWindow.save_as_action`
  - `MainWindow._save() -> bool`
  - `MainWindow._save_as() -> bool`
  - `MainWindow._ensure_wireatlas_extension(path: Path) -> Path`
  - `MainWindow._suggested_filename() -> str`
  - `MainWindow._show_save_error(error: Exception) -> None`

Return `bool` from Save methods so New/Open/Close can later continue only after a successful save.

- [ ] **Step 1: Add failing toolbar-state test**

Update or extend the toolbar test to assert:

```python
assert window.new_action.isEnabled()
assert window.open_action.isEnabled()
assert window.save_action.isEnabled()
assert window.save_as_action.isEnabled()
assert window.add_device_action.isEnabled()
assert not window.add_connection_action.isEnabled()
assert not window.export_pdf_action.isEnabled()
```

- [ ] **Step 2: Add failing test for extension helper**

```python
def test_ensure_wireatlas_extension_appends_when_missing(qapp):
    window = MainWindow()

    result = window._ensure_wireatlas_extension(
        Path("office-map")
    )

    assert result == Path("office-map.wireatlas")
```

Also test no duplication:

```python
def test_ensure_wireatlas_extension_keeps_existing_extension(qapp):
    window = MainWindow()

    result = window._ensure_wireatlas_extension(
        Path("office-map.wireatlas")
    )

    assert result == Path("office-map.wireatlas")
```

Ensure `Path` is imported.

- [ ] **Step 3: Add failing test for suggested filename**

```python
def test_suggested_filename_uses_site_name(qapp):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    assert (
        window._suggested_filename()
        == "Main Office.wireatlas"
    )
```

- [ ] **Step 4: Run these tests and verify RED**

```powershell
pytest tests/test_main_window.py -k "toolbar or ensure_wireatlas or suggested_filename" -v
```

Expected: failures for missing Save As action/helpers and currently disabled New/Open/Save.

- [ ] **Step 5: Add Save As toolbar action and enable file actions**

In `_build_toolbar()` create:

```python
self.save_as_action = toolbar.addAction("Save As")
```

Do not disable New, Open, Save, or Save As.

Continue disabling:

```python
self.add_connection_action.setEnabled(False)
self.export_pdf_action.setEnabled(False)
```

- [ ] **Step 6: Add pure path/name helpers**

Import:

```python
from pathlib import Path
```

Add:

```python
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
```

- [ ] **Step 7: Verify helper/toolbar tests GREEN**

```powershell
pytest tests/test_main_window.py -k "toolbar or ensure_wireatlas or suggested_filename" -v
```

Expected: pass.

- [ ] **Step 8: Add failing test for Save with existing path**

Use monkeypatch against the name imported into `wireatlas.ui.main_window`:

```python
def test_save_existing_path_saves_and_clears_dirty(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    path = tmp_path / "office.wireatlas"
    window.document.current_path = path

    calls = []

    def fake_save(network_map, save_path):
        calls.append((network_map, save_path))

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        fake_save,
    )

    assert window._save() is True
    assert calls == [(window.network_map, path)]
    assert window.document.dirty is False
    assert window.document.current_path == path
```

- [ ] **Step 9: Run the Save test and verify RED**

```powershell
pytest tests/test_main_window.py::test_save_existing_path_saves_and_clears_dirty -v
```

Expected: fail because `_save()` does not exist.

- [ ] **Step 10: Implement Save for an existing path**

Import:

```python
from wireatlas.core.storage import save_network_map
```

Add:

```python
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
```

Do not implement `_show_save_error` with real UI yet; add a minimal method so this task can compile:

```python
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
```

Import `QMessageBox`.

- [ ] **Step 11: Verify existing-path Save GREEN**

```powershell
pytest tests/test_main_window.py::test_save_existing_path_saves_and_clears_dirty -v
```

Expected: pass.

- [ ] **Step 12: Add failing Save As success test**

Monkeypatch `QFileDialog.getSaveFileName` and `save_network_map`:

```python
def test_save_as_appends_extension_and_adopts_path_after_success(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    selected = tmp_path / "office-map"
    saved = []

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (
            str(selected),
            "WireAtlas Network Maps (*.wireatlas)",
        ),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        lambda network_map, path: saved.append(
            (network_map, path)
        ),
    )

    assert window._save_as() is True

    expected = tmp_path / "office-map.wireatlas"
    assert saved == [(window.network_map, expected)]
    assert window.document.current_path == expected
    assert window.document.dirty is False
```

Import `QFileDialog` in the test if not already present.

- [ ] **Step 13: Add failing Save As cancel test**

```python
def test_save_as_cancel_returns_false_without_changing_state(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Office")
    assert window.document.dirty is True

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )

    assert window._save_as() is False
    assert window.document.current_path is None
    assert window.document.dirty is True
```

- [ ] **Step 14: Run Save As tests and verify RED**

```powershell
pytest tests/test_main_window.py -k "save_as" -v
```

Expected: fail because `_save_as()` does not exist.

- [ ] **Step 15: Implement Save As**

Import `QFileDialog`.

Add:

```python
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
```

- [ ] **Step 16: Add failing test that failed Save As does not adopt path**

```python
def test_failed_save_as_keeps_dirty_and_does_not_adopt_path(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    selected = tmp_path / "broken"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(selected), ""),
    )

    def fail_save(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        fail_save,
    )
    monkeypatch.setattr(
        window,
        "_show_save_error",
        lambda error: None,
    )

    assert window._save_as() is False
    assert window.document.current_path is None
    assert window.document.dirty is True
```

- [ ] **Step 17: Verify Save and Save As GREEN**

```powershell
pytest tests/test_main_window.py -k "save" -v
```

Expected: all Save-related tests pass.

- [ ] **Step 18: Connect toolbar actions**

In `__init__`, connect:

```python
self.save_action.triggered.connect(self._save)
self.save_as_action.triggered.connect(self._save_as)
```

New/Open are enabled but will be connected in later tasks.

- [ ] **Step 19: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 20: Commit Task 4**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Add save and save as workflows"
```

---

### Task 5: Add Clean Map Rebuild and New Workflow

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Produces:
  - `MainWindow._rebuild_from_document() -> None`
  - `MainWindow._new_document() -> None`

This task implements the clean-document path only. Unsaved-change prompting is added later so the rebuild behavior can be tested independently first.

- [ ] **Step 1: Add failing test for rebuilding from loaded document**

```python
def test_rebuild_from_document_restores_nodes_and_clears_details(
    qapp,
    tmp_path,
):
    window = MainWindow()

    device = Device(
        name="Loaded Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=420.0,
        y=180.0,
    )
    network_map = NetworkMap(
        site_name="Loaded Site",
        root_device_id=device.id,
        devices=[device],
    )

    window.document.replace_map(
        network_map,
        tmp_path / "loaded.wireatlas",
    )

    window._rebuild_from_document()

    node = window.topology_view.node_for_device(device.id)

    assert window.site_name_input.text() == "Loaded Site"
    assert node is not None
    assert node.pos().x() == 420.0
    assert node.pos().y() == 180.0
    assert window.network_map.root_device_id == device.id
    assert window.details_panel.form_widget.isHidden()
    assert window.document.dirty is False
```

Ensure `NetworkMap` is imported into the test.

- [ ] **Step 2: Run rebuild test and verify RED**

```powershell
pytest tests/test_main_window.py::test_rebuild_from_document_restores_nodes_and_clears_details -v
```

Expected: failure because `_rebuild_from_document` does not exist.

- [ ] **Step 3: Implement GUI rebuild without dirtying site name**

Import:

```python
from PySide6.QtCore import QSignalBlocker
```

Add:

```python
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
```

The signal blocker is required so loading/resetting a site name does not accidentally mark a clean document dirty.

- [ ] **Step 4: Verify rebuild test GREEN**

```powershell
pytest tests/test_main_window.py::test_rebuild_from_document_restores_nodes_and_clears_details -v
```

Expected: pass.

- [ ] **Step 5: Add failing clean-New test**

```python
def test_new_document_resets_clean_map_and_gui(qapp):
    window = MainWindow()

    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    window.add_device(device)
    window.site_name_input.setText("Old Site")

    window._new_document()

    assert window.network_map.site_name == "Untitled Network"
    assert window.network_map.devices == []
    assert window.document.current_path is None
    assert window.document.dirty is False
    assert window.site_name_input.text() == "Untitled Network"
    assert window.topology_view.graphics_scene.items() == []
    assert window.windowTitle() == "WireAtlas — Untitled Network"
```

- [ ] **Step 6: Run New test and verify RED**

```powershell
pytest tests/test_main_window.py::test_new_document_resets_clean_map_and_gui -v
```

Expected: failure because `_new_document()` does not exist.

- [ ] **Step 7: Implement clean New reset**

Add:

```python
    def _new_document(self) -> None:
        self.document.new_map()
        self._rebuild_from_document()
```

- [ ] **Step 8: Verify Task 5 GREEN**

```powershell
pytest tests/test_main_window.py -k "rebuild_from_document or new_document" -v
```

Expected: pass.

- [ ] **Step 9: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 10: Commit Task 5**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Add map rebuild and new document reset"
```

---

### Task 6: Implement Open, Structural Errors, and Warning Review

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Consumes:
  - `load_network_map(path: Path) -> NetworkMap`
  - `validate_network_map_data(network_map: NetworkMap) -> list[str]`
  - `WireAtlasFileError`
  - `_rebuild_from_document()`
- Produces:
  - `MainWindow._open_document() -> bool`
  - `MainWindow._confirm_open_warnings(warnings: list[str]) -> bool`
  - `MainWindow._show_open_error(error: Exception) -> None`

- [ ] **Step 1: Add failing test for valid Open**

```python
def test_open_valid_map_replaces_document_and_rebuilds_gui(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "loaded.wireatlas"
    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=300.0,
        y=140.0,
    )
    loaded = NetworkMap(
        site_name="Loaded Office",
        root_device_id=device.id,
        devices=[device],
    )

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: [],
    )

    assert window._open_document() is True

    assert window.network_map is loaded
    assert window.document.current_path == path
    assert window.document.dirty is False
    assert window.site_name_input.text() == "Loaded Office"

    node = window.topology_view.node_for_device(device.id)
    assert node is not None
    assert node.pos().x() == 300.0
    assert node.pos().y() == 140.0
```

- [ ] **Step 2: Run valid-Open test and verify RED**

```powershell
pytest tests/test_main_window.py::test_open_valid_map_replaces_document_and_rebuilds_gui -v
```

Expected: fail because `_open_document()` does not exist.

- [ ] **Step 3: Implement the valid Open path**

Import:

```python
from wireatlas.core.storage import (
    WireAtlasFileError,
    load_network_map,
    save_network_map,
)
from wireatlas.core.validation import validate_network_map_data
```

Add:

```python
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
```

Add temporary concrete dialog helpers now so the class is complete:

```python
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
```

- [ ] **Step 4: Verify valid Open GREEN**

```powershell
pytest tests/test_main_window.py::test_open_valid_map_replaces_document_and_rebuilds_gui -v
```

Expected: pass.

- [ ] **Step 5: Add failing warning-cancel preservation test**

```python
def test_open_warning_cancel_leaves_current_document_untouched(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")
    original_map = window.network_map
    original_dirty = window.document.dirty

    path = tmp_path / "warning.wireatlas"
    loaded = NetworkMap(site_name="Warning Site")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: ["Bad IP"],
    )
    monkeypatch.setattr(
        window,
        "_confirm_open_warnings",
        lambda warnings: False,
    )

    assert window._open_document() is False

    assert window.network_map is original_map
    assert window.network_map.site_name == "Current Work"
    assert window.document.dirty is original_dirty
```

- [ ] **Step 6: Add failing warning-accept test**

```python
def test_open_warning_accept_replaces_document(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "warning.wireatlas"
    loaded = NetworkMap(site_name="Warning Site")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )
    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: ["Bad IP"],
    )
    monkeypatch.setattr(
        window,
        "_confirm_open_warnings",
        lambda warnings: True,
    )

    assert window._open_document() is True
    assert window.network_map is loaded
    assert window.document.current_path == path
    assert window.document.dirty is False
```

- [ ] **Step 7: Add failing structural-error preservation test**

```python
def test_open_error_leaves_current_document_untouched(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")
    original_map = window.network_map
    original_path = window.document.current_path
    original_dirty = window.document.dirty

    path = tmp_path / "broken.wireatlas"

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    def fail_load(selected_path):
        raise WireAtlasFileError(
            "File is not valid WireAtlas data"
        )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        fail_load,
    )
    monkeypatch.setattr(
        window,
        "_show_open_error",
        lambda error: None,
    )

    assert window._open_document() is False

    assert window.network_map is original_map
    assert window.document.current_path is original_path
    assert window.document.dirty is original_dirty
    assert window.site_name_input.text() == "Current Work"
```

- [ ] **Step 8: Run Open behavior tests**

```powershell
pytest tests/test_main_window.py -k "open_" -v
```

Expected: all Open tests pass.

- [ ] **Step 9: Connect the Open toolbar action**

In `__init__`:

```python
self.open_action.triggered.connect(
    self._open_document
)
```

- [ ] **Step 10: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 11: Commit Task 6**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Add open map workflow"
```

---

### Task 7: Add Shared Unsaved-Changes Protection

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Produces:
  - `MainWindow._confirm_discard_or_save() -> bool`
  - New/Open wrapper behavior that proceeds only when safe

`_confirm_discard_or_save()` returns `True` only when the caller may proceed with the destructive action.

- [ ] **Step 1: Add failing test that clean documents proceed without prompt**

```python
def test_confirm_discard_or_save_allows_clean_document(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: pytest.fail(
            "clean document should not prompt"
        ),
    )

    assert window._confirm_discard_or_save() is True
```

Ensure `pytest` and `QMessageBox` are imported in the test file.

- [ ] **Step 2: Add failing tests for dirty Cancel / Discard / Save**

Use a monkeypatchable helper rather than invoking a real modal prompt. First add a small method boundary to the design:

```python
MainWindow._ask_unsaved_changes() -> QMessageBox.StandardButton
```

Tests:

```python
def test_unsaved_cancel_blocks_action(qapp, monkeypatch):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Cancel,
    )

    assert window._confirm_discard_or_save() is False


def test_unsaved_discard_allows_action(qapp, monkeypatch):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Discard,
    )

    assert window._confirm_discard_or_save() is True


def test_unsaved_save_allows_action_only_after_success(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Save,
    )
    monkeypatch.setattr(
        window,
        "_save",
        lambda: True,
    )

    assert window._confirm_discard_or_save() is True
```

Add failure/cancel case:

```python
def test_unsaved_save_failure_blocks_action(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Save,
    )
    monkeypatch.setattr(
        window,
        "_save",
        lambda: False,
    )

    assert window._confirm_discard_or_save() is False
```

- [ ] **Step 3: Run unsaved tests and verify RED**

```powershell
pytest tests/test_main_window.py -k "unsaved or confirm_discard" -v
```

Expected: fail because the helper methods do not exist.

- [ ] **Step 4: Implement the unsaved prompt helper**

Add:

```python
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
```

- [ ] **Step 5: Implement shared guard**

Add:

```python
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
```

This automatically satisfies the requirement that canceling Save As or failing Save cancels the pending destructive action because `_save()` returns `False` in both cases.

- [ ] **Step 6: Verify unsaved helper tests GREEN**

```powershell
pytest tests/test_main_window.py -k "unsaved or confirm_discard" -v
```

Expected: pass.

- [ ] **Step 7: Add failing guarded-New tests**

```python
def test_dirty_new_cancel_keeps_current_document(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")
    original_map = window.network_map

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )

    window._request_new_document()

    assert window.network_map is original_map
    assert window.network_map.site_name == "Current Work"


def test_dirty_new_proceeds_after_confirmation(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: True,
    )

    window._request_new_document()

    assert window.network_map.site_name == "Untitled Network"
    assert window.document.dirty is False
```

- [ ] **Step 8: Implement guarded New wrapper**

Add:

```python
    def _request_new_document(self) -> None:
        if not self._confirm_discard_or_save():
            return

        self._new_document()
```

Connect toolbar:

```python
self.new_action.triggered.connect(
    self._request_new_document
)
```

- [ ] **Step 9: Refactor Open into guarded wrapper + unguarded loader**

Rename the current file-picker/load implementation to:

```python
def _open_document_from_dialog(self) -> bool:
    ...
```

Then add:

```python
    def _request_open_document(self) -> bool:
        if not self._confirm_discard_or_save():
            return False

        return self._open_document_from_dialog()
```

Connect:

```python
self.open_action.triggered.connect(
    self._request_open_document
)
```

Update existing Open tests to call `_open_document_from_dialog()` when they are testing loading itself rather than the unsaved guard.

- [ ] **Step 10: Add guarded-Open cancellation test**

```python
def test_dirty_open_cancel_does_not_show_file_picker(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )
    monkeypatch.setattr(
        window,
        "_open_document_from_dialog",
        lambda: pytest.fail(
            "open dialog should not run"
        ),
    )

    assert window._request_open_document() is False
```

- [ ] **Step 11: Run New/Open unsaved tests**

```powershell
pytest tests/test_main_window.py -k "new_ or open_ or unsaved or confirm_discard" -v
```

Expected: pass.

- [ ] **Step 12: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 13: Commit Task 7**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Protect unsaved map changes"
```

---

### Task 8: Protect Application Close

**Files:**
- Modify: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Consumes:
  - `_confirm_discard_or_save() -> bool`
- Produces:
  - `MainWindow.closeEvent(event) -> None`

- [ ] **Step 1: Add lightweight fake close event in test**

In `tests/test_main_window.py`:

```python
class FakeCloseEvent:
    def __init__(self):
        self.accepted = False
        self.ignored = False

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True
```

- [ ] **Step 2: Add failing close-cancel test**

```python
def test_close_event_ignores_when_unsaved_guard_blocks(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    event = FakeCloseEvent()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )

    window.closeEvent(event)

    assert event.ignored is True
    assert event.accepted is False
```

- [ ] **Step 3: Add failing close-accept test**

```python
def test_close_event_accepts_when_unsaved_guard_allows(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    event = FakeCloseEvent()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: True,
    )

    window.closeEvent(event)

    assert event.accepted is True
    assert event.ignored is False
```

- [ ] **Step 4: Run close tests and verify RED**

```powershell
pytest tests/test_main_window.py -k "close_event" -v
```

Expected: fail because `closeEvent` does not implement the guard.

- [ ] **Step 5: Implement close protection**

Add:

```python
    def closeEvent(self, event) -> None:
        if self._confirm_discard_or_save():
            event.accept()
        else:
            event.ignore()
```

- [ ] **Step 6: Verify close tests GREEN**

```powershell
pytest tests/test_main_window.py -k "close_event" -v
```

Expected: pass.

- [ ] **Step 7: Run full regression suite**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit Task 8**

```powershell
git add wireatlas/ui/main_window.py tests/test_main_window.py
git commit -m "Protect unsaved changes on close"
```

---

### Task 9: Verify Real Dialog Copy and End-to-End State Transitions

**Files:**
- Modify only if needed: `wireatlas/ui/main_window.py`
- Modify: `tests/test_main_window.py`

**Interfaces:**
- Validates the complete Milestone 2 workflow.

- [ ] **Step 1: Add test that Save with no path delegates to Save As**

```python
def test_save_without_path_delegates_to_save_as(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    calls = []

    monkeypatch.setattr(
        window,
        "_save_as",
        lambda: calls.append("save-as") or True,
    )

    assert window._save() is True
    assert calls == ["save-as"]
```

- [ ] **Step 2: Add test that Save As failure preserves prior current path**

This catches a subtle regression if Save As is used on an already named document:

```python
def test_failed_save_as_preserves_existing_current_path(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    old_path = tmp_path / "old.wireatlas"
    window.document.current_path = old_path
    window.document.mark_dirty()

    selected = tmp_path / "new"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(selected), ""),
    )

    def fail_save(*args, **kwargs):
        raise OSError("write failed")

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        fail_save,
    )
    monkeypatch.setattr(
        window,
        "_show_save_error",
        lambda error: None,
    )

    assert window._save_as() is False
    assert window.document.current_path == old_path
    assert window.document.dirty is True
```

- [ ] **Step 3: Add test that Open cancel from file picker changes nothing**

```python
def test_open_file_picker_cancel_changes_nothing(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    original_map = window.network_map
    original_dirty = window.document.dirty

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("", ""),
    )

    assert window._open_document_from_dialog() is False
    assert window.network_map is original_map
    assert window.document.dirty is original_dirty
```

- [ ] **Step 4: Run the new edge-case tests**

```powershell
pytest tests/test_main_window.py -k "without_path or preserves_existing or file_picker_cancel" -v
```

Expected: pass if earlier implementations are correct; if any test fails, use systematic debugging before changing production code.

- [ ] **Step 5: Run the full suite with verbose output**

```powershell
pytest -v
```

Expected: every test passes.

- [ ] **Step 6: Check repository status**

```powershell
git status
```

Expected: only intentional test/code changes from this task, or clean if no correction was required.

- [ ] **Step 7: Commit any Task 9 test additions**

```powershell
git add tests/test_main_window.py wireatlas/ui/main_window.py
git commit -m "Add persistence workflow edge case coverage"
```

If `wireatlas/ui/main_window.py` did not change, omit it from `git add`.

---

### Task 10: Manual GUI Verification

**Files:**
- No expected code changes unless manual verification reveals a defect.

**Interfaces:**
- Verifies real PySide6 behavior that monkeypatched tests cannot fully demonstrate.

- [ ] **Step 1: Run the full automated suite one final time before manual testing**

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Launch WireAtlas**

```powershell
python -m wireatlas.main
```

- [ ] **Step 3: Verify clean startup**

Confirm:

- Title is `WireAtlas — Untitled Network`
- No `*` is present
- New, Open, Save, Save As, and Add Device are enabled
- Add Connection and Export PDF remain disabled

- [ ] **Step 4: Verify dirty-state behavior**

Change the site name.

Confirm:

- title updates immediately
- `*` appears

Add a device.

Confirm:

- device appears on the topology
- details selection still works
- document remains visibly dirty

- [ ] **Step 5: Verify first Save / Save As**

Choose Save.

Confirm:

- Save As dialog appears because the document has no path
- suggested filename uses the site name
- leaving off `.wireatlas` still results in a `.wireatlas` file
- successful Save removes the `*`

- [ ] **Step 6: Verify direct Save**

Make another change, then choose Save.

Confirm:

- no Save As dialog appears
- the existing file is updated
- `*` disappears after success

- [ ] **Step 7: Verify reopen continuity**

Close and relaunch WireAtlas.

Open the saved file.

Confirm:

- site name restores
- all saved devices restore
- root status restores
- node positions restore
- details panel starts clear
- title shows the loaded site name
- no `*` is present immediately after Open

- [ ] **Step 8: Verify warning workflow**

Using a deliberately questionable but structurally valid `.wireatlas` test file, confirm:

- warning dialog appears
- Open Anyway opens it
- Cancel leaves the existing map untouched

Do not use a customer file for this test.

- [ ] **Step 9: Verify structural-error workflow**

Try opening a deliberately invalid/non-WireAtlas JSON file.

Confirm:

- clear Open error appears
- existing document remains unchanged

- [ ] **Step 10: Verify unsaved New protection**

Make the map dirty and choose New.

Test each path:

- Cancel keeps the current map
- Discard creates a clean Untitled Network
- Save saves successfully and then creates a clean Untitled Network
- canceling the Save As picker leaves the current map open

- [ ] **Step 11: Verify unsaved Open protection**

Make the map dirty and choose Open.

Confirm:

- Cancel keeps current work
- Discard proceeds to file picker
- Save proceeds only after a successful save
- canceling Save As prevents the Open operation

- [ ] **Step 12: Verify close protection**

Make the map dirty and close the application.

Confirm:

- Cancel keeps WireAtlas open
- Discard closes
- Save closes only after successful save
- canceling Save As keeps WireAtlas open

- [ ] **Step 13: If manual testing reveals a defect, stop and use systematic debugging**

Do not patch the symptom directly. Reproduce the defect with a failing automated test first, then apply the minimum fix.

---

### Task 11: Final Verification and Branch Readiness

**Files:**
- No expected changes.

- [ ] **Step 1: Run full automated verification**

```powershell
pytest -v
```

Expected: all tests pass with no failures or errors.

- [ ] **Step 2: Verify branch**

```powershell
git branch --show-current
```

Expected:

```text
gui-milestone-2-persistence
```

- [ ] **Step 3: Verify working tree**

```powershell
git status
```

Expected:

```text
nothing to commit, working tree clean
```

- [ ] **Step 4: Review milestone commit history**

```powershell
git log --oneline --decorate -12
```

Confirm the persistence work is split into understandable commits and remains on the feature branch.

- [ ] **Step 5: Do not merge yet**

At this point invoke the branch-finishing workflow and choose the integration method only after final verification is fresh.

## Plan Self-Review

### Spec Coverage

Covered:

- New
- Save
- Save As
- Open
- `.wireatlas` extension behavior
- suggested filename from site name
- document path state
- dirty tracking
- title `*`
- saved-position restoration
- root preservation
- topology rebuild
- details clearing
- structural load errors
- data-warning Open Anyway / Cancel path
- Save / Discard / Cancel protection for New/Open/Close
- canceled Save As blocking destructive actions
- failed Save blocking destructive actions
- failed/canceled Open preserving existing work
- toolbar enable/disable state
- full regression testing
- manual GUI verification
- no scope creep into connections, editing, discovery, or PDF export

### Placeholder Scan

No TBD/TODO/“implement later” placeholders are present. Each implementation task specifies concrete interfaces, tests, commands, and minimal code.

### Type / Naming Consistency

The plan consistently uses:

- `MapDocument`
- `network_map`
- `current_path: Path | None`
- `dirty: bool`
- `mark_dirty()`
- `mark_saved(path)`
- `replace_map(network_map, path)`
- `new_map()`
- `TopologyView.add_device_at_saved_position(device)`
- `TopologyView.clear_devices()`
- `MainWindow._save()`
- `MainWindow._save_as()`
- `MainWindow._rebuild_from_document()`
- `MainWindow._new_document()`
- `MainWindow._open_document_from_dialog()`
- `MainWindow._request_open_document()`
- `MainWindow._request_new_document()`
- `MainWindow._confirm_discard_or_save()`
- `MainWindow._ask_unsaved_changes()`
