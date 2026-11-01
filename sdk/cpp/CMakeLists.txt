# sdk/cpp/CMakeLists.txt -- mem20 C++ SDK
#
# Build, test and INSTALL the native mem20 client library.
#
# Consumer contract (after `cmake --install`):
#
#     find_package(mem20 CONFIG REQUIRED)
#     target_link_libraries(app PRIVATE mem20::mem20)
#
# The same `mem20::mem20` target is available in the build tree, so an embedding
# project can also just do `add_subdirectory(sdk/cpp)` (or FetchContent) and link
# the identical name with no `find_package` at all.
#
# Options
#   MEM20_BUILD_TESTS        ON when top-level; OFF when embedded by default
#   MEM20_BUILD_EXAMPLES     build docs/sdk/cpp/examples when present
#   MEM20_WARNINGS_AS_ERRORS promote the SDK's warning set to -Werror
#   MEM20_ENABLE_SANITIZERS  ASan + UBSan on the library, tests and examples
#   MEM20_CXX_STANDARD       17 (default) or 20

cmake_minimum_required(VERSION 3.16)

project(mem20_sdk
  VERSION 0.1.0
  DESCRIPTION "Native C++17 client for the mem20 MCP server"
  HOMEPAGE_URL "https://github.com/bythewayz66-glitch/mem20"
  LANGUAGES CXX)

# --- options ----------------------------------------------------------------
if(PROJECT_IS_TOP_LEVEL)
  set(MEM20_IS_TOP_LEVEL ON)
else()
  set(MEM20_IS_TOP_LEVEL OFF)
endif()

option(MEM20_BUILD_TESTS "Build the mem20 SDK test suite" ${MEM20_IS_TOP_LEVEL})
option(MEM20_BUILD_EXAMPLES "Build the mem20 SDK examples" ${MEM20_IS_TOP_LEVEL})
option(MEM20_WARNINGS_AS_ERRORS "Treat SDK warnings as errors" OFF)
option(MEM20_ENABLE_SANITIZERS "Build with AddressSanitizer + UBSan" OFF)
set(MEM20_CXX_STANDARD "17" CACHE STRING "C++ standard used to build the SDK (17 or 20)")

set(CMAKE_CXX_STANDARD ${MEM20_CXX_STANDARD})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

# --- version header consistency --------------------------------------------
# include/mem20/version.hpp is the single source of truth the code compiles
# against; the project(VERSION) above must not drift from it, or a consumer
# asking for a version gets a package whose headers claim another one.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/include/mem20/version.hpp" _mem20_version_hpp)
string(REGEX MATCH "kSdkVersion = \"([0-9]+\\.[0-9]+\\.[0-9]+)\"" _m "${_mem20_version_hpp}")
if(NOT _m)
  message(FATAL_ERROR "could not read kSdkVersion from include/mem20/version.hpp")
endif()
set(MEM20_SDK_VERSION_FROM_HEADER "${CMAKE_MATCH_1}")
if(NOT MEM20_SDK_VERSION_FROM_HEADER STREQUAL PROJECT_VERSION)
  message(FATAL_ERROR
    "version.hpp says ${MEM20_SDK_VERSION_FROM_HEADER} but project() says ${PROJECT_VERSION}")
endif()

# --- library ----------------------------------------------------------------
add_library(mem20_sdk
  src/client.cpp
  src/transport.cpp
  src/config.cpp
  src/child_process.hpp   # internal, not installed
)
add_library(mem20::mem20 ALIAS mem20_sdk)

# The export name is what consumers link as: mem20::mem20 (not mem20::mem20_sdk).
set_target_properties(mem20_sdk PROPERTIES EXPORT_NAME mem20)

target_include_directories(mem20_sdk
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src   # internal headers (child_process.hpp)
)

# The stdio transport uses POSIX threads; the dependency is PUBLIC because a
# static library cannot resolve it itself, so it must reach the consumer.
find_package(Threads REQUIRED)
target_link_libraries(mem20_sdk PUBLIC Threads::Threads)

# --- warnings + sanitizers --------------------------------------------------
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(mem20_sdk PRIVATE -Wall -Wextra -Wpedantic)
  if(MEM20_WARNINGS_AS_ERRORS)
    target_compile_options(mem20_sdk PRIVATE -Werror)
  endif()
endif()

if(MEM20_ENABLE_SANITIZERS)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    message(WARNING "MEM20_ENABLE_SANITIZERS is only wired for GCC/Clang")
  else()
    set(MEM20_SANITIZER_FLAGS -fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all)
    add_compile_options(${MEM20_SANITIZER_FLAGS})
    add_link_options(${MEM20_SANITIZER_FLAGS})
  endif()
endif()

