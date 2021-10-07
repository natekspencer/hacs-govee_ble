"""Govee related enums."""
from enum import IntEnum, unique


@unique
class MusicMode(IntEnum):
    """Govee supported music modes."""

    ENERGIC = 0
    SPECTRUM = 1
    ROLLING = 2
    RHYTHM = 3

    # Handle unknown/future capabilities
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, _):
        return cls.UNKNOWN
