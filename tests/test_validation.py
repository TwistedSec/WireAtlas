from wireatlas.core.validation import is_valid_ip, is_valid_mac


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