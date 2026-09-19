from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.device_details import DeviceDetailsPanel


def test_details_panel_starts_empty(qapp):
    panel = DeviceDetailsPanel()

    assert panel.empty_label.text() == "No device selected"
    assert not panel.empty_label.isHidden()

def test_details_panel_shows_device_values(qapp):
    panel = DeviceDetailsPanel()

    device = Device(
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
    )

    panel.show()
    panel.show_device(device, is_root=True)
    qapp.processEvents()

    assert panel.name_value.text() == "Main Router"
    assert panel.type_value.text() == "Firewall / Router"
    assert panel.ip_value.text() == "192.168.1.1"
    assert panel.mac_value.text() == "AA:BB:CC:DD:EE:FF"
    assert panel.vlan_value.text() == "10"
    assert panel.subnet_value.text() == "192.168.1.0/24"
    assert panel.notes_value.toPlainText() == "Primary gateway"
    assert panel.root_value.text() == "Yes"
    assert panel.notes_value.isReadOnly()
    assert panel.hostname_value.text() == "MAIN-ROUTER"
    assert panel.subnet_mask_value.text() == "255.255.255.0"
    assert panel.vendor_value.text() == "Netgate"


def test_details_panel_uses_placeholder_for_blank_values(qapp):
    panel = DeviceDetailsPanel()

    device = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )

    panel.show_device(device)

    assert panel.ip_value.text() == "—"
    assert panel.mac_value.text() == "—"
    assert panel.vlan_value.text() == "—"
    assert panel.subnet_value.text() == "—"
    assert panel.notes_value.toPlainText() == "—"
    assert panel.hostname_value.text() == "—"
    assert panel.subnet_mask_value.text() == "—"
    assert panel.vendor_value.text() == "—"
    assert panel.root_value.text() == "No"