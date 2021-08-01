# Adapted from: https://github.com/Unity-Technologies/Unity-Robotics-Hub/blob/main/tutorials/pick_and_place/docker/Dockerfile
FROM ros:melodic-ros-base

RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654
RUN sudo apt-get update && sudo apt-get install -y vim python-pip python-catkin-tools ros-melodic-xacro

ENV ROS_WORKSPACE=/catkin_ws

COPY ./ros_docker/set-up-workspace /setup.sh
RUN chmod +x /setup.sh && /setup.sh && rm /setup.sh

WORKDIR $ROS_WORKSPACE