# --- examples ---------------------------------------------------------------
# The walkthrough lives in docs/sdk/cpp/examples so the repository keeps one
# copy of it. Guarded with EXISTS: when sdk/cpp is vendored standalone (vcpkg,
# Conan, FetchContent of a subtree) the directory is simply absent.
if(MEM20_BUILD_EXAMPLES)
  set(MEM20_EXAMPLE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../docs/sdk/cpp/examples")
  if(EXISTS "${MEM20_EXAMPLE_DIR}/store_recall_audit.cpp")
    add_executable(mem20_store_recall_audit "${MEM20_EXAMPLE_DIR}/store_recall_audit.cpp")
    target_link_libraries(mem20_store_recall_audit PRIVATE mem20::mem20)
  else()
    message(STATUS "mem20: examples not found under ${MEM20_EXAMPLE_DIR}, skipping")
  endif()
endif()

# --- tests ------------------------------------------------------------------
if(MEM20_BUILD_TESTS)
  enable_testing()

  if(NOT DEFINED MEM20_REPO_ROOT)
    get_filename_component(MEM20_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
  endif()

  add_executable(mem20_sdk_tests tests/test_config.cpp)
  target_link_libraries(mem20_sdk_tests PRIVATE mem20::mem20)
  add_test(NAME mem20_sdk_tests COMMAND mem20_sdk_tests)

  # --- Live surface test -----------------------------------------------------
  # Exercises a REAL mem20 server over stdio: initialize handshake, tools/list
  # (asserting the live tool count), then one grounded memory_store ->
  # memory_recall round trip. This is the only test that proves the SDK's
  # surface against a running server rather than against documentation.
  #
  # If python3 / the mcp package / the server script is unavailable the test
  # exits 77 with a NAMED reason and ctest reports SKIPPED -- never a pass.
  add_executable(mem20_test_live_surface tests/test_live_surface.cpp)
  target_link_libraries(mem20_test_live_surface PRIVATE mem20::mem20)
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

  # --- Surface documentation drift guard -------------------------------------
  # The tool/domain count is stated in exactly one place in code
  # (include/mem20/surface.hpp, with static_asserts on the derivation) and
  # quoted in the two READMEs. This test greps all three and fails when they
  # disagree, so a stale count is a red test rather than a documentation bug
  # that ships. No server and no python3 required.
  add_executable(mem20_test_surface_docs tests/test_surface_docs.cpp)
  target_link_libraries(mem20_test_surface_docs PRIVATE mem20::mem20)
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

  # --- Install / export round trip -------------------------------------------
  # Installs this build into a scratch prefix, then configures and builds the
  # standalone consumer project in tests/consumer against ONLY
  # find_package(mem20 CONFIG REQUIRED). This is what makes the packaging claim
  # self-verifying instead of a paragraph in a README.
  add_test(NAME install_export
    COMMAND ${CMAKE_COMMAND}
      -DMEM20_BUILD_DIR=${CMAKE_BINARY_DIR}
      -DMEM20_CONSUMER_DIR=${CMAKE_CURRENT_SOURCE_DIR}/tests/consumer
      -DMEM20_SCRATCH_DIR=${CMAKE_CURRENT_BINARY_DIR}/install_export
      -DMEM20_GENERATOR=${CMAKE_GENERATOR}
      -DMEM20_BUILD_TYPE=${CMAKE_BUILD_TYPE}
      -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_install_export.cmake)
  set_tests_properties(install_export PROPERTIES
    SKIP_RETURN_CODE 77
    TIMEOUT 300
    LABELS "packaging"
  )
endif()

# --- install ----------------------------------------------------------------
install(TARGETS mem20_sdk
  EXPORT mem20Targets
  ARCHIVE  DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY  DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME  DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(DIRECTORY include/mem20
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
  FILES_MATCHING PATTERN "*.hpp"
)

# CMake package config: find_package(mem20 CONFIG REQUIRED)
set(MEM20_CMAKE_INSTALL_DIR "${CMAKE_INSTALL_LIBDIR}/cmake/mem20")

install(EXPORT mem20Targets
  NAMESPACE mem20::
  FILE mem20Targets.cmake
  DESTINATION ${MEM20_CMAKE_INSTALL_DIR}
)

configure_package_config_file(
  cmake/mem20Config.cmake.in
  "${CMAKE_CURRENT_BINARY_DIR}/mem20Config.cmake"
  INSTALL_DESTINATION ${MEM20_CMAKE_INSTALL_DIR}
)

write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/mem20ConfigVersion.cmake"
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/mem20Config.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/mem20ConfigVersion.cmake"
  DESTINATION ${MEM20_CMAKE_INSTALL_DIR}
)

# pkg-config: pkg-config --cflags --libs mem20
configure_file(cmake/mem20.pc.in "${CMAKE_CURRENT_BINARY_DIR}/mem20.pc" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/mem20.pc"
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/pkgconfig"
)

# Build-tree export so a sibling project can consume an uninstalled build with
# -Dmem20_DIR=<build dir>. No install required for the FetchContent/add_subdirectory story.
export(EXPORT mem20Targets
  NAMESPACE mem20::
  FILE "${CMAKE_CURRENT_BINARY_DIR}/mem20Targets.cmake"
)
