#!/bin/bash
docker login -e $DOCKER_EMAIL -u $DOCKER_USER -p $DOCKER_PASS
export REPO=digsandpaper/digsandpaper
export TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
export DOCKERFILE_EXT=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo ".development"; else echo "" ; fi`
docker build -f Dockerfile${DOCKERFILE_EXT} -t $REPO:$TRAVIS_COMMIT .
docker tag $REPO:$TRAVIS_COMMIT $REPO:$TAG
docker push $REPO