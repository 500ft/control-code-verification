/* Development reproducer for the pinned MAVLink-to-uORB rate mapping.
 * Mirrors the yaw assignment in mavlink_receiver.cpp:1922-1927. */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { BODY_YAW_RATE_IGNORE = 4 };

typedef struct {
    uint64_t timestamp;
    float roll, pitch, yaw, thrust_body[3];
    uint8_t reset_integral;
} rates_message;

static rates_message map(uint8_t mask, float supplied_yaw)
{
    rates_message out = {0};
    out.timestamp = 123456;
    out.roll = 0.25f;
    out.pitch = -0.5f;
    out.yaw = (mask & BODY_YAW_RATE_IGNORE) ? (float)NAN : supplied_yaw;
    out.thrust_body[2] = -0.4f;
    return out;
}

int main(void)
{
    const rates_message ignored = map(BODY_YAW_RATE_IGNORE, 0.75f);
    const rates_message malformed = map(0, (float)NAN);
    uint32_t ignored_bits = 0, malformed_bits = 0;
    memcpy(&ignored_bits, &ignored.yaw, sizeof ignored_bits);
    memcpy(&malformed_bits, &malformed.yaw, sizeof malformed_bits);
    if (!isnan(ignored.yaw) || !isnan(malformed.yaw) ||
        memcmp(&ignored, &malformed, sizeof ignored) != 0) return 1;
    printf("{\"ignored_yaw_bits\":\"%08x\",\"unmasked_nan_yaw_bits\":\"%08x\",\"messages_identical\":true}\n",
           ignored_bits, malformed_bits);
    return 0;
}
