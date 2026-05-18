cmake_minimum_required(VERSION 3.22)

#
# This file is generated only once,
# and is not re-generated if converter is called multiple times.
#
# User is free to modify the file as much as necessary
#

# Setup compiler settings
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)

# Define the build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

# Set the project name
set(CMAKE_PROJECT_NAME STM32-FW-IMAGE)

# Enable compile command to ease indexing with e.g. clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Core project settings
project(${CMAKE_PROJECT_NAME})
message("Build type: " ${CMAKE_BUILD_TYPE})

# Enable CMake support for ASM and C languages
enable_language(C ASM)

# Create an executable object type
add_executable(${CMAKE_PROJECT_NAME})

# Add STM32CubeMX generated sources
add_subdirectory(cmake/stm32cubemx)

# Link directories setup
target_link_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined library search paths
)

# Add sources to executable
target_sources(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user sources here
)

# Add include paths
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined include paths
)

# Add project symbols (macros)
target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined symbols
)

# Remove wrong libob.a library dependency when using cpp files
list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_LIBRARIES ob)

# Add linked libraries
target_link_libraries(${CMAKE_PROJECT_NAME}
    stm32cubemx
    # Add user defined libraries
)

# Convert Firmware .elf to .bin
add_custom_command(TARGET ${CMAKE_PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${CMAKE_PROJECT_NAME}> ${CMAKE_PROJECT_NAME}.bin
    BYPRODUCTS ${CMAKE_PROJECT_NAME}.bin
    COMMENT "[1/2] Generating Firmware BIN file..."
)

# Find Python
find_package(Python3 REQUIRED COMPONENTS Interpreter)

# Run the Unified Builder Script
add_custom_command(TARGET ${CMAKE_PROJECT_NAME} POST_BUILD
    COMMAND Python3::Interpreter ${CMAKE_SOURCE_DIR}/FIRMWARE-HEADER-TOOL.py 
		${CMAKE_SOURCE_DIR}/build/Release/STM32-FW-IMAGE.bin # <--- Arg 1: Raw Firmware Image
		${CMAKE_SOURCE_DIR}/STM32-FW-IMAGE-SIGNED.bin        # <--- Arg 2: Signed Firmware Image
		${CMAKE_SOURCE_DIR}/STM32-FW-IMAGE-UNSIGNED.bin      # <--- Arg 2: Unsigned Firmware Image
		1                                       			 # <--- Arg 3: Version Number
		${CMAKE_SOURCE_DIR}/private.pem         			 # <--- Arg 4: Absolute path to Private Key
    COMMENT "[2/2] Filling Firmware Metadata..."
)
