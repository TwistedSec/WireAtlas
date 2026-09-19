from wireatlas.core.validation import (
    is_valid_ip,
    is_valid_mac,
    is_valid_subnet_mask,
    validate_network_map_data,
)

from wireatlas.models.device import Device, DeviceType
from wireatlas.models.network_map import NetworkMap

def test_blank_ip_is_valid():
    assert is_valid_ip("") is True


def test_valid_ip_is_accepted():
    assert is_valid_ip("192.168.1.10") is True


def test_invalid_ip_is_rejected():
    assert is_valid_ip("999.168.1.10") is False


def test_blank_mac_is_valid():
    assert is_valid_mac("") is True


def test_valid_mac_is_accepted():
    assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True


def test_invalid_mac_is_rejected():
    assert is_valid_mac("ZZ:BB:CC:DD:EE:FF") is False

def test_subnet_mask_validation():
    assert is_valid_subnet_mask("")
    assert is_valid_subnet_mask("255.255.255.0")
    assert is_valid_subnet_mask("255.255.0.0")
    assert not is_valid_subnet_mask("255.255.999.0")
    assert not is_valid_subnet_mask("255.0.255.0")
    assert not is_valid_subnet_mask("not-a-mask")

def test_network_map_warns_about_invalid_subnet_mask():
    device = Device(
        name="Main Router",
        device_type=DeviceType.FIREWALL_ROUTER,
        subnet_mask="255.0.255.0",
    )

    network_map = NetworkMap(
        site_name="Company X",
        devices=[device],
    )

    warnings = validate_network_map_data(network_map)

    assert (
        "Main Router: invalid subnet mask: 255.0.255.0"
        in warnings
    )