#!/bin/bash

echo "Starting ROS2 Docker environment..."

docker compose up -d

echo "Entering container..."

docker exec -it poc_arm_container bash
