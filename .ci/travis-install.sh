#!/bin/bash

set -e -x

pip install --upgrade pip

if [ "${BUILD}" != "flake8" ]; then
    pip install --upgrade setuptools
    git clone https://github.com/JHUISI/charm.git
    cd charm && ./configure.sh && make install
    cd ..
fi

if [ "${BUILD}" == "tests" ]; then
    pip install -e .[test]
    pip install --upgrade codecov
elif [ "${BUILD}" == "flake8" ]; then
    pip install flake8
elif [ "${BUILD}" == "docs" ]; then
    pip install -e .[docs]
fi
