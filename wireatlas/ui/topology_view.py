from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from wireatlas.models.device import Device


NODE_WIDTH = 160.0
NODE_HEIGHT = 70.0

START_X = 40.0
START_Y = 40.0

X_SPACING = 190.0
Y_SPACING = 110.0

COLUMNS = 4


class DeviceNode(QGraphicsRectItem):
    def __init__(self, device: Device):
        super().__init__(
            0.0,
            0.0,
            NODE_WIDTH,
            NODE_HEIGHT,
        )

        self.device_id = device.id

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.label = QGraphicsTextItem(
            f"{device.name}\n{device.device_type.value}",
            self,
        )

        self.label.setPos(8.0, 8.0)

    def display_text(self) -> str:
        return self.label.toPlainText()


class TopologyView(QGraphicsView):
    device_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)

        self._nodes: dict[str, DeviceNode] = {}

        self.graphics_scene.selectionChanged.connect(
            self._emit_selected_device
        )

    @staticmethod
    def position_for_index(
        index: int,
    ) -> tuple[float, float]:
        column = index % COLUMNS
        row = index // COLUMNS

        x = START_X + column * X_SPACING
        y = START_Y + row * Y_SPACING

        return x, y

    def add_device(
        self,
        device: Device,
    ) -> DeviceNode:
        x, y = self.position_for_index(
            len(self._nodes)
        )

        device.x = x
        device.y = y

        node = DeviceNode(device)
        node.setPos(x, y)

        self.graphics_scene.addItem(node)
        self._nodes[device.id] = node

        return node

    def add_device_at_saved_position(
        self,
        device: Device,
    ) -> DeviceNode:
        node = DeviceNode(device)
        node.setPos(device.x, device.y)

        self.graphics_scene.addItem(node)
        self._nodes[device.id] = node

        return node

    def clear_devices(self) -> None:
        self.graphics_scene.clear()
        self._nodes.clear()

    def node_for_device(
        self,
        device_id: str,
    ) -> DeviceNode | None:
        return self._nodes.get(device_id)

    def _emit_selected_device(self) -> None:
        for item in self.graphics_scene.selectedItems():
            if isinstance(item, DeviceNode):
                self.device_selected.emit(
                    item.device_id
                )
                return
