#!/bin/bash

set -e -x

if [ "${BUILD}" == "tests" ]; then
    codecov
fi
