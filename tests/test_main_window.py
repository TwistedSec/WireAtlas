from PySide6.QtPdf import QPdfDocument
from PySide6.QtCore import Qt, QRectF
from PySide6.QtTest import QTest
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
from wireatlas.models.connection import Connection, LinkType

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

def test_ensure_pdf_extension_appends_when_missing(qapp):
    window = MainWindow()

    result = window._ensure_pdf_extension(
        Path("Main Office Network Map")
    )

    assert result == Path("Main Office Network Map.pdf")


def test_ensure_pdf_extension_keeps_existing_extension(qapp):
    window = MainWindow()

    result = window._ensure_pdf_extension(
        Path("Main Office Network Map.pdf")
    )

    assert result == Path("Main Office Network Map.pdf")


def test_suggested_pdf_filename_uses_site_name(qapp):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    assert (
        window._suggested_pdf_filename()
        == "Main Office Network Map.pdf"
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

def test_clicking_node_populates_details_panel(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    router = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        hostname="MAIN-ROUTER",
        subnet_mask="255.255.255.0",
        vendor="Netgate",
    )

    window.add_device(router)

    window.resize(1200, 700)
    window.show()
    qapp.processEvents()

    def fail_clear():
        raise AssertionError(
            "details panel was cleared after device selection"
        )

    monkeypatch.setattr(
        window.details_panel,
        "clear",
        fail_clear,
    )

    node = window.topology_view.node_for_device(router.id)

    selected_ids = []
    window.topology_view.device_selected.connect(
        selected_ids.append
    )

    click_position = window.topology_view.mapFromScene(
        node.label.sceneBoundingRect().center()
    )

    QTest.mouseClick(
        window.topology_view.viewport(),
        Qt.MouseButton.LeftButton,
        pos=click_position,
    )
    qapp.processEvents()

    assert node.isSelected()
    assert selected_ids == [router.id]
    assert window.details_panel.name_value.text() == "Main Router"
    assert not window.details_panel.form_widget.isHidden()

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

def test_export_pdf_cancel_leaves_document_unchanged(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    dirty_before = window.document.dirty
    path_before = window.document.current_path
    dialog_args = []

    def fake_get_save_file_name(*args, **kwargs):
        dialog_args.append(args)
        return "", "PDF Files (*.pdf)"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        fake_get_save_file_name,
    )

    result = window._export_pdf()

    assert result is False
    assert window.document.dirty is dirty_before
    assert window.document.current_path == path_before

    assert dialog_args[0][1] == "Export Network Map as PDF"
    assert dialog_args[0][2] == "Main Office Network Map.pdf"
    assert dialog_args[0][3] == "PDF Files (*.pdf)"

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


def test_save_without_path_delegates_to_save_as(
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

    assert window._save() is True
    assert calls == ["save-as"]

def test_failed_save_as_preserves_existing_current_path(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()

    old_path = tmp_path / "existing.wireatlas"
    new_path = tmp_path / "replacement.wireatlas"

    window.document.mark_saved(old_path)
    window.document.mark_dirty()

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(new_path), ""),
    )

    def fail_save(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(
        main_window_module,
        "save_network_map",
        fail_save,
    )

    monkeypatch.setattr(
        window,
        "_show_save_error",
        lambda error: None,
    )

    assert window._save_as() is False
    assert window.document.current_path == old_path
    assert window.document.dirty is True

def test_open_picker_cancel_leaves_document_unchanged(
    qapp,
    monkeypatch,
):
    window = MainWindow()
    window.site_name_input.setText("Current Work")

    original_map = window.network_map
    original_path = window.document.current_path
    original_dirty = window.document.dirty

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: ("", ""),
    )

    assert window._open_document_from_dialog() is False
    assert window.network_map is original_map
    assert window.document.current_path == original_path
    assert window.document.dirty == original_dirty
    assert window.network_map.site_name == "Current Work"

def test_add_connection_action_enables_after_second_device(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    assert window.add_connection_action.isEnabled() is False

    window.add_device(firewall)

    assert window.add_connection_action.isEnabled() is False

    window.add_device(switch)

    assert window.add_connection_action.isEnabled() is True

def test_rebuild_enables_add_connection_for_two_device_map(qapp):
    window = MainWindow()

    network_map = NetworkMap(
        site_name="Office",
        devices=[
            Device(
                name="Firewall",
                device_type=DeviceType.FIREWALL_ROUTER,
            ),
            Device(
                name="Main Switch",
                device_type=DeviceType.SWITCH,
            ),
        ],
    )

    window.document.replace_map(network_map)

    window._rebuild_from_document()

    assert window.add_connection_action.isEnabled() is True

def test_add_connection_action_uses_connection_dialog(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    calls = []

    monkeypatch.setattr(
        window,
        "_open_add_connection_dialog",
        lambda: calls.append("connection"),
        raising=False,
    )

    window.add_connection_action.setEnabled(True)
    window.add_connection_action.trigger()

    assert calls == ["connection"]

def test_open_add_connection_dialog_adds_connection(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    class FakeConnectionDialog:
        def __init__(self, devices, parent=None):
            self.devices = devices

        def exec(self):
            return QDialog.DialogCode.Accepted

        def build_connection(self):
            return connection

    monkeypatch.setattr(
        main_window_module,
        "ConnectionDialog",
        FakeConnectionDialog,
        raising=False,
    )

    window._open_add_connection_dialog()

    assert window.network_map.connections == [
        connection
    ]

def test_add_connection_adds_model_and_marks_dirty(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    window.document.dirty = False

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    assert connection in window.network_map.connections
    assert window.document.dirty is True

def test_add_connection_adds_edge_to_topology(qapp, monkeypatch):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    calls = []

    monkeypatch.setattr(
        window.topology_view,
        "add_connection",
        lambda value: calls.append(value),
    )

    window.add_connection(connection)

    assert calls == [connection]

def test_rebuild_from_document_restores_connections(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    network_map = NetworkMap(
        site_name="Office",
        devices=[firewall, switch],
        connections=[connection],
    )

    window.document.replace_map(network_map)

    calls = []

    monkeypatch.setattr(
        window.topology_view,
        "add_connection",
        lambda value: calls.append(value),
    )

    window._rebuild_from_document()

    assert calls == [connection]

def test_add_connection_rejects_exact_duplicate(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    first_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    duplicate_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    window.add_connection(first_connection)
    window.add_connection(duplicate_connection)

    assert len(window.network_map.connections) == 1

def test_add_connection_rejects_reversed_duplicate(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    first_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    reversed_connection = Connection(
        source_device_id=switch.id,
        destination_device_id=firewall.id,
        source_interface="Gi1/0/24",
        destination_interface="igb2",
        link_type=LinkType.TRUNK,
    )

    window.add_connection(first_connection)
    window.add_connection(reversed_connection)

    assert len(window.network_map.connections) == 1

def test_add_connection_allows_different_interfaces(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    first_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb1",
        destination_interface="Gi1/0/1",
        link_type=LinkType.STANDARD_ACCESS,
    )

    second_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    window.add_connection(first_connection)
    window.add_connection(second_connection)

    assert len(window.network_map.connections) == 2

def test_connection_selection_enables_delete_action(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    edge = window.topology_view.edge_for_connection(
        connection.id
    )

    edge.setSelected(True)

    assert window.delete_connection_action.isEnabled()

def test_delete_connection_action_removes_selected_connection(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    edge = window.topology_view.edge_for_connection(
        connection.id
    )

    edge.setSelected(True)

    window.delete_connection_action.trigger()

    assert connection not in window.network_map.connections
    assert (
        window.topology_view.edge_for_connection(
            connection.id
        )
        is None
    )
    assert not window.delete_connection_action.isEnabled()

def test_selecting_device_disables_delete_connection(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    edge = window.topology_view.edge_for_connection(
        connection.id
    )

    firewall_node = window.topology_view.node_for_device(
        firewall.id
    )

    edge.setSelected(True)

    assert window.delete_connection_action.isEnabled()

    edge.setSelected(False)
    firewall_node.setSelected(True)

    assert not window.delete_connection_action.isEnabled()

def test_rebuild_clears_selected_connection(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    edge = window.topology_view.edge_for_connection(
        connection.id
    )

    edge.setSelected(True)

    assert window.delete_connection_action.isEnabled()

    window._rebuild_from_document()

    assert not window.delete_connection_action.isEnabled()
    assert window.selected_connection_id is None

def test_deselecting_connection_disables_delete_action(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    edge = window.topology_view.edge_for_connection(
        connection.id
    )

    edge.setSelected(True)

    assert window.delete_connection_action.isEnabled()

    edge.setSelected(False)

    assert not window.delete_connection_action.isEnabled()
    assert window.selected_connection_id is None

def test_export_pdf_appends_extension_and_preserves_document_state(
    qapp,
    monkeypatch,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    dirty_before = window.document.dirty
    path_before = window.document.current_path

    selected = tmp_path / "main-office-map"
    exported_paths = []

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (
            str(selected),
            "PDF Files (*.pdf)",
        ),
    )

    monkeypatch.setattr(
        window,
        "_write_pdf",
        lambda path: exported_paths.append(path),
        raising=False,
    )

    result = window._export_pdf()

    assert result is True
    assert exported_paths == [
        tmp_path / "main-office-map.pdf"
    ]
    assert window.document.dirty is dirty_before
    assert window.document.current_path == path_before

def test_write_pdf_creates_valid_pdf_file(
    qapp,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "test-map.pdf"

    window._write_pdf(path)

    assert path.exists()
    assert path.stat().st_size > 0
    assert path.read_bytes().startswith(b"%PDF")

def test_write_pdf_uses_letter_landscape(
    qapp,
    tmp_path,
):
    window = MainWindow()

    path = tmp_path / "letter-landscape.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    page_size = document.pagePointSize(0)

    assert round(page_size.width()) == 792
    assert round(page_size.height()) == 612

def test_add_device_enables_export_pdf(qapp):
    window = MainWindow()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(device)

    assert window.export_pdf_action.isEnabled()

def test_rebuild_enables_export_pdf_for_existing_map(qapp):
    window = MainWindow()

    network_map = NetworkMap(
        site_name="Office",
        devices=[
            Device(
                name="Firewall",
                device_type=DeviceType.FIREWALL_ROUTER,
            ),
        ],
    )

    window.document.replace_map(network_map)

    window._rebuild_from_document()

    assert window.export_pdf_action.isEnabled() is True

def test_export_pdf_action_uses_export_workflow(
    qapp,
    monkeypatch,
):
    window = MainWindow()

    calls = []

    monkeypatch.setattr(
        window,
        "_export_pdf",
        lambda: calls.append("pdf"),
        raising=False,
    )

    window.export_pdf_action.setEnabled(True)
    window.export_pdf_action.trigger()

    assert calls == ["pdf"]

def test_write_pdf_includes_site_name_header(
    qapp,
    tmp_path,
):
    window = MainWindow()
    window.site_name_input.setText("Main Office")

    path = tmp_path / "site-header.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    page_text = document.getAllText(0).text()

    assert "Main Office" in page_text

def test_write_pdf_includes_topology_device(
    qapp,
    tmp_path,
):
    window = MainWindow()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    window.add_device(device)

    path = tmp_path / "topology-device.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    page_text = document.getAllText(0).text()

    assert "Main Router" in page_text
    assert "Firewall / Router" in page_text

def test_write_pdf_includes_topology_connection(
    qapp,
    tmp_path,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="LAN1",
        destination_interface="Gi0/1",
        link_type=LinkType.TRUNK,
    )

    window.add_connection(connection)

    path = tmp_path / "topology-connection.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    page_text = document.getAllText(0).text()

    assert "Firewall" in page_text
    assert "Main Switch" in page_text
    assert "Trunk" in page_text
    assert "LAN1" in page_text
    assert "Gi0/1" in page_text

def test_topology_fit_scale_uses_smaller_dimension(qapp):
    window = MainWindow()

    scale = window._topology_fit_scale(
        source_width=1000.0,
        source_height=400.0,
        target_width=720.0,
        target_height=504.0,
    )

    assert scale == pytest.approx(0.72)


def test_topology_requires_pagination_below_readable_scale(qapp):
    window = MainWindow()

    assert (
        window._topology_fits_single_page(
            source_width=1000.0,
            source_height=400.0,
            target_width=720.0,
            target_height=504.0,
        )
        is False
    )


def test_topology_fits_single_page_at_readable_scale(qapp):
    window = MainWindow()

    assert (
        window._topology_fits_single_page(
            source_width=800.0,
            source_height=400.0,
            target_width=720.0,
            target_height=504.0,
        )
        is True
    )

def test_plan_topology_pages_keeps_readable_map_on_one_page(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    window.add_device(firewall)
    window.add_device(switch)

    pages = window._plan_topology_pages(
        target_width=720.0,
        target_height=504.0,
    )

    assert pages == [
        [firewall.id, switch.id]
    ]

def test_plan_topology_pages_repeats_common_ancestor(qapp):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )
    printer = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )

    window.add_device(firewall)
    window.add_device(switch)
    window.add_device(printer)

    window.add_connection(
        Connection(
            source_device_id=firewall.id,
            destination_device_id=switch.id,
        )
    )
    window.add_connection(
        Connection(
            source_device_id=switch.id,
            destination_device_id=printer.id,
        )
    )

    window.topology_view.node_for_device(
        firewall.id
    ).setPos(0.0, 40.0)

    window.topology_view.node_for_device(
        switch.id
    ).setPos(500.0, 40.0)

    window.topology_view.node_for_device(
        printer.id
    ).setPos(900.0, 40.0)

    pages = window._plan_topology_pages(
        target_width=720.0,
        target_height=504.0,
    )

    assert pages == [
        [firewall.id, switch.id],
        [switch.id, printer.id],
    ]

def test_write_pdf_uses_multiple_topology_pages_when_needed(
    qapp,
    tmp_path,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )
    printer = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )

    window.add_device(firewall)
    window.add_device(switch)
    window.add_device(printer)

    window.add_connection(
        Connection(
            source_device_id=firewall.id,
            destination_device_id=switch.id,
        )
    )
    window.add_connection(
        Connection(
            source_device_id=switch.id,
            destination_device_id=printer.id,
        )
    )

    window.topology_view.node_for_device(
        firewall.id
    ).setPos(0.0, 40.0)

    window.topology_view.node_for_device(
        switch.id
    ).setPos(500.0, 40.0)

    window.topology_view.node_for_device(
        printer.id
    ).setPos(900.0, 40.0)

    path = tmp_path / "multi-page-topology.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    assert document.pageCount() == 3

    reference_text = "".join(
        document.getAllText(2).text().split()
    )
    assert "DeviceReference" in reference_text

def test_write_pdf_repeats_common_ancestor_on_continuation_page(
    qapp,
    tmp_path,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )
    printer = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )

    window.add_device(firewall)
    window.add_device(switch)
    window.add_device(printer)

    window.add_connection(
        Connection(
            source_device_id=firewall.id,
            destination_device_id=switch.id,
        )
    )
    window.add_connection(
        Connection(
            source_device_id=switch.id,
            destination_device_id=printer.id,
        )
    )

    window.topology_view.node_for_device(
        firewall.id
    ).setPos(0.0, 40.0)

    window.topology_view.node_for_device(
        switch.id
    ).setPos(500.0, 40.0)

    window.topology_view.node_for_device(
        printer.id
    ).setPos(900.0, 40.0)

    path = tmp_path / "continuation.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    page_one = "".join(
        document.getAllText(0).text().split()
    )
    page_two = "".join(
        document.getAllText(1).text().split()
    )

    assert "Firewall" in page_one
    assert "MainSwitch" in page_one
    assert "Printer" not in page_one

    assert "MainSwitch" in page_two
    assert "Printer" in page_two
    assert "Firewall" not in page_two

def test_write_pdf_adds_device_reference_after_topology(
    qapp,
    tmp_path,
):
    window = MainWindow()

    device = Device(
        name="Front Desk PC",
        device_type=DeviceType.WORKSTATION,
        hostname="DESKTOP-7F3K2Q",
        ip_address="192.168.1.25",
        subnet_mask="255.255.255.0",
        subnet="192.168.1.0/24",
        vlan_id="10",
        mac_address="AA:BB:CC:DD:EE:FF",
        vendor="Dell",
    )

    window.add_device(device)

    path = tmp_path / "device-reference.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    assert document.pageCount() == 2

    reference_text = "".join(
        document.getAllText(1).text().split()
    )

    assert "DeviceReference" in reference_text
    assert "FrontDeskPC" in reference_text
    assert "DESKTOP-7F3K2Q" in reference_text
    assert "192.168.1.25" in reference_text
    assert "255.255.255.0" in reference_text
    assert "192.168.1.0/24" in reference_text
    assert "AA:BB:CC:DD:EE:FF" in reference_text
    assert "Dell" in reference_text

def test_device_reference_paginates_when_rows_do_not_fit(
    qapp,
    tmp_path,
):
    window = MainWindow()

    first_device = Device(
        name="Device 1",
        device_type=DeviceType.WORKSTATION,
    )
    window.add_device(first_device)

    for index in range(2, 26):
        window.network_map.devices.append(
            Device(
                name=f"Device {index}",
                device_type=DeviceType.WORKSTATION,
            )
        )

    path = tmp_path / "reference-pagination.pdf"
    window._write_pdf(path)

    document = QPdfDocument()
    document.load(str(path))

    assert document.pageCount() == 3

    page_two = "".join(
        document.getAllText(1).text().split()
    )
    page_three = "".join(
        document.getAllText(2).text().split()
    )

    assert "DeviceReference" in page_two
    assert "DeviceReference" in page_three
    assert "Device1" in page_two
    assert "Device25" in page_three

def test_topology_render_rect_does_not_upscale_small_map(qapp):
    window = MainWindow()

    source_rect = QRectF(
        0.0,
        0.0,
        300.0,
        150.0,
    )

    target_rect = QRectF(
        36.0,
        72.0,
        720.0,
        504.0,
    )

    render_rect = window._topology_render_rect(
        source_rect,
        target_rect,
    )

    assert render_rect.width() == pytest.approx(300.0)
    assert render_rect.height() == pytest.approx(150.0)
    assert render_rect.center() == target_rect.center()

def test_write_pdf_uses_topology_render_rect(
    qapp,
    tmp_path,
    monkeypatch,
):
    window = MainWindow()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    window.add_device(device)

    calls = []

    def fake_render_rect(source_rect, target_rect):
        calls.append((source_rect, target_rect))
        return target_rect

    monkeypatch.setattr(
        window,
        "_topology_render_rect",
        fake_render_rect,
    )

    path = tmp_path / "render-scale.pdf"
    window._write_pdf(path)

    assert len(calls) == 1

def test_write_pdf_hides_selection_during_topology_render(
    qapp,
    tmp_path,
    monkeypatch,
):
    window = MainWindow()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    window.add_device(device)

    node = window.topology_view.node_for_device(
        device.id
    )
    node.setSelected(True)

    scene = window.topology_view.graphics_scene
    selections_during_render = []

    original_render = type(scene).render

    def tracking_render(self, *args, **kwargs):
        if self is scene:
            selections_during_render.append(
                len(self.selectedItems())
            )

        return original_render(
            self,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        type(scene),
        "render",
        tracking_render,
    )

    path = tmp_path / "selection-test.pdf"
    window._write_pdf(path)

    assert selections_during_render == [0]
    assert node.isSelected() is True

def test_connection_labels_use_compact_display_names(
    qapp,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    workstation = Device(
        name="Workstation",
        device_type=DeviceType.WORKSTATION,
    )

    window.add_device(firewall)
    window.add_device(workstation)

    cases = [
        (
            LinkType.STANDARD_ACCESS,
            "Wired • Gi0 ↔ lan0",
        ),
        (
            LinkType.WIRELESS,
            "WiFi • wlan0 ↔ WiFi",
        ),
        (
            LinkType.TRUNK,
            "Trunk • Gi1 ↔ Gi24",
        ),
    ]

    for link_type, expected_text in cases:
        connection = Connection(
            source_device_id=firewall.id,
            destination_device_id=workstation.id,
            source_interface=(
                "wlan0"
                if link_type == LinkType.WIRELESS
                else "Gi1"
                if link_type == LinkType.TRUNK
                else "Gi0"
            ),
            destination_interface=(
                "WiFi"
                if link_type == LinkType.WIRELESS
                else "Gi24"
                if link_type == LinkType.TRUNK
                else "lan0"
            ),
            link_type=link_type,
        )

        window.add_connection(connection)

        edge = window.topology_view._edges[
            connection.id
        ]

        assert edge.display_text() == expected_text

def test_connection_belongs_on_topology_page(qapp):
    window = MainWindow()

    assert window._connection_belongs_on_topology_page(
        "firewall",
        "switch",
        {"firewall", "switch"},
    )

    assert not window._connection_belongs_on_topology_page(
        "switch",
        "nas",
        {"firewall", "switch"},
    )

def test_write_pdf_hides_connections_not_on_current_topology_page(
    qapp,
    tmp_path,
    monkeypatch,
):
    window = MainWindow()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )
    nas = Device(
        name="NAS",
        device_type=DeviceType.SERVER_NAS,
    )

    window.add_device(firewall)
    window.add_device(switch)
    window.add_device(nas)

    first_connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
    )

    second_connection = Connection(
        source_device_id=switch.id,
        destination_device_id=nas.id,
    )

    window.add_connection(first_connection)
    window.add_connection(second_connection)

    window.topology_view.node_for_device(
        firewall.id
    ).setPos(0.0, 40.0)

    window.topology_view.node_for_device(
        switch.id
    ).setPos(500.0, 40.0)

    window.topology_view.node_for_device(
        nas.id
    ).setPos(900.0, 40.0)

    scene = window.topology_view.graphics_scene
    visible_connections = []

    original_render = type(scene).render

    def tracking_render(self, *args, **kwargs):
        if self is scene:
            visible_connections.append(
                {
                    connection_id
                    for connection_id, edge
                    in window.topology_view._edges.items()
                    if (
                        edge.isVisible()
                        and edge.label.isVisible()
                    )
                }
            )

        return original_render(
            self,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        type(scene),
        "render",
        tracking_render,
    )

    path = tmp_path / "page-connections.pdf"
    window._write_pdf(path)

    assert visible_connections == [
        {first_connection.id},
        {second_connection.id},
    ]

    assert window.topology_view._edges[
        first_connection.id
    ].isVisible()

    assert window.topology_view._edges[
        first_connection.id
    ].label.isVisible()

    assert window.topology_view._edges[
        second_connection.id
    ].isVisible()

    assert window.topology_view._edges[
        second_connection.id
    ].label.isVisible()

def test_topology_page_plan_does_not_drop_last_device(
    qapp,
):
    window = MainWindow()

    firewall = Device(
        name="Main Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    comp1 = Device(
        name="Comp1",
        device_type=DeviceType.WORKSTATION,
    )
    comp2 = Device(
        name="Comp2",
        device_type=DeviceType.WORKSTATION,
    )
    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )
    printer = Device(
        name="Printer",
        device_type=DeviceType.PRINTER,
    )
    nas = Device(
        name="NAS",
        device_type=DeviceType.SERVER_NAS,
    )

    for device in [
        firewall,
        comp1,
        comp2,
        switch,
        printer,
        nas,
    ]:
        window.add_device(device)

    for source, destination in [
        (firewall, comp1),
        (firewall, comp2),
        (firewall, switch),
        (switch, printer),
        (switch, nas),
    ]:
        window.add_connection(
            Connection(
                source_device_id=source.id,
                destination_device_id=destination.id,
            )
        )

    positions = {
        firewall.id: (40.0, 120.0),
        comp1.id: (260.0, 20.0),
        comp2.id: (260.0, 220.0),
        switch.id: (620.0, 120.0),
        printer.id: (850.0, 20.0),
        nas.id: (1120.0, 220.0),
    }

    for device_id, position in positions.items():
        window.topology_view.node_for_device(
            device_id
        ).setPos(*position)

    pages = window._plan_topology_pages(
        target_width=720.0,
        target_height=504.0,
    )

    all_planned_devices = {
        device_id
        for page in pages
        for device_id in page
    }

    assert nas.id in all_planned_devices
    assert all_planned_devices == {
        firewall.id,
        comp1.id,
        comp2.id,
        switch.id,
        printer.id,
        nas.id,
    }

def test_export_pdf_failure_preserves_document_state(
    qapp,
    tmp_path,
    monkeypatch,
):
    window = MainWindow()

    window.document.dirty = True
    original_path = window.document.current_path

    export_path = tmp_path / "failed-export.pdf"

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (
            str(export_path),
            "PDF Files (*.pdf)",
        ),
    )

    def fail_export(path):
        raise OSError("Test export failure")

    monkeypatch.setattr(
        window,
        "_write_pdf",
        fail_export,
    )

    errors = []

    monkeypatch.setattr(
        window,
        "_show_export_error",
        lambda error: errors.append(error),
    )

    assert window._export_pdf() is False
    assert window.document.current_path == original_path
    assert window.document.dirty is True
    assert len(errors) == 1
    assert str(errors[0]) == "Test export failure"
