# WireAtlas GUI Milestone 2 Design

**Date:** 2026-09-15
**Scope:** Persistence workflow for New, Save, Save As, Open, unsaved-change protection, and map restoration.

## Goal

Make WireAtlas usable across sessions by allowing a technician to create a map, save it to a `.wireatlas` file, close the application, reopen the file later, and continue working without losing the map or its layout.

Milestone 2 builds on the existing storage and validation core rather than duplicating file-format logic in the GUI.

## User-Facing Workflow

### New

Choosing **New** creates a fresh document containing:

```text
NetworkMap(site_name="Untitled Network")
```

The current file path is cleared and the document is marked clean.

If the current document has unsaved changes, WireAtlas first prompts:

> **Save changes to <site name>?**
> Your changes will be lost if you don’t save them.

Buttons:

- Save
- Discard
- Cancel

If Save is chosen but the user later cancels the Save As file picker, the New operation is also canceled and the current document remains unchanged.

### Save

If the current document already has a file path, **Save** writes directly to that file using the existing `save_network_map()` function.

If the document has no file path, **Save** behaves like Save As.

A successful Save clears the dirty state and removes the unsaved indicator from the window title.

A failed or canceled Save does not clear the dirty state.

### Save As

Save As always opens a file picker.

The file dialog should prefer:

```text
WireAtlas Network Maps (*.wireatlas)
```

The suggested filename should be based on the site name. For example:

```text
Company X Main Office.wireatlas
```

If the user enters a filename without the `.wireatlas` extension, WireAtlas appends it automatically.

A successful Save As updates the current document path and clears the dirty state.

If saving fails, the failed filename is not adopted as the current document path.

### Open

If the current document has unsaved changes, Open first uses the same Save / Discard / Cancel workflow as New and Close.

If the user proceeds, WireAtlas presents a file picker and attempts to load the selected map using the existing `load_network_map()` function.

Open behavior:

- Structurally invalid or unsupported files are rejected.
- Structurally valid files with questionable network data may still be opened after warning review.
- Valid files with no warnings open immediately.

A failed or canceled Open must leave the current document completely untouched.

## File Validation and Warning Behavior

WireAtlas already distinguishes between structural file errors and map-data warnings. Milestone 2 exposes that distinction in the GUI.

### Structural Errors

Examples include:

- Invalid JSON
- Unsupported format version
- Missing required site name
- Unknown device type
- Unknown link type

These produce a blocking error such as:

> **Could not open the network map.**
> <specific error detail>

The current document remains unchanged.

### Questionable but Loadable Data

Examples include:

- Invalid IP address
- Invalid MAC address
- Missing root-device reference
- Connection referencing a missing source or destination device

WireAtlas shows:

> **WireAtlas found issues in this network map**
>
> The file opened successfully, but some network data may need attention:
>
> • Main Router: invalid IP address: 192.168.1.999
> • Office Printer: invalid MAC address: ZZ:12:34:56:78:90
> • Connection references missing destination device: device-123
>
> You can continue working with the map, but affected items should be reviewed.

Buttons:

- Open Anyway
- Cancel

There is no read-only mode in Milestone 2.

Cancel leaves the existing document untouched.

## Document-State Architecture

Introduce a small `MapDocument` object that owns:

- the current `NetworkMap`
- the current file path or `None`
- the dirty flag

`MainWindow` remains responsible for GUI orchestration:

- toolbar actions
- file pickers
- confirmation dialogs
- warning dialogs
- error dialogs
- rebuilding the canvas after a successful Open or New

The existing storage layer remains responsible for reading and writing `.wireatlas` files.

Conceptually:

```text
MainWindow
   │
   ├── File dialogs
   ├── Save / Discard / Cancel prompts
   ├── Warning and error dialogs
   ▼
MapDocument
   ├── network_map
   ├── current_path
   ├── dirty
   ├── mark_dirty()
   ├── mark_saved(path)
   └── replace_map(...)
           │
           ▼
wireatlas.core.storage
   ├── save_network_map()
   └── load_network_map()
```

## Dirty-State Rules

The document becomes dirty when user-visible map content changes.

Milestone 2 must mark the document dirty when:

- a device is added
- the site name changes

Later milestones will reuse the same mechanism for editing devices, dragging nodes, adding connections, and other mutations.

The document becomes clean after:

- successful Save
- successful Save As
- successful Open
- successful New

## Window Title

The title reflects both the site name and dirty state.

Clean example:

```text
WireAtlas — Company X Main Office
```

Dirty example:

```text
WireAtlas — Company X Main Office *
```

