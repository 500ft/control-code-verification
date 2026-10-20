cmake_minimum_required(VERSION 3.20)
project(active_symmetric_binary64_state C)
add_library(active_symmetric_binary64_state STATIC generated/active_symmetric_binary64_state.c)
target_compile_features(active_symmetric_binary64_state PRIVATE c_std_99)
# Strict option A is local to this library. PX4 target flags must be inspected separately.
target_compile_options(active_symmetric_binary64_state PRIVATE
  -O2 -fno-fast-math -fno-associative-math -fno-reciprocal-math
  -fsigned-zeros -ftrapping-math -ffp-contract=off
  -Wall -Wextra -Werror -Wno-float-equal)
