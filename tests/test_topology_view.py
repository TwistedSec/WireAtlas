from wireatlas.models.device import Device, DeviceType
from wireatlas.ui.topology_view import TopologyView


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