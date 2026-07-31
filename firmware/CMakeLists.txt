cmake_minimum_required(VERSION 3.13...3.27)

# The SDK is installed outside the repository so this project stays small and
# its toolchain can be upgraded independently.
if (NOT DEFINED PICO_SDK_PATH)
    set(PICO_SDK_PATH "$ENV{HOME}/.pico-sdk")
endif()

include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(airgap_tx_signer C CXX ASM)

pico_sdk_init()

add_executable(airgap_tx_signer_bringup
    src/main.c
)

target_include_directories(airgap_tx_signer_bringup PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/include
)

target_link_libraries(airgap_tx_signer_bringup PRIVATE
    pico_stdlib
)

# The USB CDC serial device is the first host/device integration point.
pico_enable_stdio_usb(airgap_tx_signer_bringup 1)
pico_enable_stdio_uart(airgap_tx_signer_bringup 0)
pico_add_extra_outputs(airgap_tx_signer_bringup)
