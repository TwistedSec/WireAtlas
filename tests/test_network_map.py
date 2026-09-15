from wireatlas.models.device import Device, DeviceType
from wireatlas.models.connection import Connection
from wireatlas.models.network_map import NetworkMap


def test_network_map_preserves_supplied_fields():
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
        notes="Main office network",
    )

    assert network_map.site_name == "Company X"
    assert network_map.root_device_id == router.id
    assert network_map.devices == [router, switch]
    assert network_map.connections == [connection]
    assert network_map.notes == "Main office network"
    assert network_map.format_version == "0.1"


def test_network_maps_have_independent_device_and_connection_lists():
    first = NetworkMap(site_name="Site A")
    second = NetworkMap(site_name="Site B")

    first.devices.append(
        Device(
            name="Router",
            device_type=DeviceType.FIREWALL_ROUTER,
        )
    )

    assert len(first.devices) == 1
    assert second.devices == []
    assert first.connections == []
    assert second.connections == []