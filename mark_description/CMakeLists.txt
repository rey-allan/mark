cmake_minimum_required(VERSION 3.0.2)
project(mark_description)

find_package(catkin REQUIRED COMPONENTS roslaunch)

catkin_package()

# Uncomment once we have a launch file
# roslaunch_add_file_check(launch)

install(
  DIRECTORY launch meshes urdf
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)