cmake_minimum_required(VERSION 3.8)
project(poc_v2)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

install(
  DIRECTORY launch rviz urdf meshes config
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    poc_v2/pd_test.py
    poc_v2/gravity_comp_node.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
