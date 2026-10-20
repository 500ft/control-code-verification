# Include from an isolated pinned PX4 checkout's rate_control CMakeLists.txt
# for a build-only qualification of the separate strict library.
px4_add_library(ActiveDoubleProbe
    "${CMAKE_CURRENT_LIST_DIR}/generated/active_symmetric_binary64_state.c")
target_compile_options(ActiveDoubleProbe PRIVATE
    -O2 -fno-fast-math -fno-associative-math -fno-reciprocal-math
    -fsigned-zeros -ftrapping-math -ffp-contract=off -Wno-float-equal)
