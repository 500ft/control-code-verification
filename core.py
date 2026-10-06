"""Independent exact intent and explicitly rounded reference; no generator imports."""
from fractions import Fraction as Q
import math
import numpy as np


def validate(x, u, dt, reset, spec):
    d = spec['domain']
    if type(reset) is not bool:
        raise ValueError('reset must be bool')
    if not all(math.isfinite(v) for v in (x, u, dt)):
        raise ValueError('finite inputs required, including during reset')
    if abs(x) > d['state_abs_max'] or abs(u) > d['input_abs_max']:
        raise ValueError('rate outside registered domain')
    if dt != 0 and not d['dt_min_positive'] <= dt <= d['dt_max']:
        raise ValueError('dt outside registered domain')
    if any(float(np.float32(v)) != v for v in (x, u, dt)):
        raise ValueError('inputs must already be exactly binary32')


def intent(x, u, dt, reset, cfg, limit):
    """Exact backward-Euler target, then projection onto reachable rate interval."""
    x, u, dt, tau, limit = map(Q, (x, u, dt, cfg['tau'], limit))
    if reset:
        return (max(-limit, min(limit, u)) if cfg['reset_tracks_input'] else Q(0)), 0, 0
    if dt == 0:
        return x, 0, 0
    target = (tau*x + dt*u)/(tau+dt)
    lo, hi = x-Q(cfg['slew_down'])*dt, x+Q(cfg['slew_up'])*dt
    slew = -1 if target < lo else 1 if target > hi else 0
    reachable = max(lo, min(hi, target))
    sat = -1 if reachable < -limit else 1 if reachable > limit else 0
    return max(-limit, min(limit, reachable)), slew, sat


def reference(x, u, dt, reset, cfg, limit):
    f = np.float32
    x, u, dt, tau, limit = map(f, (x, u, dt, cfg['tau'], limit))
    if reset:
        return (max(-limit, min(limit, u)) if cfg['reset_tracks_input'] else f(0)), 0, 0
    if dt == 0:
        return x, 0, 0
    alpha = f(dt/f(tau+dt))
    delta = f(alpha*f(u-x))
    lo, hi = f(-f(cfg['slew_down'])*dt), f(f(cfg['slew_up'])*dt)
    slew = -1 if delta < lo else 1 if delta > hi else 0
    reached = f(x + max(lo, min(hi, delta)))
    sat = -1 if reached < -limit else 1 if reached > limit else 0
    return max(-limit, min(limit, reached)), slew, sat
