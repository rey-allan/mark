# Adapted from: https://github.com/Unity-Technologies/Unity-Robotics-Hub/blob/main/tutorials/pick_and_place/docker/Dockerfile
FROM ros:melodic-ros-base

RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654
RUN sudo apt-get update && sudo apt-get install -y vim python-pip python-catkin-tools ros-melodic-xacro

ENV ROS_WORKSPACE=/catkin_ws

COPY ./mark_docker/scripts ${ROS_WORKSPACE}/scripts
RUN ${ROS_WORKSPACE}/scripts/setup-workspace.sh

WORKDIR $ROS_WORKSPACE
