#!/bin/bash

# Build the catkin workspace
catkin build && source devel/setup.bash

# Compile the `xacro` files into a single `urdf` file
rosrun xacro xacro -o src/mark_description/urdf/mark.urdf src/mark_description/urdf/mark.urdf.xacro
