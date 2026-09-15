# WireAtlas v0.1 Design Specification

## Purpose

WireAtlas is a local desktop network topology and documentation tool intended to supplement existing shop systems such as Syncro.

WireAtlas focuses only on documenting the technical network layout. Customer records, ticket information, addresses, phone numbers, billing information, and other job metadata remain in the existing service management platform.

## Design Principles

WireAtlas v0.1 will follow a KISS approach.

The application will:

* Run locally as a Windows desktop application.
* Require no account or login.
* Use no cloud services.
* Use no database.
* Perform no automatic network discovery in v0.1.
* Store no credentials, passwords, authentication tokens, keys, or other secrets.
* Save network maps locally.
* Keep the core data model independent from the graphical interface.

## Technology

WireAtlas v0.1 will use:

* Python
* PySide6 for the desktop interface
* Qt graphics components for the topology canvas
* JSON-based local `.wireatlas` files
* Qt PDF functionality for report generation
* pytest for core unit testing

## Application Architecture

WireAtlas will be divided into four primary areas.

### Models

The `models` package defines the data used by WireAtlas.

Initial models include:

* Device
* DeviceType
* Connection
* LinkType
* NetworkMap

Models contain network data but do not handle GUI behavior, file operations, or network discovery.

### Core

The `core` package handles application logic including:

* Topology management
* Input validation
* Save and load operations
* File format handling
* Atomic file writes
* Report data preparation

The UI will not read or write JSON directly.

### UI

The `ui` package handles:

* Main application window
* Topology canvas
* Device creation and editing
* Connection creation and editing
* Right-side details panel
* File dialogs
* PDF report generation interface

### Entry Point

`main.py` starts the PySide6 application and loads the main window.

## Device Model

Each device will contain:

* Unique internal ID
* Device name
* Device type
* Primary IP address
* Optional MAC address
* Optional VLAN ID
* Optional subnet
* Optional notes
* X coordinate
* Y coordinate

The unique internal ID will be generated independently from the IP or MAC address.

IP addresses, MAC addresses, VLAN IDs, and subnet values will initially be stored as strings. Validation will be handled outside the Device model.

### Initial Device Types

* Firewall / Router
* Switch
* Access Point
* Server / NAS
* Workstation
* Printer
* IoT Device
* Other

## Connection Model

Each connection will contain:

* Unique internal ID
* Source device ID
* Destination device ID
* Optional source interface or port
* Optional destination interface or port
* Link type
* Optional notes

### Initial Link Types

* Standard / Access
* Trunk
* Wireless
* Other

More advanced information such as negotiated speed, cable type, PoE state, and spanning-tree information is outside the scope of v0.1.

## Network Map Model

A NetworkMap represents one documented network.

It will contain:

* Site or network name
* Designated root device ID
* Devices
* Connections
* Optional map notes
* WireAtlas file format version

The root device will normally be the primary router, firewall, or gateway.

WireAtlas may display other network relationships and redundant links, but the root provides the logical starting point for organizing the topology.

## Saved Files

WireAtlas maps will use the `.wireatlas` extension.

The underlying format for v0.1 will be JSON.

Example:

`Company X.wireatlas`

The user-selected site/network name will also appear at the top of the WireAtlas interface when the map is open.

Saved files will contain the full technical map information.

They will not contain:

* Passwords
* Credentials
* Private keys
* Authentication tokens
* Customer billing information
* Customer contact information

Encryption is outside the scope of v0.1 and may be added in a future release if shop requirements justify it.

## Save Reliability

Saving will use an atomic-write approach.

WireAtlas will write the new map to a temporary file first. The existing `.wireatlas` file will only be replaced after the new file has been successfully written.

This reduces the likelihood of corrupting an existing map because of an application error, interrupted write, or system failure.

## Main Interface

The main window will contain:

* Site/network name
* Main topology canvas
* Toolbar
* Right-side details panel

### Initial Toolbar Actions

* New
* Open
* Save
* Add Device
* Add Connection
* Export PDF

## Topology Canvas

Devices will appear as draggable graphical nodes.

The default node display will contain only:

* Device name
* Device type

IP addresses, MAC addresses, VLAN information, subnet information, and other technical details will not be continuously displayed on the main canvas.

This reduces casual exposure of network information when someone walks past a technician's workstation.

This behavior is intended only as protection against casual shoulder surfing and is not considered access control.

Device positions will be stored in the `.wireatlas` file so the layout remains the same when reopened.

## Device Details Panel

Selecting a device will display its complete information in the right-side panel.

The panel may display:

* Device name
* Device type
* Primary IP
* MAC address
* VLAN
* Subnet
* Notes
* Connected devices
* Interface or port information

Selecting empty canvas space will clear or hide the detailed device information.

## VLAN and Subnet Support

VLAN and subnet information will be supported in v0.1 but remain optional.

Simple networks will not require VLAN data.

Connections may also be marked as trunk links.

A dedicated VLAN management subsystem is outside the scope of v0.1.

## PDF Reporting

WireAtlas v0.1 will support PDF report export.

The PDF will intentionally contain the full network details rather than applying the privacy-oriented screen behavior used by the live topology view.

The initial report will contain:

* Site/network name
* Report generation date
* Topology diagram
* Device inventory
* Device names and types
* IP addresses
* MAC addresses
* VLAN and subnet information
* Device notes
* Connection information
* Source and destination interfaces or ports
* Link types
* Identification of the root router/firewall

Customer and ticket metadata will not be duplicated because those records remain in Syncro.

## Validation

WireAtlas should provide clear user-facing errors rather than crash when invalid information is entered.

Initial validation will include:

* Invalid IP addresses
* Invalid MAC addresses
* Duplicate internal device IDs
* Connections referencing nonexistent devices
* Invalid or incomplete topology data
* Attempts to finalize a map without a designated root device

Optional fields may remain blank.

## Testing

Core application logic will be tested using pytest.

Initial automated tests should cover:

* Device creation
* Preservation of device fields
* Connection creation
* Rejection of invalid connections
* NetworkMap creation
* Save operations
* Load operations
* Save/load round trips
* Preservation of device positions
* Preservation of the root device
* IP validation
* MAC validation
* Report-data generation

The graphical interface will primarily use practical manual testing during v0.1 development rather than extensive automated GUI testing.

## Future Development

Features intentionally postponed beyond v0.1 include:

* Automatic network discovery
* Starting discovery from the root router and mapping outward
* Multiple IP addresses per device
* Encrypted map files
* Rich VLAN management
* Link-speed detection
* PoE information
* Spanning-tree information
* Device polling
* Cloud synchronization
* Multi-user collaboration

The v0.1 architecture should allow these features to be added later without replacing the core Device, Connection, and NetworkMap concepts.
