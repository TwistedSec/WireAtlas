from wireatlas.models.connection import Connection, LinkType


def test_connection_preserves_supplied_fields():
    connection = Connection(
        source_device_id="device-1",
        destination_device_id="device-2",
        source_interface="LAN1",
        destination_interface="Gi0/1",
        link_type=LinkType.TRUNK,
        notes="Primary switch uplink",
    )

    assert connection.source_device_id == "device-1"
    assert connection.destination_device_id == "device-2"
    assert connection.source_interface == "LAN1"
    assert connection.destination_interface == "Gi0/1"
    assert connection.link_type == LinkType.TRUNK
    assert connection.notes == "Primary switch uplink"


def test_connections_receive_unique_ids():
    first = Connection(
        source_device_id="device-1",
        destination_device_id="device-2",
    )

    second = Connection(
        source_device_id="device-2",
        destination_device_id="device-3",
    )

    assert first.id
    assert second.id
    assert first.id != second.id