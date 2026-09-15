from wireatlas.core.topology import validate_topology
from wireatlas.models.connection import Connection
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap


def test_valid_topology_has_no_errors():
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    connection = Connection(
        source_device_id=router.id,
        destination_device_id=switch.id,
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id=router.id,
        devices=[router, switch],
        connections=[connection],
    )

    assert validate_topology(network_map) == []


def test_connection_to_missing_device_returns_error():
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    connection = Connection(
        source_device_id=router.id,
        destination_device_id="missing-device",
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id=router.id,
        devices=[router],
        connections=[connection],
    )

    errors = validate_topology(network_map)

    assert "Connection references missing destination device: missing-device" in errors


def test_missing_root_device_returns_error():
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id="missing-root",
        devices=[router],
    )

    errors = validate_topology(network_map)

    assert "Root device does not exist: missing-root" in errors


def test_connection_from_missing_device_returns_error():
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    connection = Connection(
        source_device_id="missing-device",
        destination_device_id=switch.id,
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id=switch.id,
        devices=[switch],
        connections=[connection],
    )

    errors = validate_topology(network_map)

    assert "Connection references missing source device: missing-device" in errors