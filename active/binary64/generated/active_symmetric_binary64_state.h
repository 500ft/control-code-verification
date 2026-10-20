#ifndef ACTIVE_SYMMETRIC_BINARY64_STATE_H
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
