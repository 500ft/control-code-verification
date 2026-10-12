/* Minimal characterization of a known bitwise discrepancy, not its repair.
 * A one-step dt=0 hold must be enough to expose it. No Python adapter is used.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../generated/zero_reset.h"
#include "../generated/tracking_reset.h"

static uint32_t bits(float x) { uint32_t u; memcpy(&u, &x, sizeof u); return u; }
int main(void) {
    float input[4]={-0.0f, 0.0f, 0.0f, 0.0f};
    float zero[3], tracking[3];
    const float *args[]={input};
    float *zero_res[]={zero}, *tracking_res[]={tracking};
    if (zero_reset(args, zero_res, NULL, NULL, 0) ||
        tracking_reset(args, tracking_res, NULL, NULL, 0)) return 2;
    printf("{\"input_state_bits\":\"%08x\",\"hold_reference_bits\":\"%08x\","
           "\"zero_reset_state_bits\":\"%08x\",\"tracking_reset_state_bits\":\"%08x\","
           "\"zero_reset_flags\":[%g,%g],\"tracking_reset_flags\":[%g,%g]}\n",
           bits(input[0]), bits(input[0]), bits(zero[0]), bits(tracking[0]),
           (double)zero[1], (double)zero[2], (double)tracking[1], (double)tracking[2]);
    /* Preserve the known discrepancy explicitly. A repair requires new review. */
    return !(bits(input[0])==0x80000000 && bits(zero[0])==0 && bits(tracking[0])==0 &&
             zero[1]==0 && zero[2]==0 && tracking[1]==0 && tracking[2]==0);
}
