"""Emit the separately registered, stateful binary64 active core."""
from pathlib import Path

here=Path(__file__).resolve().parent
out=here/'generated'
out.mkdir(exist_ok=True)
header='''#ifndef ACTIVE_SYMMETRIC_BINARY64_STATE_H
#define ACTIVE_SYMMETRIC_BINARY64_STATE_H

typedef struct { double x; int initialized; } active_double_state;
typedef struct {
    float published;
    int slew_flag;
    int clamp_flag;
    int status; /* 0: update, 1: hold, -1: rejected */
} active_double_output;

int active_double_init(active_double_state *state, float preceding_effective);
void active_double_reset(active_double_state *state);
active_double_output active_double_step(active_double_state *state, float command, float dt);

#endif
'''
source='''#include "active_symmetric_binary64_state.h"
#include <math.h>

int active_double_init(active_double_state *state, float preceding_effective)
{
    if (!state || !isfinite(preceding_effective) || fabsf(preceding_effective) > 2.0f) return -1;
    state->x = (double)preceding_effective;
    state->initialized = 1;
    return 0;
}

void active_double_reset(active_double_state *state)
{
    if (state) { state->x = 0.0; state->initialized = 1; }
}

active_double_output active_double_step(active_double_state *state, float command, float dt)
{
    active_double_output out = {0.0f, 0, 0, -1};
    if (!state || !state->initialized || !isfinite(state->x) || fabs(state->x) > 2.0 ||
        !isfinite(command) || fabsf(command) > 8.0f || !isfinite(dt) || dt < 0.0f ||
        dt > 0.0625f || (dt > 0.0f && dt < 0.0000152587890625f)) return out;

    if (dt <= 0.0f) {
        out.published = (float)state->x;
        out.status = 1;
        return out;
    }

    const double h = (double)dt;
    const double u = (double)command;
    const double x = state->x;
    const double d = 0.25 + h;
    const double v = u - x;
    const double a = h / d;
    const double delta = a * v;
    const double lo = -2.0 * h;
    const double hi = 2.0 * h;
    out.slew_flag = delta < lo ? -1 : (delta > hi ? 1 : 0);
    const double q = delta < lo ? lo : (delta > hi ? hi : delta);
    const double r = x + q;
    out.clamp_flag = r < -2.0 ? -1 : (r > 2.0 ? 1 : 0);
    state->x = r < -2.0 ? -2.0 : (r > 2.0 ? 2.0 : r);
    out.published = (float)state->x;
    out.status = 0;
    return out;
}
'''
for name,body in [('active_symmetric_binary64_state.h',header),('active_symmetric_binary64_state.c',source)]:
    (out/name).write_text(body)
