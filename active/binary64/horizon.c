#include "generated/active_symmetric_binary64_state.h"
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    active_double_state state = {0.0, 0};
    if (active_double_init(&state, 1.25f)) return 2;
    uint64_t checksum = 0;
    const uint64_t steps = 117964800ULL;
    const float dt = 0.0000152587890625f;
    for (uint64_t k = 0; k < steps; ++k) {
        float command = (k & 1ULL) ? -8.0f : 8.0f;
        active_double_output out = active_double_step(&state, command, dt);
        if (out.status) return 3;
        checksum += (uint64_t)(out.slew_flag + 2);
    }
    const double elapsed = (double)steps * (double)dt;
    printf("{\"steps\":%llu,\"elapsed_s\":%.17g,\"state\":%.17g,\"checksum\":%llu}\n",
           (unsigned long long)steps, elapsed, state.x, (unsigned long long)checksum);
    return state.x == 1.25 ? 0 : 4;
}
