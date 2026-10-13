cmake_minimum_required(VERSION 3.22)
project(control_core_build_probe C)

# Build-only host analogue of PX4's common arithmetic and warning options.
# The generated numerical core is unchanged. The target-local options appear
# after the common options, so the effective command is reviewable.
add_compile_options(-O2 -fno-signed-zeros -freciprocal-math
    -Wall -Wextra -Werror -Wfloat-equal -Wno-unused-parameter)

add_library(control_core STATIC
    ../../generated/zero_reset.c
    ../../generated/tracking_reset.c)
set_target_properties(control_core PROPERTIES C_STANDARD 99 C_STANDARD_REQUIRED YES C_EXTENSIONS NO)
set_property(TARGET control_core PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
target_compile_options(control_core PRIVATE
    -fno-fast-math -fsigned-zeros -fno-reciprocal-math
    -ffp-contract=off -Wno-float-equal)
