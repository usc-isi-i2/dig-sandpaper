#!/bin/bash
docker login -e $DOCKER_EMAIL -u $DOCKER_USER -p $DOCKER_PASS
export REPO=digsandpaper/digsandpaper
export TAG=`if [ "$TRAVIS_BRANCH" == "master" ]; then echo "latest"; else echo $TRAVIS_BRANCH ; fi`
docker build -f Dockerfile -t $REPO:$TRAVIS_COMMIT .
docker tag $REPO:$TRAVIS_COMMIT $REPO:$TAG
docker push $REPO