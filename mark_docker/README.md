# mark_docker

A Docker image for running ROS Melodic and MARK-related ROS utilities.

## Building the image

```
docker build -t mark:ros -f mark_docker/Dockerfile .
```

> **Note:** The Dockerfile assumes the working directory to be the repo's root.

## Running the image interactively

```
docker run -it --rm mark:ros /bin/bash
```

## Compiling MARK's `xacro` files to a single `urdf`

Run the `compile-urdf.sh` script mounting the `mark_description` directory.

```
docker run --rm -v /path/to/mark_description:/catkin_ws/src/mark_description mark:ros ./scripts/compile-urdf.sh
```

The `urdf` file should be available inside `mark_description/urdf`.
