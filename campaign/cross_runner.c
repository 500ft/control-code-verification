/* Hexadecimal binary32 transport; independent traces retain native history.
 * Input: variant begin initial_state reference_state u dt reset (all hex).
 * Output: native state/flags, then common-reference-input state/flags.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../generated/zero_reset.h"
#include "../generated/tracking_reset.h"
static float value(unsigned bits) { float x; memcpy(&x,&bits,sizeof x); return x; }
static unsigned bits(float x) { unsigned b; memcpy(&b,&x,sizeof b); return b; }
static int step(unsigned variant, float x, float u, float dt, float reset, float out[3]) {
    float v[4]={x,u,dt,reset}; const float *args[]={v}; float *res[]={out};
    return variant ? tracking_reset(args,res,NULL,NULL,0) : zero_reset(args,res,NULL,NULL,0);
}
int main(void) {
    unsigned variant,begin,initial,reference,u,dt,reset,active=2;
    float state=0,sequence[3],common[3];
    int count;
    while ((count=scanf("%x %x %x %x %x %x %x",&variant,&begin,&initial,&reference,&u,&dt,&reset))==7) {
        if (variant>1 || begin>1 || reset>1 || (!begin && active!=variant)) return 2;
        if (begin) { state=value(initial); active=variant; }
        if (step(variant,state,value(u),value(dt),(float)reset,sequence) ||
            step(variant,value(reference),value(u),value(dt),(float)reset,common)) return 3;
        printf("%08x %08x %08x %08x %08x %08x\n",bits(sequence[0]),bits(sequence[1]),bits(sequence[2]),bits(common[0]),bits(common[1]),bits(common[2]));
        state=sequence[0];
    }
    return count==EOF ? 0 : 4;
}
