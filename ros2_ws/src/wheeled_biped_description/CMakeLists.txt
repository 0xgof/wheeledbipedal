cmake_minimum_required(VERSION 3.8)
project(wheeled_biped_description)

find_package(ament_cmake REQUIRED)

# Robot description, launch, and RViz config.
install(DIRECTORY urdf launch rviz
        DESTINATION share/${PROJECT_NAME})

# BRG-1: install the canonical robot config (single source of truth in
# configs/robot/) into the package share at build time. The installed copy is a
# build artifact; configs/robot/wheeled_biped.yaml stays canonical.
get_filename_component(ROBOT_CONFIG
  "${CMAKE_CURRENT_SOURCE_DIR}/../../../configs/robot/wheeled_biped.yaml" ABSOLUTE)
if(NOT EXISTS "${ROBOT_CONFIG}")
  message(FATAL_ERROR "Canonical robot config not found: ${ROBOT_CONFIG}")
endif()
install(FILES "${ROBOT_CONFIG}" DESTINATION share/${PROJECT_NAME}/config)

ament_package()
