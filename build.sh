#!/bin/bash

# Update pip
pip install --upgrade pip

# Install system dependencies
apt-get update && apt-get install -y libheif-dev

# Install Python dependencies
pip install -r requirements.txt