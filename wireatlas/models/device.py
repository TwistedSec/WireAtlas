from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class DeviceType(Enum):
    FIREWALL_ROUTER = "Firewall / Router"
    SWITCH = "Switch"
    ACCESS_POINT = "Access Point"
    SERVER_NAS = "Server / NAS"
    WORKSTATION = "Workstation"
    PRINTER = "Printer"
    IOT = "IoT Device"
    OTHER = "Other"


@dataclass
class Device:
    name: str
    device_type: DeviceType
    ip_address: str = ""
    mac_address: str = ""
    vlan_id: str = ""
    subnet: str = ""
    notes: str = ""
    x: float = 0.0
    y: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))