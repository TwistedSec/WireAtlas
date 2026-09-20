import math
from PySide6.QtCore import QPointF, Signal
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QGraphicsLineItem,
)

from wireatlas.models.device import Device
from wireatlas.models.connection import Connection, LinkType

NODE_WIDTH = 160.0
NODE_HEIGHT = 70.0

START_X = 40.0
START_Y = 40.0

X_SPACING = 190.0
Y_SPACING = 110.0

CONNECTION_SPACING = 24.0

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
        self.device = device
        self._edges = []

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
            True,
        )

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
            True,
        )

        self.label = QGraphicsTextItem(
            f"{device.name}\n{device.device_type.value}",
            self,
        )

        self.label.setPos(8.0, 8.0)

    def display_text(self) -> str:
        return self.label.toPlainText()

    def add_edge(self, edge) -> None:
        self._edges.append(edge)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)

        if (
            change
            == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
        ):
            self.device.x = value.x()
            self.device.y = value.y()

            for edge in self._edges:
                edge.update_position()

        return result

class ConnectionEdge(QGraphicsLineItem):
    def __init__(
        self,
        connection: Connection,
        source_node: DeviceNode,
        destination_node: DeviceNode,
    ):
        source_x = (
            source_node.scenePos().x()
            + NODE_WIDTH / 2
        )
        source_y = (
            source_node.scenePos().y()
            + NODE_HEIGHT / 2
        )

        destination_x = (
            destination_node.scenePos().x()
            + NODE_WIDTH / 2
        )
        destination_y = (
            destination_node.scenePos().y()
            + NODE_HEIGHT / 2
        )

        super().__init__(
            source_x,
            source_y,
            destination_x,
            destination_y,
        )

        self.connection_id = connection.id
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )
        self.bundle_offset = 0.0
        self.label_fraction = 0.5
        self.source_node = source_node
        self.destination_node = destination_node

        source_node.add_edge(self)
        destination_node.add_edge(self)

        display_names = {
            LinkType.STANDARD_ACCESS: "Wired",
            LinkType.WIRELESS: "WiFi",
            LinkType.TRUNK: "Trunk",
            LinkType.OTHER: "Other",
        }

        label_text = display_names[
            connection.link_type
        ]

        if (
            connection.source_interface
            and connection.destination_interface
        ):
            label_text = (
                f"{label_text} • "
                f"{connection.source_interface} ↔ "
                f"{connection.destination_interface}"
            )
        elif connection.source_interface:
            label_text = (
                f"{label_text} • "
                f"{connection.source_interface}"
            )
        elif connection.destination_interface:
            label_text = (
                f"{label_text} • "
                f"{connection.destination_interface}"
            )

        self.label = QGraphicsTextItem(
            label_text
        )

        self.label.connection_id = connection.id

        self.label.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

        midpoint_x = (
            source_x + destination_x
        ) / 2

        midpoint_y = (
            source_y + destination_y
        ) / 2

        self.label.setPos(
            midpoint_x,
            midpoint_y,
        )

    def display_text(self) -> str:
        return self.label.toPlainText()

    def update_position(self) -> None:
        source_rect = (
            self.source_node.sceneBoundingRect()
        )

        destination_rect = (
            self.destination_node.sceneBoundingRect()
        )

        source_center = source_rect.center()
        destination_center = destination_rect.center()

        dx = (
            destination_center.x()
            - source_center.x()
        )

        dy = (
            destination_center.y()
            - source_center.y()
        )

        length = math.hypot(dx, dy)

        if length == 0:
            return

        direction_x = dx / length
        direction_y = dy / length

        perpendicular_x = -direction_y
        perpendicular_y = direction_x

        source_anchor = QPointF(
            source_center.x()
            + perpendicular_x
            * self.bundle_offset,
            source_center.y()
            + perpendicular_y
            * self.bundle_offset,
        )

        destination_anchor = QPointF(
            destination_center.x()
            + perpendicular_x
            * self.bundle_offset,
            destination_center.y()
            + perpendicular_y
            * self.bundle_offset,
        )

        source_point = self._rect_exit_point(
            source_rect,
            source_anchor,
            direction_x,
            direction_y,
        )

        destination_point = self._rect_exit_point(
            destination_rect,
            destination_anchor,
            -direction_x,
            -direction_y,
        )

        self.setLine(
            source_point.x(),
            source_point.y(),
            destination_point.x(),
            destination_point.y(),
        )

        label_x = (
            source_point.x()
            + (
                destination_point.x()
                - source_point.x()
            )
            * self.label_fraction
        )

        label_y = (
            source_point.y()
            + (
                destination_point.y()
                - source_point.y()
            )
            * self.label_fraction
        )

        self.label.setPos(
            label_x,
            label_y,
        )
    def set_bundle_offset(
        self,
        offset: float,
    ) -> None:
        self.bundle_offset = offset
        self.update_position()

    def set_label_fraction(
        self,
        fraction: float,
    ) -> None:
        self.label_fraction = fraction
        self.update_position()

    @staticmethod
    def _rect_exit_point(
        rect,
        point: QPointF,
        direction_x: float,
        direction_y: float,
    ) -> QPointF:
        distances = []

        if direction_x > 0:
            distances.append(
                (rect.right() - point.x())
                / direction_x
            )
        elif direction_x < 0:
            distances.append(
                (rect.left() - point.x())
                / direction_x
            )

        if direction_y > 0:
            distances.append(
                (rect.bottom() - point.y())
                / direction_y
            )
        elif direction_y < 0:
            distances.append(
                (rect.top() - point.y())
                / direction_y
            )

        positive_distances = [
            distance
            for distance in distances
            if distance >= 0
        ]

        distance = min(positive_distances)

        return QPointF(
            point.x()
            + direction_x * distance,
            point.y()
            + direction_y * distance,
        )

