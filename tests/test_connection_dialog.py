from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.connection_dialog import ConnectionDialog


def test_connection_dialog_lists_devices_with_ip(qapp):
    devices = [
        Device(
            name="Main Switch",
            device_type=DeviceType.SWITCH,
            ip_address="192.168.1.2",
        ),
        Device(
            name="NAS01",
            device_type=DeviceType.SERVER_NAS,
        ),
    ]

    dialog = ConnectionDialog(devices)

    assert dialog.source_combo.itemText(0) == (
        "Main Switch — 192.168.1.2"
    )
    assert dialog.source_combo.itemText(1) == "NAS01"

    assert dialog.destination_combo.itemText(0) == (
        "Main Switch — 192.168.1.2"
    )
    assert dialog.destination_combo.itemText(1) == "NAS01"

from wireatlas.models.connection import LinkType


def test_connection_dialog_shows_connection_fields(qapp):
    devices = [
        Device(
            name="Firewall",
            device_type=DeviceType.FIREWALL_ROUTER,
        ),
        Device(
            name="Main Switch",
            device_type=DeviceType.SWITCH,
        ),
    ]

    dialog = ConnectionDialog(devices)

    assert dialog.source_interface_input.text() == ""
    assert dialog.destination_interface_input.text() == ""

    assert dialog.link_type_combo.count() == 4
    assert dialog.link_type_combo.itemText(0) == (
        LinkType.STANDARD_ACCESS.value
    )
    assert dialog.link_type_combo.itemText(1) == (
        LinkType.TRUNK.value
    )
    assert dialog.link_type_combo.itemText(2) == (
        LinkType.WIRELESS.value
    )
    assert dialog.link_type_combo.itemText(3) == (
        LinkType.OTHER.value
    )

    assert dialog.notes_input.text() == ""

def test_connection_dialog_builds_connection(qapp):
    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    dialog = ConnectionDialog(
        [firewall, switch]
    )

    dialog.source_combo.setCurrentIndex(0)
    dialog.destination_combo.setCurrentIndex(1)

    dialog.source_interface_input.setText("igb2")
    dialog.destination_interface_input.setText("Gi1/0/24")

    dialog.link_type_combo.setCurrentIndex(1)
    dialog.notes_input.setText("Main trunk")

    connection = dialog.build_connection()

    assert connection.source_device_id == firewall.id
    assert connection.destination_device_id == switch.id
    assert connection.source_interface == "igb2"
    assert connection.destination_interface == "Gi1/0/24"
    assert connection.link_type == LinkType.TRUNK
    assert connection.notes == "Main trunk"

def test_connection_dialog_rejects_same_source_and_destination(qapp):
    device = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    dialog = ConnectionDialog([device])

    dialog.source_combo.setCurrentIndex(0)
    dialog.destination_combo.setCurrentIndex(0)

    assert dialog.is_valid() is False

def test_connection_dialog_add_button_requires_distinct_devices(qapp):
    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    dialog = ConnectionDialog(
        [firewall, switch]
    )

    dialog.source_combo.setCurrentIndex(0)
    dialog.destination_combo.setCurrentIndex(0)

    assert dialog.add_button.isEnabled() is False

    dialog.destination_combo.setCurrentIndex(1)

    assert dialog.add_button.isEnabled() is True