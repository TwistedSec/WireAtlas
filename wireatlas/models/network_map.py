from dataclasses import dataclass, field

from wireatlas.models.connection import Connection
from wireatlas.models.device import Device


@dataclass
class NetworkMap:
    site_name: str
    root_device_id: str = ""
    devices: list[Device] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    notes: str = ""
    format_version: str = "0.1"