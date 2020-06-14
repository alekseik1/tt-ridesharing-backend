#!/bin/bash
if [ "$1" = "prod" ]
then
  docker tag "$IMAGE_NAME" "${IMAGE_NAME}:${version}" && \
  docker tag "$IMAGE_NAME" "${IMAGE_NAME}:latest" && \
  docker push "${IMAGE_NAME}:${version}" && \
  docker push "${IMAGE_NAME}:latest"
elif [ "$1" = "dev" ]
then
   docker tag "$IMAGE_NAME" "${IMAGE_NAME}:dev" && \
   docker push "${IMAGE_NAME}:dev"
fi
