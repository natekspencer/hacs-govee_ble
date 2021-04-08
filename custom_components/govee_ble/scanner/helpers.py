"""Govee BLE Helpers."""
from typing import Optional


def decode_temps(packet_value: int) -> float:
    """Decode potential negative temperatures."""
    # https://github.com/Thrilleratplay/GoveeWatcher/issues/2

    if packet_value & 0x800000:
        return float((packet_value ^ 0x800000) / -10000)
    return float(packet_value / 10000)


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
