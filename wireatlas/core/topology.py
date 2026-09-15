from wireatlas.models.network_map import NetworkMap


def validate_topology(network_map: NetworkMap) -> list[str]:
    errors: list[str] = []

    device_ids = {device.id for device in network_map.devices}

    if (
        network_map.root_device_id
        and network_map.root_device_id not in device_ids
    ):
        errors.append(
            f"Root device does not exist: {network_map.root_device_id}"
        )

    for connection in network_map.connections:
        if connection.source_device_id not in device_ids:
            errors.append(
                "Connection references missing source device: "
                f"{connection.source_device_id}"
            )

        if connection.destination_device_id not in device_ids:
            errors.append(
                "Connection references missing destination device: "
                f"{connection.destination_device_id}"
            )

    return errors