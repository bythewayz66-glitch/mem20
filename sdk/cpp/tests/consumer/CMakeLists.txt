# sdk/cpp/tests/consumer/CMakeLists.txt
#
# A SEPARATE project whose only knowledge of mem20 is
# `find_package(mem20 CONFIG REQUIRED)`. It exists so the packaging claim is
# verified by the build instead of asserted in a document: `install_export`
# installs the SDK into a scratch prefix and then configures and builds THIS
# directory against that prefix.
#
# If the export set, the config file, the include install rule or the Threads
# dependency is wrong, this project fails to configure or link.

cmake_minimum_required(VERSION 3.16)
project(mem20_consumer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(MEM20_SANITIZERS "Match the SDK build's sanitizer flags" OFF)
if(MEM20_SANITIZERS AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
  add_link_options(-fsanitize=address,undefined)
endif()

find_package(mem20 CONFIG REQUIRED)

add_executable(mem20_consumer main.cpp)
target_link_libraries(mem20_consumer PRIVATE mem20::mem20)
