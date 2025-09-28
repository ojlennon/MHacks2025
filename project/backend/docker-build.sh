#!/bin/bash

docker buildx rm multiarch-builder
docker buildx create --name multiarch-builder --use
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64 -t ojlennon77/plate-ocr:latest --push .