Changing the site name updates the title immediately and marks the document dirty.

## Unsaved-Changes Protection

New, Open, and application Close all use the same confirmation behavior when the document is dirty.

Prompt:

> **Save changes to <site name>?**
> Your changes will be lost if you don’t save them.

Buttons:

- Save
- Discard
- Cancel

Behavior:

- Save attempts to save first, then continues only if saving succeeds.
- Discard proceeds without saving.
- Cancel aborts the pending action.
- If Save invokes Save As and that file picker is canceled, the pending New/Open/Close action is canceled too.
- If Save fails, the pending action is canceled.

## Map Restoration

After a successful Open, WireAtlas replaces the current document with the loaded map and rebuilds the GUI state.

The rebuild process should:

1. Clear the current topology scene.
2. Clear the selected-device details panel.
3. Replace the current `NetworkMap`.
4. Update the site-name field.
5. Recreate a node for every saved device.
6. Restore each device node using its saved `x` and `y` coordinates.
7. Preserve `root_device_id`.
8. Set the current file path to the opened file.
9. Mark the document clean.
10. Update the window title.

Loaded devices must not be passed through the existing automatic-placement path because doing so would overwrite their saved positions.

The topology view therefore needs a way to add a device at its existing coordinates as well as the existing automatic-placement behavior used for newly created devices.

## New Map Reset

A successful New operation should:

1. Clear the topology scene.
2. Clear the details panel.
3. Replace the document map with `NetworkMap(site_name="Untitled Network")`.
4. Clear the current file path.
5. Mark the document clean.
6. Update the site-name field.
7. Update the window title.

## Save Failure Behavior

Save failures are non-destructive.

Display:

> **Could not save the network map.**
> <specific error detail>

After failure:

- the document remains dirty
- the current map remains unchanged
- a failed Save As path is not adopted
- a pending New/Open/Close action is canceled

## Open Failure Behavior

Open failures are non-destructive.

Display:

> **Could not open the network map.**
> <specific error detail>

After failure:

- the current document remains unchanged
- the current file path remains unchanged
- dirty state remains unchanged
- the existing canvas remains unchanged
- the existing details panel remains unchanged

## Toolbar Changes

Milestone 2 enables:

- New
- Open
- Save

Milestone 2 also adds or exposes:

- Save As

Still disabled:

- Add Connection
- Export PDF

Add Device remains enabled.

## Testing

Milestone 2 should add tests for document state, file workflows, warning behavior, and GUI integration.

### MapDocument Tests

Verify:

- starts with `Untitled Network`
- starts with no path
- starts clean
- `mark_dirty()` sets dirty state
- successful save state records path and clears dirty
- replacing a map records the new map/path and clears dirty

### Main Window State Tests

Verify:

- adding a device marks the document dirty
- editing the site name marks the document dirty
- clean title has no asterisk
- dirty title has an asterisk
- New/Open/Save are enabled
- Add Connection and Export PDF remain disabled

### Save Tests

Verify:

- Save with no path invokes Save As behavior
- Save with an existing path calls `save_network_map()` directly
- successful Save clears dirty state
- failed Save keeps dirty state
- Save As appends `.wireatlas` when omitted
- Save As updates current path only after success
- suggested Save As filename is derived from site name

### Open Tests

Verify:

- valid files replace the current document
- loaded device coordinates are preserved
- loaded root-device ID is preserved
- the topology scene is rebuilt
- details panel is cleared after Open
- warnings trigger Open Anyway / Cancel
- Cancel leaves the current document untouched
- structural file errors leave the current document untouched

### Unsaved-Change Tests

Verify:

- New prompts when dirty
- Open prompts when dirty
- Close prompts when dirty
- Save continues only after a successful save
- Discard proceeds
- Cancel aborts
- canceled Save As aborts the pending action
- failed Save aborts the pending action

### Regression Requirement

All existing core and GUI tests must continue to pass.

## Explicitly Out of Scope

Milestone 2 does not implement:

- autosave
- recent-files menus
- read-only mode
- file locking
- cloud storage
- database storage
- automatic backup copies
- edit/delete device controls
- drag-and-drop node movement
- connections
- connection rendering
- PDF export
- discovery
- provenance conflict UI
- authentication or accounts

## Success Criteria

Milestone 2 is successful when a technician can:

1. Launch WireAtlas.
2. Create or modify a network map.
3. See unsaved state clearly.
4. Save the map to a `.wireatlas` file.
5. Close or create/open another map without accidental data loss.
6. Reopen the saved map later.
7. See the same devices, root assignment, site name, and saved node positions restored.
8. Continue working from where they left off.
