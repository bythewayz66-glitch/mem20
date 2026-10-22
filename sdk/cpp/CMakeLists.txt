cmake_minimum_required(VERSION 3.16)
project(mem20_sdk VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(mem20_sdk
  src/client.cpp
  src/transport.cpp
  src/config.cpp
)
target_include_directories(mem20_sdk
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
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
