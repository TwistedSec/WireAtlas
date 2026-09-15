# WireAtlas GUI Milestone 1 Design

**Date:** 2026-09-15  
**Scope:** First functional PySide6 GUI vertical slice

## Goal

Build the first usable WireAtlas desktop interface and prove one complete end-to-end workflow:

1. Launch WireAtlas.
2. Start with an `Untitled Network` map.
3. Add a device through a real dialog.
4. Create a real `Device` in the current `NetworkMap`.
5. Place that device on the topology canvas.
6. Select the device and view its full details in the right-side panel.

This milestone intentionally does not implement save/open wiring, connection creation, node dragging, discovery, or PDF export.

## Main Window Architecture

Use `QMainWindow` with a horizontal `QSplitter`.

The window contains:
- A top toolbar.
- An editable site/network name field below the toolbar.
- A central topology canvas on the left.
- A read-only device details panel on the right.
- A status bar at the bottom.

The toolbar exposes:
- New
- Open
- Save
- Add Device
- Add Connection
- Export PDF

For milestone one, only **Add Device** is enabled. The other future actions remain visible but disabled.

The current map starts as `NetworkMap(site_name="Untitled Network")`.

The site name is editable directly in the main window. A future Save workflow may require replacing `Untitled Network` with a meaningful name before saving.

## Topology Canvas

Use `QGraphicsView` and `QGraphicsScene`.

Each device appears as a rectangular node containing only:
- Device name
- Device type

IP address, MAC address, VLAN, subnet, and notes are not displayed directly on the canvas.

Nodes are selectable. Selecting a node populates the device details panel.

Milestone one does not support dragging nodes. Device positions are assigned automatically using a deterministic grid/cascade layout based on device count. The generated position is stored in the device's `x` and `y` fields.

The selected node receives a clear visual selection state.

The `QGraphicsView` / `QGraphicsScene` foundation allows later milestones to add dragging, zooming, connection lines, and richer topology interaction without replacing the canvas architecture.

## Add Device Dialog

The Add Device dialog is modal and contains:
- Name
- Device Type
- IP Address
- MAC Address
- VLAN
- Subnet
- Notes

### Required Fields

Name is required.

Device Type is required. The dropdown begins with an unselected placeholder such as `Select device type…`.

No device type is assumed by default.

### Optional Fields

IP, MAC, VLAN, subnet, and notes are optional.

Blank IP and MAC values are valid.

If an IP or MAC value is entered, the existing core validation functions are used to validate it.

Invalid input is shown as a short inline validation message associated with the field rather than through a generic error popup.

The Add action is unavailable until required fields are valid.

## Device Creation and Provenance

Submitting a valid dialog creates a real `Device` model object.

Every nonblank field entered by the technician receives per-field provenance:

```python
field_sources[field_name] = "manual"
```

Blank optional fields receive no provenance entry.

The canvas, not the dialog, determines `x` and `y`.

If no root device is currently set and the newly added device is a `Firewall / Router`, WireAtlas automatically sets that device as `NetworkMap.root_device_id`.

Manual data has priority over future discovery data. A later discovery feature must never silently overwrite a technician-entered manual value. Conflicting discovered information should be surfaced for review.

## Device Details Panel

The right-side details panel is read-only in milestone one.

When no device is selected, it shows `No device selected`.

When a device is selected, it displays:
- Name
- Device Type
- IP Address
- MAC Address
- VLAN
- Subnet
- Notes
- Root-device status

Blank values display as an em dash or equivalent neutral placeholder.

Provenance is preserved in the model but is not displayed in the first milestone. A later milestone may add subtle `Manual`, `Discovered`, or similar source indicators.

Editing existing devices is outside milestone-one scope.

## Data Flow

The GUI does not manipulate JSON directly.

```text
Add Device Dialog
        ↓
validated user input
        ↓
Device model
        ↓
current NetworkMap
        ↓
Topology View + Details Panel
```

This preserves the existing architecture:
- `models` contain data.
- `core` contains validation, storage, and topology logic.
- `ui` contains PySide6 presentation and interaction.
- `main.py` remains the application entry point.

## Error Handling

The dialog prevents invalid required fields from being submitted.

IP and MAC errors use the existing validators.

Unexpected GUI errors should not be hidden, but milestone one does not introduce a global exception framework.

File-open warnings and `WireAtlasFileError` behavior already implemented in the core are not wired into the GUI during this milestone because Open remains disabled.

## Discovery Compatibility

Automatic network discovery is not part of milestone one, but the GUI and model behavior must remain compatible with it.

Later discovery may populate fields such as:
- IP address
- MAC address
- Hostname/name when available
- Manufacturer
- Device type when evidence supports it

Discovered values should use provenance such as `discovered`.

If a discovered value conflicts with an existing manual value, WireAtlas must preserve the manual value and surface the conflict for technician review.

## Testing

GUI behavior should be tested independently from the core where practical.

Milestone-one tests should verify:
- Main window starts with `Untitled Network`.
- Add Device is enabled.
- Future toolbar actions are disabled.
- Device Type starts unselected.
- Name is required.
- Device Type is required.
- Invalid nonblank IP is rejected.
- Invalid nonblank MAC is rejected.
- Valid dialog data creates a `Device`.
- Nonblank technician-entered fields receive `manual` provenance.
- Blank optional fields receive no provenance entry.
- The first Firewall / Router becomes root when no root exists.
- A created device produces a canvas node.
- Canvas nodes display only device name and device type.
- Selecting a node populates the details panel.
- The details panel is read-only.
- Deterministic placement assigns and stores device coordinates.

Existing core tests must continue to pass.

## Explicitly Out of Scope

Milestone one does not implement:
- Save/Open GUI wiring
- File picker behavior
- Map warning dialogs
- Editing existing devices
- Deleting devices
- Add Connection behavior
- Connection rendering
- Node dragging
- Zoom controls
- Automatic discovery
- Discovery/manual conflict UI
- Device-type icons
- PDF export
- Database or cloud storage
- Authentication or accounts

## Success Criteria

Milestone one is successful when a technician can launch WireAtlas, see the main application shell, enter real device data through Add Device, see the resulting device on the topology canvas, select it, and inspect its full details in the right-side panel without bypassing the existing core models or validation architecture.
