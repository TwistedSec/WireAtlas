import json
import pytest

from wireatlas.core.storage import (
    WireAtlasFileError,
    load_network_map,
    save_network_map,
)

from wireatlas.models.connection import Connection, LinkType
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap

def test_save_and_load_network_map_round_trip(tmp_path):
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        hostname="MAIN-ROUTER",
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        mac_address="AA:BB:CC:DD:EE:FF",
        vlan_id="10",
        subnet="192.168.1.0/24",
        vendor="Netgate",
        notes="Primary gateway",
        x=100.0,
        y=200.0,
        field_sources={
            "name": "manual",
            "ip_address": "manual",
            "mac_address": "manual",
        },
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
        ip_address="192.168.1.2",
        x=300.0,
        y=200.0,
    )

    connection = Connection(
        source_device_id=router.id,
        destination_device_id=switch.id,
        source_interface="LAN1",
        destination_interface="Gi0/1",
        link_type=LinkType.TRUNK,
        notes="Main uplink",
    )

    original = NetworkMap(
        site_name="Company X",
        root_device_id=router.id,
        devices=[router, switch],
        connections=[connection],
        notes="Main office network",
    )

    path = tmp_path / "company-x.wireatlas"

    save_network_map(original, path)
    loaded = load_network_map(path)

    assert loaded.site_name == original.site_name
    assert loaded.root_device_id == original.root_device_id
    assert loaded.notes == original.notes
    assert loaded.format_version == original.format_version

    assert loaded.devices == original.devices
    assert loaded.connections == original.connections

    import json


def test_saved_wireatlas_file_contains_readable_json(tmp_path):
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id=router.id,
        devices=[router],
    )

    path = tmp_path / "company-x.wireatlas"

    save_network_map(network_map, path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["site_name"] == "Company X"
    assert data["root_device_id"] == router.id
    assert data["devices"][0]["name"] == "Main Router"
    assert data["devices"][0]["ip_address"] == "192.168.1.1"
    assert data["format_version"] == "0.1"

def test_load_rejects_invalid_json(tmp_path):
    path = tmp_path / "bad.wireatlas"
    path.write_text("{not-valid-json", encoding="utf-8")

    with pytest.raises(WireAtlasFileError, match="not valid WireAtlas data"):
        load_network_map(path)


def test_load_rejects_unsupported_format_version(tmp_path):
    path = tmp_path / "future.wireatlas"
    path.write_text(
        json.dumps(
            {
                "site_name": "Company X",
                "root_device_id": "",
                "devices": [],
                "connections": [],
                "format_version": "9.9",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(WireAtlasFileError, match="Unsupported WireAtlas format version"):
        load_network_map(path)


def test_load_rejects_missing_site_name(tmp_path):
    path = tmp_path / "missing-site.wireatlas"
    path.write_text(
        json.dumps(
            {
                "root_device_id": "",
                "devices": [],
                "connections": [],
                "format_version": "0.1",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(WireAtlasFileError, match="Missing required site name"):
        load_network_map(path)


def test_load_rejects_unknown_device_type(tmp_path):
    path = tmp_path / "bad-device-type.wireatlas"
    path.write_text(
        json.dumps(
            {
                "site_name": "Company X",
                "root_device_id": "device-1",
                "format_version": "0.1",
                "devices": [
                    {
                        "id": "device-1",
                        "name": "Mystery Device",
                        "device_type": "Not A Real Type",
                    }
                ],
                "connections": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(WireAtlasFileError, match="Unknown device type"):
        load_network_map(path)


def test_load_rejects_unknown_link_type(tmp_path):
    path = tmp_path / "bad-link-type.wireatlas"
    path.write_text(
        json.dumps(
            {
                "site_name": "Company X",
                "root_device_id": "device-1",
                "format_version": "0.1",
                "devices": [
                    {
                        "id": "device-1",
                        "name": "Router",
                        "device_type": "Firewall / Router",
                    },
                    {
                        "id": "device-2",
                        "name": "Switch",
                        "device_type": "Switch",
                    },
                ],
                "connections": [
                    {
                        "id": "connection-1",
                        "source_device_id": "device-1",
                        "destination_device_id": "device-2",
                        "link_type": "Quantum Tunnel",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(WireAtlasFileError, match="Unknown link type"):
        load_network_map(path)

def test_load_old_file_without_new_device_metadata(tmp_path):
    path = tmp_path / "old-map.wireatlas"
    path.write_text(
        json.dumps(
            {
                "site_name": "Legacy Site",
                "root_device_id": "device-1",
                "format_version": "0.1",
                "devices": [
                    {
                        "id": "device-1",
                        "name": "Old Router",
                        "device_type": "Firewall / Router",
                        "ip_address": "192.168.1.1",
                    }
                ],
                "connections": [],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_network_map(path)
    device = loaded.devices[0]

    assert device.hostname == ""
    assert device.subnet_mask == ""
    assert device.vendor == ""