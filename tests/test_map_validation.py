from wireatlas.core.validation import validate_network_map_data
from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap
from wireatlas.models.connection import Connection


def test_validate_network_map_data_reports_topology_warning():
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

    warnings = validate_network_map_data(network_map)

    assert warnings == [
        "Connection references missing destination device: missing-device"
    ]


def test_validate_network_map_data_reports_invalid_ip():
    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.999",
    )

    network_map = NetworkMap(
        site_name="Company X",
        root_device_id=router.id,
        devices=[router],
    )

    warnings = validate_network_map_data(network_map)

    assert warnings == [
        "Main Router: invalid IP address: 192.168.1.999"
    ]

def test_validate_network_map_data_reports_invalid_mac():
    printer = Device(
        name="Office Printer",
        device_type=DeviceType.PRINTER,
        mac_address="ZZ:12:34:56:78:90",
    )

    network_map = NetworkMap(
        site_name="Company X",
        devices=[printer],
    )

    warnings = validate_network_map_data(network_map)

    assert warnings == [
        "Office Printer: invalid MAC address: ZZ:12:34:56:78:90"
    ]