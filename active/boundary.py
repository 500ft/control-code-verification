"""Numerical admission boundary for the proposed active core, not a PX4 wrapper."""
import math
import struct


def _binary32(value):
    return struct.unpack('f', struct.pack('f', value))[0] == value


def initialize(preceding_effective_setpoint, state_limit):
    """Copy an in-domain binary32 PID setpoint without an update step."""
    value = float(preceding_effective_setpoint)
    if not math.isfinite(value) or abs(value) > state_limit or not _binary32(value):
        raise ValueError('active entry rejected: preceding setpoint outside numerical domain')
    return value


def validate_step(state, command, dt, state_limit, input_limit, dt_min, dt_max):
    """Reject values that the bare generated C must never receive."""
    values = tuple(float(v) for v in (state, command, dt))
    if not all(math.isfinite(v) and _binary32(v) for v in values):
        raise ValueError('active step rejected: non-finite or non-binary32 input')
    x, u, h = values
    if abs(x) > state_limit or abs(u) > input_limit or not dt_min <= h <= dt_max:
        raise ValueError('active step rejected: outside numerical domain')
    return values