class TopologyView(QGraphicsView):
    device_selected = Signal(str)
    connection_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphics_scene = QGraphicsScene(self)
        self.setScene(self.graphics_scene)

        self.graphics_scene.selectionChanged.connect(
            self._emit_selected_connection
        )

        self._nodes: dict[str, DeviceNode] = {}

        self._edges: dict[str, ConnectionEdge] = {}

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

    def add_connection(
        self,
        connection: Connection,
    ) -> ConnectionEdge:
        source_node = self._nodes[
            connection.source_device_id
        ]

        destination_node = self._nodes[
            connection.destination_device_id
        ]

        edge = ConnectionEdge(
            connection,
            source_node,
            destination_node,
        )

        self.graphics_scene.addItem(edge)
        self.graphics_scene.addItem(edge.label)

        self._edges[connection.id] = edge

        self._recalculate_connection_bundle(
            connection.source_device_id,
            connection.destination_device_id,
        )

        return edge

    def _recalculate_connection_bundle(
        self,
        source_device_id: str,
        destination_device_id: str,
    ) -> None:
        edges = [
            edge
            for edge in self._edges.values()
            if {
                edge.source_node.device_id,
                edge.destination_node.device_id,
            }
            == {
                source_device_id,
                destination_device_id,
            }
        ]

        if not edges:
            return

        start_offset = (
            -(
                len(edges) - 1
            )
            * CONNECTION_SPACING
            / 2
        )

        reference_source = (
            edges[0].source_node.device_id
        )

        for index, edge in enumerate(edges):
            offset = (
                start_offset
                + index * CONNECTION_SPACING
            )

            label_fraction = (
                index + 1
            ) / (
                len(edges) + 1
            )

            if (
                edge.source_node.device_id
                != reference_source
            ):
                offset = -offset
                label_fraction = (
                    1.0 - label_fraction
                )

            edge.set_bundle_offset(
                offset
            )

            edge.set_label_fraction(
                label_fraction
            )

    def remove_connection(
        self,
        connection_id: str,
    ) -> None:
        edge = self._edges.pop(
            connection_id,
            None,
        )

        if edge is None:
            return

        source_device_id = (
            edge.source_node.device_id
        )

        destination_device_id = (
            edge.destination_node.device_id
        )

        if edge in edge.source_node._edges:
            edge.source_node._edges.remove(edge)

        if edge in edge.destination_node._edges:
            edge.destination_node._edges.remove(edge)

        if edge.label.scene() is not None:
            self.graphics_scene.removeItem(
                edge.label
            )

        if edge.scene() is not None:
            self.graphics_scene.removeItem(
                edge
            )

        if edge.scene() is not None:
            self.graphics_scene.removeItem(
                edge
            )

    def clear_devices(self) -> None:
        self.graphics_scene.clear()
        self._nodes.clear()
        self._edges.clear()

    def node_for_device(
        self,
        device_id: str,
    ) -> DeviceNode | None:
        return self._nodes.get(device_id)

    def edge_for_connection(
        self,
        connection_id: str,
    ) -> ConnectionEdge | None:
        return self._edges.get(connection_id)

    def _emit_selected_device(self) -> None:
        for item in self.graphics_scene.selectedItems():
            if isinstance(item, DeviceNode):
                self.device_selected.emit(
                    item.device_id
                )
                return

    def _emit_selected_connection(self) -> None:
        for item in self.graphics_scene.selectedItems():
            connection_id = getattr(
                item,
                "connection_id",
                None,
            )

            if connection_id:
                self.connection_selected.emit(
                    connection_id
                )
                return

        self.connection_selected.emit("")