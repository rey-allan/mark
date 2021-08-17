#!/bin/bash

# Source the environment
source /opt/ros/melodic/setup.bash

# Create workspace
mkdir -p ~/catkin_ws/src

cd ~/catkin_ws
catkin init

# Build the workspace
cd ~/catkin_ws/
catkin build

# Source the workspace
cd ~/catkin_ws/
source devel/setup.bash

# Add the workspace to the .bashrc file
echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
