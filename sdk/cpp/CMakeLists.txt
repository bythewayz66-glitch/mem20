cmake_minimum_required(VERSION 3.16)
project(mem20_sdk VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(mem20_sdk
  src/client.cpp
  src/transport.cpp
  src/config.cpp
  src/child_process.hpp   # internal, not installed
)
target_include_directories(mem20_sdk
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src   # internal headers (child_process.hpp)
)

if(UNIX AND NOT APPLE)
  target_link_libraries(mem20_sdk PUBLIC pthread)
endif()

add_executable(mem20_store_recall_audit
  ${CMAKE_SOURCE_DIR}/../../docs/sdk/cpp/examples/store_recall_audit.cpp
)
target_link_libraries(mem20_store_recall_audit PRIVATE mem20_sdk)

enable_testing()
add_executable(mem20_sdk_tests tests/test_config.cpp)
target_link_libraries(mem20_sdk_tests PRIVATE mem20_sdk)
add_test(NAME mem20_sdk_tests COMMAND mem20_sdk_tests)

# --- Live surface test -------------------------------------------------------
# Exercises a REAL mem20 server over stdio: initialize handshake, tools/list
# (asserting the live tool count), then one grounded memory_store ->
# memory_recall round trip. This is the only test that proves the SDK's surface
# against a running server rather than against documentation.
#
# If no python3 is available the test exits 77 with a named reason and ctest
# reports it as SKIPPED -- never as a silent pass.
if(NOT DEFINED MEM20_REPO_ROOT)
  get_filename_component(MEM20_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
endif()

add_executable(mem20_test_live_surface tests/test_live_surface.cpp)
target_link_libraries(mem20_test_live_surface PRIVATE mem20_sdk)
target_compile_definitions(mem20_test_live_surface PRIVATE
  MEM20_TEST_SERVER_SCRIPT="${MEM20_REPO_ROOT}/mcp/mcp_server.py"
  MEM20_TEST_REPO_ROOT="${MEM20_REPO_ROOT}"
)
add_test(NAME live_surface COMMAND mem20_test_live_surface)
set_tests_properties(live_surface PROPERTIES
  SKIP_RETURN_CODE 77
  TIMEOUT 180
  LABELS "integration;live"
)

# --- Surface documentation drift guard ---------------------------------------
# The tool/domain count is stated in exactly one place in code
# (include/mem20/surface.hpp, with static_asserts on the derivation) and quoted
# in the two READMEs. This test greps all three and fails when they disagree, so
# a stale count is a red test rather than a documentation bug that ships. It
# needs no server and no python3, so it runs everywhere the suite runs.
add_executable(mem20_test_surface_docs tests/test_surface_docs.cpp)
target_link_libraries(mem20_test_surface_docs PRIVATE mem20_sdk)
target_compile_definitions(mem20_test_surface_docs PRIVATE
  MEM20_TEST_SURFACE_HEADER="${CMAKE_CURRENT_SOURCE_DIR}/include/mem20/surface.hpp"
  MEM20_TEST_SDK_README="${CMAKE_CURRENT_SOURCE_DIR}/README.md"
  MEM20_TEST_DOCS_README="${MEM20_REPO_ROOT}/docs/sdk/cpp/README.md"
)
add_test(NAME surface_docs COMMAND mem20_test_surface_docs)
set_tests_properties(surface_docs PROPERTIES
  SKIP_RETURN_CODE 77
  LABELS "unit;docs"
)
