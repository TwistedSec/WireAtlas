import json
import os
import tempfile
from pathlib import Path

from wireatlas.models.connection import Connection, LinkType
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap

class WireAtlasFileError(Exception):
    pass

def _device_to_dict(device: Device) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "device_type": device.device_type.value,
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "vlan_id": device.vlan_id,
        "subnet": device.subnet,
        "notes": device.notes,
        "x": device.x,
        "y": device.y,
        "field_sources": device.field_sources,
    }


def _connection_to_dict(connection: Connection) -> dict:
    return {
        "id": connection.id,
        "source_device_id": connection.source_device_id,
        "destination_device_id": connection.destination_device_id,
        "source_interface": connection.source_interface,
        "destination_interface": connection.destination_interface,
        "link_type": connection.link_type.value,
        "notes": connection.notes,
    }


def save_network_map(network_map: NetworkMap, path) -> None:
    path = Path(path)

    data = {
        "site_name": network_map.site_name,
        "root_device_id": network_map.root_device_id,
        "notes": network_map.notes,
        "format_version": network_map.format_version,
        "devices": [
            _device_to_dict(device)
            for device in network_map.devices
        ],
        "connections": [
            _connection_to_dict(connection)
            for connection in network_map.connections
        ],
    }

    temp_fd, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )

    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=2)

        os.replace(temp_name, path)

    except Exception:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise


def load_network_map(path) -> NetworkMap:
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise WireAtlasFileError(
            "File is not valid WireAtlas data"
        ) from exc

    format_version = data.get("format_version", "0.1")

    if format_version != "0.1":
        raise WireAtlasFileError(
            f"Unsupported WireAtlas format version: {format_version}"
        )

    site_name = data.get("site_name")

    if not site_name:
        raise WireAtlasFileError(
            "Missing required site name"
        )

    devices = []

    for device in data.get("devices", []):
        try:
            device_type = DeviceType(device["device_type"])
        except ValueError as exc:
            raise WireAtlasFileError(
                f"Unknown device type: {device['device_type']}"
            ) from exc

        devices.append(
            Device(
                id=device["id"],
                name=device["name"],
                device_type=device_type,
                ip_address=device.get("ip_address", ""),
                mac_address=device.get("mac_address", ""),
                vlan_id=device.get("vlan_id", ""),
                subnet=device.get("subnet", ""),
                notes=device.get("notes", ""),
                x=device.get("x", 0.0),
                y=device.get("y", 0.0),
                field_sources=device.get("field_sources", {}),
            )
        )

    connections = []

    for connection in data.get("connections", []):
        try:
            link_type = LinkType(
                connection.get(
                    "link_type",
                    LinkType.STANDARD_ACCESS.value,
                )
            )
        except ValueError as exc:
            raise WireAtlasFileError(
                f"Unknown link type: {connection.get('link_type')}"
            ) from exc

        connections.append(
            Connection(
                id=connection["id"],
                source_device_id=connection["source_device_id"],
                destination_device_id=connection["destination_device_id"],
                source_interface=connection.get("source_interface", ""),
                destination_interface=connection.get(
                    "destination_interface",
                    "",
                ),
                link_type=link_type,
                notes=connection.get("notes", ""),
            )
        )

    return NetworkMap(
        site_name=site_name,
        root_device_id=data.get("root_device_id", ""),
        devices=devices,
        connections=connections,
        notes=data.get("notes", ""),
        format_version=format_version,
    )