from wireatlas.core.document import MapDocument
from wireatlas.models.network_map import NetworkMap


def test_document_starts_with_untitled_clean_map():
    document = MapDocument()

    assert document.network_map.site_name == "Untitled Network"
    assert document.current_path is None
    assert document.dirty is False


def test_mark_dirty_sets_dirty_state():
    document = MapDocument()

    document.mark_dirty()

    assert document.dirty is True


def test_mark_saved_records_path_and_clears_dirty(tmp_path):
    document = MapDocument()
    document.mark_dirty()

    path = tmp_path / "office.wireatlas"
    document.mark_saved(path)

    assert document.current_path == path
    assert document.dirty is False


def test_replace_map_replaces_map_path_and_clears_dirty(tmp_path):
    document = MapDocument()
    document.mark_dirty()

    network_map = NetworkMap(site_name="Loaded Site")
    path = tmp_path / "loaded.wireatlas"

    document.replace_map(network_map, path)

    assert document.network_map is network_map
    assert document.current_path == path
    assert document.dirty is False


def test_new_map_resets_to_clean_untitled_document(tmp_path):
    document = MapDocument()
    document.network_map.site_name = "Old Site"
    document.current_path = tmp_path / "old.wireatlas"
    document.mark_dirty()

    document.new_map()

    assert document.network_map.site_name == "Untitled Network"
    assert document.current_path is None
    assert document.dirty is False
