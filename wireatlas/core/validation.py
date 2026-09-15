import ipaddress
import re


def is_valid_ip(value: str) -> bool:
    if value == "":
        return True

    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_mac(value: str) -> bool:
    if value == "":
        return True

    pattern = r"^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
    return re.fullmatch(pattern, value) is not None