"""Govee BLE Helpers."""
from __future__ import annotations

from typing import Optional


def decode_temperature_and_humidity(data_packet: bytes) -> tuple[float, float]:
    # Adapted from: https://github.com/Thrilleratplay/GoveeWatcher/issues/2
    packet_value = int(data_packet.hex(), 16)
    multiplier = 1
    if packet_value & 0x800000:
        packet_value = packet_value ^ 0x800000
        multiplier = -1
    return float(packet_value / 10000 * multiplier), float(packet_value % 1000 / 10)


def twos_complement(n: int, w: int = 16) -> int:
    """Two's complement integer conversion."""
    # Adapted from: https://stackoverflow.com/a/33716541.
    if n & (1 << (w - 1)):
        n = n - (1 << w)
    return n


#
# Reverse MAC octet order, return as a string
#
def reverse_mac(rmac: bytes) -> Optional[str]:
    """Change Little Endian order to Big Endian."""
    if len(rmac) != 6:
        return None
    macarr = [format(c, "02x") for c in list(reversed(rmac))]
    return (":".join(macarr)).upper()
