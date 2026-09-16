from PySide6.QtWidgets import QDialog

from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.main_window import MainWindow
import wireatlas.ui.main_window as main_window_module


def test_main_window_starts_with_untitled_network(qapp):
    window = MainWindow()

    assert window.network_map.site_name == "Untitled Network"
    assert window.site_name_input.text() == "Untitled Network"


def test_main_window_toolbar_enables_only_add_device(qapp):
    window = MainWindow()

    assert window.add_device_action.isEnabled()

    assert not window.new_action.isEnabled()
    assert not window.open_action.isEnabled()
    assert not window.save_action.isEnabled()
    assert not window.add_connection_action.isEnabled()
    assert not window.export_pdf_action.isEnabled()


def test_site_name_edit_updates_network_map(qapp):
    window = MainWindow()

    window.site_name_input.setText("Company X")

    assert window.network_map.site_name == "Company X"


def test_add_device_adds_model_node_and_root(qapp):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(router)

    assert window.network_map.devices == [router]
    assert window.network_map.root_device_id == router.id
    assert window.topology_view.node_for_device(router.id) is not None
    assert (router.x, router.y) == (40.0, 40.0)


def test_non_router_does_not_become_root(qapp):
    window = MainWindow()

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(switch)

    assert window.network_map.root_device_id == ""


def test_selecting_node_populates_details_panel(qapp):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
    )

    window.add_device(router)

    node = window.topology_view.node_for_device(router.id)
    node.setSelected(True)
    qapp.processEvents()

    assert window.details_panel.name_value.text() == "Main Router"
    assert window.details_panel.ip_value.text() == "192.168.1.1"
    assert window.details_panel.root_value.text() == "Yes"


def test_main_window_starts_with_map_wider_than_details(qapp):
    window = MainWindow()
    window.resize(1200, 700)
    window.show()

    qapp.processEvents()

    sizes = window.main_splitter.sizes()

    assert sizes[0] >= sizes[1] * 2

def test_add_device_action_uses_device_dialog(qapp, monkeypatch):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    class FakeDeviceDialog:
        def __init__(self, parent=None):
            pass

        def exec(self):
            return QDialog.DialogCode.Accepted

        def build_device(self):
            return router

    monkeypatch.setattr(
        main_window_module,
        "DeviceDialog",
        FakeDeviceDialog,
    )

    window.add_device_action.trigger()

    assert window.network_map.devices == [router]

def test_main_window_starts_clean_with_site_in_title(qapp):
    window = MainWindow()

    assert window.document.dirty is False
    assert window.windowTitle() == "WireAtlas — Untitled Network"


def test_site_name_change_marks_document_dirty_and_updates_title(qapp):
    window = MainWindow()

    window.site_name_input.setText("Dental Office")

    assert window.network_map.site_name == "Dental Office"
    assert window.document.dirty is True
    assert window.windowTitle() == "WireAtlas — Dental Office *"


def test_add_device_marks_document_dirty(qapp):
    window = MainWindow()
    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(device)

    assert window.document.dirty is True
    assert window.windowTitle() == "WireAtlas — Untitled Network *"

