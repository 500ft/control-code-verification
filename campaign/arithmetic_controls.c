#include <fenv.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t bits(float x) { uint32_t u; memcpy(&u, &x, sizeof u); return u; }
int main(void) {
    volatile float one=1.0f, half_ulp=0x1p-24f, minimum_normal=0x1p-126f;
    volatile float a=0x1.000002p0f, b=0x1.fffffcp-1f, minus_one=-1.0f;
    float tie=one+half_ulp, subnormal=minimum_normal*0.5f;
    float contraction=a*b+minus_one;
    unsigned long long fpcr=0;
#if defined(__aarch64__)
    __asm__ volatile("mrs %0, fpcr" : "=r"(fpcr));
#endif
    printf("{\"tie_bits\":\"%08x\",\"subnormal_bits\":\"%08x\","
           "\"contraction_bits\":\"%08x\",\"fpcr\":%llu,\"round_nearest\":%s}\n",
           bits(tie), bits(subnormal), bits(contraction), fpcr,
           fegetround()==FE_TONEAREST ? "true" : "false");
    return !(bits(tie)==0x3f800000 && bits(subnormal)==0x00400000 &&
             bits(contraction)==0 && fegetround()==FE_TONEAREST && !(fpcr & (1ULL<<24)));
}
