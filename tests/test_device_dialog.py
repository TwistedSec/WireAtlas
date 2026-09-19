from wireatlas.models.device import DeviceType
from wireatlas.ui.device_dialog import DeviceDialog


def test_device_dialog_starts_without_selected_type(qapp):
    dialog = DeviceDialog()

    assert dialog.type_combo.currentData() is None
    assert not dialog.add_button.isEnabled()


def test_device_dialog_requires_name_and_type(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")

    assert not dialog.add_button.isEnabled()

    dialog.type_combo.setCurrentIndex(1)

    assert dialog.add_button.isEnabled()


def test_device_dialog_rejects_invalid_nonblank_ip(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")
    dialog.type_combo.setCurrentIndex(1)
    dialog.ip_input.setText("192.168.1.999")

    assert not dialog.add_button.isEnabled()
    assert dialog.ip_error.text() == "Enter a valid IP address."


def test_device_dialog_rejects_invalid_nonblank_mac(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Office Printer")
    dialog.type_combo.setCurrentIndex(1)
    dialog.mac_input.setText("ZZ:12:34:56:78:90")

    assert not dialog.add_button.isEnabled()
    assert dialog.mac_error.text() == "Enter a valid MAC address."


def test_device_dialog_builds_device_with_manual_provenance(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")
    dialog.type_combo.setCurrentIndex(
        dialog.type_combo.findData(DeviceType.FIREWALL_ROUTER)
    )
    dialog.ip_input.setText("192.168.1.1")
    dialog.notes_input.setPlainText("Primary gateway")

    device = dialog.build_device()

    assert device.name == "Main Router"
    assert device.device_type == DeviceType.FIREWALL_ROUTER
    assert device.ip_address == "192.168.1.1"
    assert device.notes == "Primary gateway"

    assert device.field_sources == {
        "name": "manual",
        "device_type": "manual",
        "ip_address": "manual",
        "notes": "manual",
    }

def test_device_dialog_builds_discovery_ready_metadata(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Front Desk PC")
    dialog.type_combo.setCurrentIndex(
        dialog.type_combo.findData(DeviceType.WORKSTATION)
    )

    dialog.hostname_input.setText("DESKTOP-7F3K2Q")
    dialog.subnet_mask_input.setText("255.255.255.0")
    dialog.vendor_input.setText("Dell")

    device = dialog.build_device()

    assert device.hostname == "DESKTOP-7F3K2Q"
    assert device.subnet_mask == "255.255.255.0"
    assert device.vendor == "Dell"

    assert device.field_sources["hostname"] == "manual"
    assert device.field_sources["subnet_mask"] == "manual"
    assert device.field_sources["vendor"] == "manual"

def test_device_dialog_rejects_invalid_nonblank_subnet_mask(qapp):
    dialog = DeviceDialog()

    dialog.name_input.setText("Main Router")
    dialog.type_combo.setCurrentIndex(
        dialog.type_combo.findData(DeviceType.FIREWALL_ROUTER)
    )
    dialog.subnet_mask_input.setText("255.0.255.0")

    assert not dialog.add_button.isEnabled()
    assert (
        dialog.subnet_mask_error.text()
        == "Enter a valid subnet mask."
    )