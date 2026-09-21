# WireAtlas

WireAtlas is a lightweight desktop application for creating, documenting, and exporting network topology maps.

## Purpose

WireAtlas is being built to make network documentation easier to create, maintain, and understand, especially when a technician is working with a network they did not build.

At its core, WireAtlas should make one question easy to answer:

**What physically connects to what?**

The goal is to keep the basic mapping experience simple enough for networking students, homelab users, and small networks while still providing a foundation capable of representing more complicated business environments.

**Complex networks shouldn't require complicated documentation.**

WireAtlas focuses on practical network documentation without requiring cloud services, accounts, or a database. The editable `.wireatlas` map remains under the user's control and can be exported to PDF when a portable reference is needed.

## Features

- Create and manage network topology maps
- Add devices manually and position them visually
- Document hostnames, IP addresses, subnet masks, subnets, VLANs, MAC addresses, vendors, and notes
- Create wired, wireless, trunk, and other connection types
- Record source and destination interfaces for connections
- Save editable maps as `.wireatlas` files
- Export topology maps and device reference information to PDF
- Automatically split large topology maps across multiple PDF pages while preserving logical branch context

## How It Works

WireAtlas is built around a simple workflow:

1. Create a new network map and give it a site name.
2. Add devices and document the network information you want to keep.
3. Position devices on the topology.
4. Add connections between devices and record connection types and interfaces.
5. Save the editable map as a `.wireatlas` file.
6. Export the topology and device reference information to PDF when a portable copy is needed.

The `.wireatlas` file remains the editable source of truth, while the PDF is intended as a read-only snapshot for sharing or reference.

## Design Philosophy

Manual network mapping is the core of WireAtlas.

Future capabilities such as network discovery, VLAN visualization, diagnostics, and other advanced features are intended to assist the technician rather than replace technician input or complicate the basic mapping workflow.

WireAtlas should remain useful whether someone is documenting a small home network or working through a larger network they did not originally build.

The project is being developed around a simple principle:

**Get the map right first. Then give the map superpowers.**

## Project Status

WireAtlas v0.1 focuses on manual network documentation and topology mapping.

This version provides the foundation for creating, arranging, saving, reopening, and exporting network maps without requiring cloud services, accounts, or a database.

Device information and topology relationships are entered and maintained manually in v0.1.

Future development is planned to include device editing, network discovery, additional network views, diagnostics, and other optional advanced features while keeping the basic mapping workflow simple.

## File Format

WireAtlas uses `.wireatlas` files as the editable source of truth for network maps.

These files store device information, connection information, topology positions, site details, and other map data needed to reopen and continue working with a network.

PDF exports are separate from the editable project file. They are intended as portable, read-only snapshots for documentation, sharing, or reference.

Changes should be made in the `.wireatlas` file and exported again when an updated PDF is needed.

## Requirements

WireAtlas currently runs from source and has been tested on Windows with Python 3.14.

The required Python packages are listed in `requirements.txt`:

- PySide6 for the application interface
- pytest for development and automated testing

Install the required packages with:

```powershell
pip install -r requirements.txt
```

## Running from Source

From the WireAtlas project directory, activate the virtual environment and start the application:

```powershell
.\.venv\Scripts\Activate.ps1
python -m wireatlas.main
```

If PowerShell blocks virtual environment activation for the current session, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Development

WireAtlas uses automated testing as a core part of the development workflow.

The test suite covers the data model, file storage, validation, dialogs, topology behavior, document state, GUI workflows, and PDF export.

Run the full test suite from the project directory with:

```powershell
pytest
```

## License

Copyright (C) 2026 Paul Planchon

WireAtlas is open source software licensed under the GNU General Public License v3.0 only (`GPL-3.0-only`).

You are free to use, study, modify, and redistribute WireAtlas under the terms of the GPLv3. Distributed modified versions must remain available under the same open source license terms.

See [LICENSE](LICENSE) for the complete license terms.
