from pathlib import Path

from wireatlas.models.network_map import NetworkMap


class MapDocument:
    def __init__(self) -> None:
        self.network_map = NetworkMap(
            site_name="Untitled Network"
        )
        self.current_path: Path | None = None
        self.dirty = False

    def mark_dirty(self) -> None:
        self.dirty = True

    def mark_saved(self, path: Path) -> None:
        self.current_path = path
        self.dirty = False

    def replace_map(
        self,
        network_map: NetworkMap,
        path: Path | None = None,
    ) -> None:
        self.network_map = network_map
        self.current_path = path
        self.dirty = False

    def new_map(self) -> None:
        self.replace_map(
            NetworkMap(site_name="Untitled Network")
        )
