from wireatlas.ui.main_window import MainWindow


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