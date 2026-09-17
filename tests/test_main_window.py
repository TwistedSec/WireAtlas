from PySide6.QtGui import QCloseEvent
import pytest
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QDialog
from pathlib import Path
from PySide6.QtWidgets import QFileDialog
from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.main_window import MainWindow
import wireatlas.ui.main_window as main_window_module
from wireatlas.models.network_map import NetworkMap
from wireatlas.core.storage import WireAtlasFileError

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


def test_rebuild_from_document_restores_nodes_and_clears_details(
    qapp,
    tmp_path,
):
    window = MainWindow()

    device = Device(
        name="Loaded Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=420.0,
        y=180.0,
    )

    network_map = NetworkMap(
        site_name="Loaded Site",
        root_device_id=device.id,
        devices=[device],
    )

    window.document.replace_map(
        network_map,
        tmp_path / "loaded.wireatlas",
    )

    window._rebuild_from_document()

    node = window.topology_view.node_for_device(device.id)

    assert window.site_name_input.text() == "Loaded Site"
    assert node is not None
    assert node.pos().x() == 420.0
    assert node.pos().y() == 180.0
    assert window.network_map.root_device_id == device.id
    assert window.details_panel.form_widget.isHidden()
    assert window.document.dirty is False

def test_new_document_resets_clean_map_and_gui(qapp):
    window = MainWindow()

    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(device)
    window.site_name_input.setText("Old Site")

    window._new_document()

    assert window.network_map.site_name == "Untitled Network"
    assert window.network_map.devices == []
    assert window.document.current_path is None
    assert window.document.dirty is False
    assert window.site_name_input.text() == "Untitled Network"
    assert window.topology_view.graphics_scene.items() == []
    assert window.windowTitle() == "WireAtlas — Untitled Network"

def test_open_valid_map_replaces_document_and_rebuilds_gui(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "loaded.wireatlas"

    device = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=300.0,
        y=140.0,
    )

    loaded = NetworkMap(
        site_name="Loaded Office",
        root_device_id=device.id,
        devices=[device],
    )

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: [],
    )

    assert window._open_document_from_dialog() is True

    assert window.network_map is loaded
    assert window.document.current_path == path
    assert window.document.dirty is False
    assert window.site_name_input.text() == "Loaded Office"

    node = window.topology_view.node_for_device(device.id)

    assert node is not None
    assert node.pos().x() == 300.0
    assert node.pos().y() == 140.0

def test_open_warning_cancel_leaves_current_document_untouched(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    original_map = window.network_map
    original_dirty = window.document.dirty

    path = tmp_path / "warning.wireatlas"
    loaded = NetworkMap(site_name="Warning Site")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: ["Bad IP"],
    )

    monkeypatch.setattr(
        window,
        "_confirm_open_warnings",
        lambda warnings: False,
    )

    assert window._open_document_from_dialog() is False

    assert window.network_map is original_map
    assert window.network_map.site_name == "Current Work"
    assert window.document.dirty is original_dirty

