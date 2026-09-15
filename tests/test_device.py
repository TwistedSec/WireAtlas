from wireatlas.models.device import Device, DeviceType


def test_device_preserves_supplied_fields():
    device = Device(
        name="Main Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
        vlan_id="20",
        subnet="192.168.1.0/24",
        notes="Primary network gateway",
        x=100.0,
        y=200.0,
    )

    assert device.name == "Main Firewall"
    assert device.device_type == DeviceType.FIREWALL_ROUTER
    assert device.ip_address == "192.168.1.1"
    assert device.mac_address == "AA:BB:CC:DD:EE:FF"
    assert device.vlan_id == "20"
    assert device.subnet == "192.168.1.0/24"
    assert device.notes == "Primary network gateway"
    assert device.x == 100.0
    assert device.y == 200.0


def test_device_tracks_field_sources():
    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
        field_sources={
            "name": "manual",
            "ip_address": "manual",
            "mac_address": "manual",
        },
    )

    assert device.field_sources["name"] == "manual"
    assert device.field_sources["ip_address"] == "manual"
    assert device.field_sources["mac_address"] == "manual"


def test_devices_receive_unique_ids():
    first = Device(
        name="Switch 1",
        device_type=DeviceType.SWITCH,
    )

    second = Device(
        name="Switch 2",
        device_type=DeviceType.SWITCH,
    )

    assert first.id
    assert second.id
    assert first.id != second.id