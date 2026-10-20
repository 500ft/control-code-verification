"""Separate explicitly rounded binary64 reference for the new stateful core."""
import math
import struct

def f32(value): return struct.unpack('<f',struct.pack('<f',value))[0]

def initialize(preceding):
    if not math.isfinite(preceding) or abs(preceding)>2 or f32(preceding)!=preceding:
        raise ValueError('out-of-domain preceding setpoint')
    return float(preceding)

def step(x, command, dt):
    if not all(math.isfinite(y) for y in (x,command,dt)) or abs(x)>2 or abs(command)>8 or \
       f32(command)!=command or f32(dt)!=dt or dt<0 or dt>1/16 or (dt>0 and dt<1/65536):
        raise ValueError('out-of-domain active step')
    if dt<=0: return x,f32(x),0,0,1
    h=float(dt); u=float(command)
    d=0.25+h
    v=u-x
    a=h/d
    delta=a*v
    lo=-2.0*h; hi=2.0*h
    slew=-1 if delta<lo else 1 if delta>hi else 0
    q=lo if delta<lo else hi if delta>hi else delta
    reached=x+q
    clamp=-1 if reached<-2.0 else 1 if reached>2.0 else 0
    state=max(-2.0,min(2.0,reached))
    return state,f32(state),slew,clamp,0
