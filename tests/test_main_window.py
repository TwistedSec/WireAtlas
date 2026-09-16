from PySide6.QtWidgets import QDialog
from pathlib import Path
from PySide6.QtWidgets import QFileDialog
from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.main_window import MainWindow
import wireatlas.ui.main_window as main_window_module


def test_main_window_starts_with_untitled_network(qapp):
    window = MainWindow()

    assert window.network_map.site_name == "Untitled Network"
    assert window.site_name_input.text() == "Untitled Network"


def test_main_window_toolbar_enables_file_actions(qapp):
    window = MainWindow()

    assert window.new_action.isEnabled()
    assert window.open_action.isEnabled()
    assert window.save_action.isEnabled()
    assert window.save_as_action.isEnabled()
    assert window.add_device_action.isEnabled()
    assert not window.add_connection_action.isEnabled()
    assert not window.export_pdf_action.isEnabled()

def test_ensure_wireatlas_extension_appends_when_missing(qapp):
    window = MainWindow()

    result = window._ensure_wireatlas_extension(
        Path("office-map")
    )

    assert result == Path("office-map.wireatlas")


def test_ensure_wireatlas_extension_keeps_existing_extension(qapp):
    window = MainWindow()

    result = window._ensure_wireatlas_extension(
        Path("office-map.wireatlas")
    )

    assert result == Path("office-map.wireatlas")


def test_suggested_filename_uses_site_name(qapp):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    assert (
        window._suggested_filename()
        == "Main Office.wireatlas"
    )

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


def test_save_existing_path_saves_and_clears_dirty(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    path = tmp_path / "office.wireatlas"
    window.document.current_path = path

    calls = []

    def fake_save(network_map, save_path):
        calls.append((network_map, save_path))

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        fake_save,
    )

    assert window._save() is True
    assert calls == [(window.network_map, path)]
    assert window.document.dirty is False
    assert window.document.current_path == path


def test_save_as_appends_extension_and_adopts_path_after_success(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    selected = tmp_path / "office-map"
    saved = []

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (
            str(selected),
            "WireAtlas Network Maps (*.wireatlas)",
        ),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        lambda network_map, path: saved.append(
            (network_map, path)
        ),
    )

    assert window._save_as() is True

    expected = tmp_path / "office-map.wireatlas"
    assert saved == [(window.network_map, expected)]
    assert window.document.current_path == expected
    assert window.document.dirty is False


def test_save_as_cancel_returns_false_without_changing_state(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )

    assert window._save_as() is False
    assert window.document.current_path is None
    assert window.document.dirty is True


def test_failed_save_as_keeps_dirty_and_does_not_adopt_path(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    selected = tmp_path / "broken"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(selected), ""),
    )

    def fail_save(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        fail_save,
    )

    monkeypatch.setattr(
        window,
        "_show_save_error",
        lambda error: None,
    )

    assert window._save_as() is False
    assert window.document.current_path is None
    assert window.document.dirty is True  


def test_save_action_uses_save_workflow(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Office")

    path = tmp_path / "office.wireatlas"
    window.document.current_path = path

    saved = []

    monkeypatch.setattr(
        "wireatlas.ui.main_window.save_network_map",
        lambda network_map, save_path: saved.append(
            (network_map, save_path)
        ),
    )

    window.save_action.trigger()

    assert saved == [(window.network_map, path)]
    assert window.document.dirty is False

def test_save_as_action_uses_save_as_workflow(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    calls = []

    monkeypatch.setattr(
        window,
        "_save_as",
        lambda: calls.append("save-as") or True,
    )

    window.save_as_action.trigger()

    assert calls == ["save-as"]