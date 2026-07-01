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

# RVT-1: register the display-vertical test suite for `colcon test`.
# (No ament_lint_auto: the repo enforces its own style per AGENTS.md.)
if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)

  ament_add_pytest_test(test_config test/test_config.py)
  ament_add_pytest_test(test_xacro_urdf test/test_xacro_urdf.py)
  ament_add_pytest_test(test_bridge_install test/test_bridge_install.py)

  add_launch_test(test/test_display_launch.py)
endif()

ament_package()
