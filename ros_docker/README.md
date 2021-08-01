# ROS Docker

This is an image for setting up and running ROS Melodic in a Docker container.

## Building the image

```
docker build -t mark:ros -f ros_docker/Dockerfile .
```

> **Note:** The Dockerfile assumes the working directory to be the repo's root.

## Running the image

```
docker run -it --rm mark:ros /bin/bash
```

## Converting MARK's `xacro` files to `urdf`

First run the image mounting the `mark_description` directory.

```
docker run -it --rm -v /path/to/mark_description:/catkin_ws/src/mark_description mark:ros /bin/bash
```

Then build the `mark_description` package.

```
catkin build && source devel/setup.bash
```

Finally, convert the `xacro` files into a single `urdf` file.

```
rosrun xacro xacro -o src/mark_description/urdf/mark.urdf src/mark_description/urdf/mark.urdf.xacro
```

The `urdf` file should be available inside `mark_description/urdf`.
