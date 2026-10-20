#include "generated/active_symmetric_binary64_state.h"

volatile float command_input = 8.0f;
volatile float dt_input = 0.000125f;

int main(void)
{
    active_double_state state = {0.0, 0};
    if (active_double_init(&state, 1.25f)) return 2;
    active_double_output output = active_double_step(&state, command_input, dt_input);
    return output.status + (state.x > 1.25 ? 0 : 1);
}
