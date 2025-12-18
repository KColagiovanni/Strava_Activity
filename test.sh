#!/usr/bin/env bash

export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 # Disable auto-loading of external pytest plugins(ROS)
export CULTUREMESH_API_KEY=1234
export WTF_CSRF_SECRET_KEY=1234
export CULTUREMESH_API_BASE_ENDPOINT=dummy

python -m pytest