cmake_minimum_required(VERSION 3.22)
project(active_symmetric_build_probe C)

# Host analogue of pinned PX4 common options. This is a separate library target.
add_compile_options(-O2 -fno-signed-zeros -freciprocal-math
    -Wall -Wextra -Werror -Wfloat-equal -Wno-unused-parameter)
add_library(active_symmetric_core STATIC generated/active_symmetric.c)
set_target_properties(active_symmetric_core PROPERTIES
    C_STANDARD 99 C_STANDARD_REQUIRED YES C_EXTENSIONS NO
    INTERPROCEDURAL_OPTIMIZATION TRUE)
target_compile_options(active_symmetric_core PRIVATE
    -fno-fast-math -fsigned-zeros -fno-reciprocal-math
    -ffp-contract=off -Wno-float-equal)
