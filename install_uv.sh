#!/bin/bash

curl -LsSf https://astral.sh/uv/install.sh | sh

uv add -r requirements.txt
