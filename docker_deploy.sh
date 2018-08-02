#!/bin/bash
echo "0"
docker login -u $DOCKER_USER -p $DOCKER_PASS
echo "0.1"
export REPO=uscisii2/digsandpaper
echo "$REPO"
export TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
echo "1"
#export DOCKERFILE_EXT=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo ".development"; else echo "" ; fi`
export DOCKERFILE_EXT=""
echo "2"
docker build -f Dockerfile${DOCKERFILE_EXT} -t $REPO:$TRAVIS_COMMIT .
echo "3"
docker tag $REPO:$TRAVIS_COMMIT $REPO:$TAG
echo "4"
docker push $REPO
echo "Done"