import os

from . import config

ENV_VAR = 'SLOT_LANE_PINS'


def lane_pins():
    """GPIO pin per lane: the SLOT_LANE_PINS env override, else config.LANE_PINS."""
    raw = os.environ.get(ENV_VAR)
    if not raw:
        return list(config.LANE_PINS)
    pins = [int(p) for p in raw.split(',') if p.strip()]
    if not pins or len(set(pins)) != len(pins):
        raise ValueError(f'{ENV_VAR} needs unique, comma separated pin numbers')
    return pins