def test_confirm_open_warnings_accepts_open_anyway(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    class FakeMessageBox:
        class Icon:
            Warning = object()

        class ButtonRole:
            AcceptRole = object()
            RejectRole = object()

        def __init__(self, parent=None):
            self.informative_text = ""
            self.buttons = []
            self.clicked = None

        def setIcon(self, icon):
            pass

        def setWindowTitle(self, title):
            pass

        def setText(self, text):
            pass

        def setInformativeText(self, text):
            self.informative_text = text

        def addButton(self, text, role):
            button = object()
            self.buttons.append((text, role, button))

            if text == "Open Anyway":
                self.clicked = button

            return button

        def exec(self):
            pass

        def clickedButton(self):
            return self.clicked

    monkeypatch.setattr(
        "wireatlas.ui.main_window.QMessageBox",
        FakeMessageBox,
    )
    assert window._confirm_open_warnings(
        ["Bad IP", "Bad MAC"]
    ) is True

def test_open_warning_accept_replaces_document(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "warning.wireatlas"
    loaded = NetworkMap(site_name="Warning Site")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: ["Bad IP"],
    )

    monkeypatch.setattr(
        window,
        "_confirm_open_warnings",
        lambda warnings: True,
    )

    assert window._open_document_from_dialog() is True
    assert window.network_map is loaded
    assert window.document.current_path == path
    assert window.document.dirty is False

def test_open_error_leaves_current_document_untouched(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    original_map = window.network_map
    original_path = window.document.current_path
    original_dirty = window.document.dirty

    path = tmp_path / "broken.wireatlas"

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    def fail_load(selected_path):
        raise WireAtlasFileError(
            "File is not valid WireAtlas data"
        )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        fail_load,
    )

    monkeypatch.setattr(
        window,
        "_show_open_error",
        lambda error: None,
        raising=False,
    )

    assert window._open_document_from_dialog() is False

    assert window.network_map is original_map
    assert window.document.current_path is original_path
    assert window.document.dirty is original_dirty
    assert window.site_name_input.text() == "Current Work"

def test_open_action_uses_open_workflow(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "loaded.wireatlas"
    loaded = NetworkMap(site_name="Loaded Office")

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(path), ""),
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.load_network_map",
        lambda selected_path: loaded,
    )

    monkeypatch.setattr(
        "wireatlas.ui.main_window.validate_network_map_data",
        lambda network_map: [],
    )

    window.open_action.trigger()

    assert window.network_map is loaded
    assert window.document.current_path == path
    assert window.document.dirty is False

def test_confirm_discard_or_save_allows_clean_document(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: pytest.fail(
            "clean document should not prompt"
        ),
    )

    assert window._confirm_discard_or_save() is True

def test_unsaved_cancel_blocks_action(qapp, monkeypatch):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Cancel,
    )

    assert window._confirm_discard_or_save() is False


def test_unsaved_discard_allows_action(qapp, monkeypatch):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Discard,
    )

    assert window._confirm_discard_or_save() is True


def test_unsaved_save_allows_action_only_after_success(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Save,
    )

    monkeypatch.setattr(
        window,
        "_save",
        lambda: True,
    )

    assert window._confirm_discard_or_save() is True


def test_unsaved_save_failure_blocks_action(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_ask_unsaved_changes",
        lambda: QMessageBox.StandardButton.Save,
    )

    monkeypatch.setattr(
        window,
        "_save",
        lambda: False,
    )

    assert window._confirm_discard_or_save() is False

def test_dirty_new_cancel_keeps_current_document(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    original_map = window.network_map

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )

    window._request_new_document()

    assert window.network_map is original_map
    assert window.network_map.site_name == "Current Work"


def test_dirty_new_proceeds_after_confirmation(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: True,
    )

    window._request_new_document()

    assert window.network_map.site_name == "Untitled Network"
    assert window.document.dirty is False

def test_new_action_uses_guarded_new_workflow(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    calls = []

    monkeypatch.setattr(
        window,
        "_request_new_document",
        lambda: calls.append("new"),
    )

    window.new_action.trigger()

    assert calls == ["new"]

def test_dirty_open_cancel_does_not_open_dialog(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.document.mark_dirty()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )

    monkeypatch.setattr(
        window,
        "_open_document_from_dialog",
        lambda: pytest.fail(
            "open dialog should not run"
        ),
    )

    assert window._request_open_document() is False

def test_open_action_uses_guarded_open_workflow(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    calls = []

    monkeypatch.setattr(
        window,
        "_request_open_document",
        lambda: calls.append("open"),
    )

    window.open_action.trigger()

    assert calls == ["open"]

def test_close_event_ignores_close_when_unsaved_action_cancelled(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: False,
    )

    event = QCloseEvent()

    window.closeEvent(event)

    assert event.isAccepted() is False

def test_close_event_accepts_close_after_confirmation(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    monkeypatch.setattr(
        window,
        "_confirm_discard_or_save",
        lambda: True,
    )

    event = QCloseEvent()

    window.closeEvent(event)

    assert event.isAccepted() is True