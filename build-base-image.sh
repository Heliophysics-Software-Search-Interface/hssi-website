# build the base image for the website docker container
docker build -f ./docker/base_image/Dockerfile -t hssi_base:latest ./docker/base_image/