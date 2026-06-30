cmake_minimum_required(VERSION 3.8)
project(wheeled_biped_description)

find_package(ament_cmake REQUIRED)

# Robot description, launch, RViz config, and the build-time config copy (BRG-1).
install(DIRECTORY urdf launch rviz config
        DESTINATION share/${PROJECT_NAME})

ament_package()
