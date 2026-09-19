from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.topology_view import TopologyView
from wireatlas.models.connection import Connection, LinkType
from PySide6.QtWidgets import QGraphicsItem


def test_topology_node_shows_only_name_and_type(qapp):
    view = TopologyView()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        ip_address="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
    )

    node = view.add_device(device)

    assert node.display_text() == "Main Router\nFirewall / Router"
    assert "192.168.1.1" not in node.display_text()
    assert "AA:BB:CC:DD:EE:FF" not in node.display_text()


def test_topology_view_assigns_deterministic_positions(qapp):
    view = TopologyView()

    first = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )
    second = Device(
        name="Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(first)
    view.add_device(second)

    assert (first.x, first.y) == (40.0, 40.0)
    assert (second.x, second.y) == (230.0, 40.0)


def test_topology_view_emits_selected_device_id(qapp):
    view = TopologyView()

    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    node = view.add_device(device)

    selected_ids = []
    view.device_selected.connect(selected_ids.append)

    node.setSelected(True)
    qapp.processEvents()

    assert selected_ids == [device.id]

def test_add_device_at_saved_position_preserves_coordinates(qapp):
    view = TopologyView()
    device = Device(
        name="Loaded Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        x=515.0,
        y=225.0,
    )

    node = view.add_device_at_saved_position(device)

    assert device.x == 515.0
    assert device.y == 225.0
    assert node.pos().x() == 515.0
    assert node.pos().y() == 225.0
    assert view.node_for_device(device.id) is node


def test_clear_devices_removes_nodes_and_lookup_entries(qapp):
    view = TopologyView()
    device = Device(
        name="Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(device)
    assert view.node_for_device(device.id) is not None

    view.clear_devices()

    assert view.node_for_device(device.id) is None
    assert view.graphics_scene.items() == []

def test_add_connection_draws_labeled_edge(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        destination_interface="Gi1/0/24",
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert edge.connection_id == connection.id
    assert edge.display_text() == (
        "Trunk • igb2 ↔ Gi1/0/24"
    )

def test_connection_edge_follows_moved_device(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    source_node = view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    original_point = edge.line().p1()

    source_node.setPos(
        source_node.x() + 10,
        source_node.y() + 20,
    )

    moved_point = edge.line().p1()
    source_rect = source_node.sceneBoundingRect()

    assert moved_point != original_point

    distance_to_edge = min(
        abs(moved_point.x() - source_rect.left()),
        abs(moved_point.x() - source_rect.right()),
        abs(moved_point.y() - source_rect.top()),
        abs(moved_point.y() - source_rect.bottom()),
    )

    assert distance_to_edge < 0.001

def test_connection_label_falls_back_to_link_type(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert edge.display_text() == "Trunk"

def test_clear_devices_clears_connection_lookup(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert (
        view.edge_for_connection(connection.id)
        is edge
    )

    view.clear_devices()

    assert (
        view.edge_for_connection(connection.id)
        is None
    )

def test_connection_label_handles_single_interface(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        source_interface="igb2",
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert edge.display_text() == "Trunk • igb2"

def test_connection_edge_is_selectable(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert edge.flags() & (
        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    )

def test_connection_label_is_selectable(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    assert edge.label.flags() & (
        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    )

    assert edge.label.connection_id == connection.id

def test_selecting_connection_label_emits_connection_id(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    view.add_device(firewall)
    view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    selected = []

    view.connection_selected.connect(
        lambda connection_id: selected.append(
            connection_id
        )
    )

    edge.label.setSelected(True)

    assert selected == [connection.id]

def test_remove_connection_clears_edge(qapp):
    view = TopologyView()

    firewall = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    switch = Device(
        name="Main Switch",
        device_type=DeviceType.SWITCH,
    )

    source_node = view.add_device(firewall)
    destination_node = view.add_device(switch)

    connection = Connection(
        source_device_id=firewall.id,
        destination_device_id=switch.id,
        link_type=LinkType.TRUNK,
    )

    edge = view.add_connection(connection)

    view.remove_connection(connection.id)

    assert view.edge_for_connection(connection.id) is None
    assert edge.scene() is None
    assert edge.label.scene() is None
    assert edge not in source_node._edges
    assert edge not in destination_node._edges

def test_device_node_is_movable(qapp):
    view = TopologyView()

    device = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    node = view.add_device(device)

    assert node.flags() & (
        QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    )

def test_moving_device_node_updates_saved_position(qapp):
    view = TopologyView()

    device = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    node = view.add_device(device)

    node.setPos(300.0, 220.0)

    assert device.x == 300.0
    assert device.y == 220.0

def test_parallel_connections_are_centered_ordered_and_touch_node_edges(qapp):
    view = TopologyView()

    source = Device(
        name="Router",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    destination = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    source_node = view.add_device(source)
    destination_node = view.add_device(destination)

    first = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="wan1",
        destination_interface="wan1",
        link_type=LinkType.STANDARD_ACCESS,
    )

    second = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="wan2",
        destination_interface="wan2",
        link_type=LinkType.STANDARD_ACCESS,
    )

    third = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="wan3",
        destination_interface="wan3",
        link_type=LinkType.STANDARD_ACCESS,
    )

    first_edge = view.add_connection(first)
    second_edge = view.add_connection(second)
    third_edge = view.add_connection(third)

    source_rect = source_node.sceneBoundingRect()
    destination_rect = destination_node.sceneBoundingRect()

    center_y = source_rect.center().y()

    assert first_edge.line().y1() == center_y - 24.0
    assert second_edge.line().y1() == center_y
    assert third_edge.line().y1() == center_y + 24.0

    assert first_edge.line().x1() == source_rect.right()
    assert second_edge.line().x1() == source_rect.right()
    assert third_edge.line().x1() == source_rect.right()

    assert first_edge.line().x2() == destination_rect.left()
    assert second_edge.line().x2() == destination_rect.left()
    assert third_edge.line().x2() == destination_rect.left()

def test_parallel_connection_labels_are_distributed_in_order(qapp):
    view = TopologyView()

    source = Device(
        name="Firewall",
        device_type=DeviceType.FIREWALL_ROUTER,
    )

    destination = Device(
        name="Computer",
        device_type=DeviceType.WORKSTATION,
    )

    view.add_device(source)
    destination_node = view.add_device(destination)

    destination_node.setPos(
        40.0,
        400.0,
    )

    first = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="ig1",
        destination_interface="ig1",
        link_type=LinkType.STANDARD_ACCESS,
    )

    second = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="ig2",
        destination_interface="ig2",
        link_type=LinkType.STANDARD_ACCESS,
    )

    third = Connection(
        source_device_id=source.id,
        destination_device_id=destination.id,
        source_interface="ig3",
        destination_interface="ig3",
        link_type=LinkType.STANDARD_ACCESS,
    )

    first_edge = view.add_connection(first)
    second_edge = view.add_connection(second)
    third_edge = view.add_connection(third)

    first_y = first_edge.label.pos().y()
    second_y = second_edge.label.pos().y()
    third_y = third_edge.label.pos().y()

    assert first_y < second_y < third_y

    assert first_y != second_y
    assert second_y != third_y