#!/bin/bash
#!/bin/bash

DEFAULT_REPO="iamtaochen"
DEFAULT_NAME="onboarding"
DOCKER_FILE="back/Dockerfile"
MODE=$1; shift
if [ -z "$MODE" ]; then
    MODE="build"
fi

function build() {
    NAME=$1
    if [ -z "$NAME" ]; then
        NAME=$DEFAULT_NAME
    fi
    TAG=$2
    if [ -z "$TAG" ]; then
        TAG="latest"
    fi
    docker build -t $NAME:$TAG -f $DOCKER_FILE .
}

function push()
{
    NAME=$1
    if [ -z "$NAME" ]; then
        NAME=$DEFAULT_NAME
    fi
    TAG=$2
    if [ -z "$TAG" ]; then
        TAG="latest"
    fi
    REPO=$3
    if [ -z "$REPO" ]; then
        REPO=$DEFAULT_REPO
    fi
    IMAG=$NAME:$TAG
    REMOTE=$REPO/$IMAG
    docker tag $IMAG $REMOTE
    docker push $REMOTE
}

if [ "$MODE" == "build" ]; then
    build $@
elif [ "$MODE" == "push" ]; then
    push $@
elif [ "$MODE" == "all" ]; then
    build $@
    push $@
fi

