FROM osrf/ros:humble-desktop

# Install basic tools
RUN apt update && apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-serial \
    git \
    nano

# Initialize rosdep
RUN rosdep update

# Create workspace
WORKDIR /ros2_ws

# Copy only src for dependency resolution
COPY src src

# Install ROS dependencies from packages
RUN rosdep install --from-paths src --ignore-src -r -y

# Source ROS automatically
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

CMD ["bash"]
