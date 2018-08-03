#!/bin/bash
docker login -u $DOCKER_USER -p $DOCKER_PASS
export REPO=uscisii2/digsandpaper
echo "$REPO"
export TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
#export DOCKERFILE_EXT=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo ".development"; else echo "" ; fi`
export DOCKERFILE_EXT=""
docker build -f Dockerfile${DOCKERFILE_EXT} -t $REPO:$TRAVIS_COMMIT .
docker tag $REPO:$TRAVIS_COMMIT $REPO:$TAG
docker push $REPO