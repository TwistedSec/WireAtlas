import ipaddress
import re
from wireatlas.models.network_map import NetworkMap
from wireatlas.core.topology import validate_topology

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

def validate_network_map_data(network_map: NetworkMap) -> list[str]:
    warnings: list[str] = []

    for device in network_map.devices:
        if not is_valid_ip(device.ip_address):
            warnings.append(
                f"{device.name}: invalid IP address: {device.ip_address}"
            )

        if not is_valid_mac(device.mac_address):
            warnings.append(
                f"{device.name}: invalid MAC address: {device.mac_address}"
            )

    warnings.extend(validate_topology(network_map))

    return warnings
