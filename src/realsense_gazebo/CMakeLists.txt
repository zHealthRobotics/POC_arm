cmake_minimum_required(VERSION 3.8)
project(realsense_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ========================
# Find dependencies
# ========================
find_package(ament_cmake REQUIRED)

# ========================
# Install non-code assets
# ========================
install(
  DIRECTORY
    launch
    worlds
    models
  DESTINATION share/${PROJECT_NAME}
)

# ========================
# Install Python nodes
# ========================
install(
  PROGRAMS
    scripts/yolo_world_node.py
    scripts/base_yolow.py
  DESTINATION lib/${PROJECT_NAME}
)

# ========================
# Testing (unchanged)
# ========================
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

