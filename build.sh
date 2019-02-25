#!/usr/bin/env bash

# Fail on error
set -e
VIRTUAL_ENV_PATH="venv"

function print_help() {
    echo ""
    echo "Utility script for building and publishing package"
    echo ""
    echo "Usage: build command1"
    echo ""
    echo "Positional arguments"
    echo "command           Command to run. Available options are: clean, build, publish"
    echo ""
}

if [[ ! -v SKIP_VENV ]]; then
    print "Virtual environment is disabled. Continue with system global context."
else
    source "${VIRTUAL_ENV_PATH}/bin/activate"
fi

if [[ $# -eq 0 ]]; then
    print_help
    exit 1
fi

while [[ $# -gt 0 ]]
do
    command="$1"
    module="setup.py"
    case $command in
        clean)
        echo "Cleaning build output dirs"
        rm -rf src/build
        rm -rf dist/*
        rm -rf *.egg-info
        rm -rf src/*.egg-info
        ;;
        build)
        echo "Applying copyright..."
        ./development/copyright-update
        echo "done"
        echo "Building wheel package..."
        bash -c "cd src && python ./$module bdist_wheel --dist-dir=../dist --bdist-dir=../../build"
        echo "done"
        echo "Building source distribution..."
        bash -c "cd src && python ./$module sdist --dist-dir=../dist"
        echo "done"
        ;;
        publish)
        echo "Uploading packages on PyPi"
        twine upload -r pypi dist/*
        ;;
        *)
        echo "ERROR: Unknown command: $command."
        exit 1
    esac
    shift
done