from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class LinkType(Enum):
    STANDARD_ACCESS = "Standard / Access"
    TRUNK = "Trunk"
    WIRELESS = "Wireless"
    OTHER = "Other"


@dataclass
class Connection:
    source_device_id: str
    destination_device_id: str
    source_interface: str = ""
    destination_interface: str = ""
    link_type: LinkType = LinkType.STANDARD_ACCESS
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))