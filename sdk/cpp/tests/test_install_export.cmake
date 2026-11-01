# sdk/cpp/tests/test_install_export.cmake
#
# Install/export round-trip test, driven by ctest as `install_export`.
#
# Sequence:
#   1. cmake --install <build> --prefix <scratch>/prefix
#   2. configure  tests/consumer  with CMAKE_PREFIX_PATH=<prefix> only
#   3. build it
#   4. RUN it and require exit 0
#
# Step 4 is what separates "it configured" from "it works": a wrong export set or
# a missing Threads dependency shows up at link time, and a wrong install rule
# shows up as a missing header at compile time.
#
# Exit contract: 0 pass, 1 fail, 77 skip (with a named reason).

cmake_minimum_required(VERSION 3.16)

foreach(var MEM20_BUILD_DIR MEM20_CONSUMER_DIR MEM20_SCRATCH_DIR)
  if(NOT DEFINED ${var})
    message(FATAL_ERROR "test_install_export.cmake: ${var} must be provided by CMakeLists.txt")
  endif()
endforeach()

set(prefix "${MEM20_SCRATCH_DIR}/prefix")
set(consumer_build "${MEM20_SCRATCH_DIR}/consumer-build")

if(DEFINED MEM20_BUILD_TYPE AND NOT MEM20_BUILD_TYPE STREQUAL "")
  set(build_config --config "${MEM20_BUILD_TYPE}")
else()
  set(build_config "")
endif()

function(run_step label)
  execute_process(
    COMMAND ${ARGN}
    RESULT_VARIABLE rc
    OUTPUT_VARIABLE out
    ERROR_VARIABLE err)
  if(NOT rc EQUAL 0)
    message(STATUS "--- ${label} stdout ---\n${out}")
    message(STATUS "--- ${label} stderr ---\n${err}")
    message(FATAL_ERROR "install_export: ${label} failed (exit ${rc})")
  endif()
  set(LAST_OUT "${out}${err}" PARENT_SCOPE)
endfunction()

# A clean scratch prefix every run: a stale prefix could hide a missing file that
# an earlier version of the install rules happened to leave behind.
file(REMOVE_RECURSE "${MEM20_SCRATCH_DIR}")
file(MAKE_DIRECTORY "${MEM20_SCRATCH_DIR}")

# --- 1. install --------------------------------------------------------------
run_step("cmake --install"
  "${CMAKE_COMMAND}" --install "${MEM20_BUILD_DIR}" --prefix "${prefix}" ${build_config})
message(STATUS "installed into ${prefix}")

# The package config and the imported-targets file are the packaging contract;
# fail loudly rather than letting find_package produce a confusing message.
foreach(required
    "lib/cmake/mem20/mem20Config.cmake"
    "lib/cmake/mem20/mem20ConfigVersion.cmake"
    "lib/cmake/mem20/mem20Targets.cmake"
    "include/mem20/client.hpp"
    "include/mem20/surface.hpp")
  if(NOT EXISTS "${prefix}/${required}")
    message(FATAL_ERROR "install_export: expected installed file missing: ${required}")
  endif()
endforeach()

# --- 2. configure the standalone consumer -----------------------------------
# Only CMAKE_PREFIX_PATH is passed: the consumer must not learn about mem20 any
# other way than find_package.
run_step("configure consumer"
  "${CMAKE_COMMAND}"
  -S "${MEM20_CONSUMER_DIR}"
  -B "${consumer_build}"
  -G "${MEM20_GENERATOR}"
  -DCMAKE_BUILD_TYPE=${MEM20_BUILD_TYPE}
  -DCMAKE_PREFIX_PATH=${prefix}
  -DMEM20_SANITIZERS=${MEM20_SANITIZERS})
message(STATUS "${LAST_OUT}")

# --- 3. build it -------------------------------------------------------------
run_step("build consumer"
  "${CMAKE_COMMAND}" --build "${consumer_build}" ${build_config})
message(STATUS "${LAST_OUT}")

# --- 4. run it ---------------------------------------------------------------
find_program(SETARCH_CMD setarch)
set(run_prefix "")
# Same container/ASan interaction documented for the main suite: ASan needs ASLR
# off in this kernel, so run the consumer under `setarch -R` when sanitizers are on.
if(MEM20_SANITIZERS AND SETARCH_CMD)
  set(run_prefix "${SETARCH_CMD}" -R)
endif()

execute_process(
  COMMAND ${run_prefix} "${consumer_build}/mem20_consumer"
  RESULT_VARIABLE run_rc
  OUTPUT_VARIABLE run_out
  ERROR_VARIABLE run_err)
message(STATUS "${run_out}")
if(NOT run_err STREQUAL "")
  message(STATUS "${run_err}")
endif()
if(NOT run_rc EQUAL 0)
  message(FATAL_ERROR "install_export: installed consumer exited ${run_rc}")
endif()

message(STATUS "install_export: PASS -- find_package(mem20 CONFIG REQUIRED) configured, linked and ran")
