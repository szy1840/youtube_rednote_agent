#!/bin/bash

# Set full environment for cron job
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Configuration - Set these environment variables in your crontab or system
# export CRON_LOG_PATH="/path/to/your/cron_log.txt"
# export PROJECT_ROOT_PATH="/path/to/your/project/root"
# export CONDA_PATH="/path/to/your/conda/installation"

# Source conda initialization
source ${CONDA_PATH:-/opt/conda}/etc/profile.d/conda.sh

# Activate the videolingo environment
conda activate videolingo

# Quick environment verification
echo "\n \n === Cron Job Started === \n \n" >> ${CRON_LOG_PATH:-/tmp/cron_log.txt}

# Change to working directory
cd ${PROJECT_ROOT_PATH:-/path/to/project/root}

# Run the Python script (already in activated conda environment)
python ${PROJECT_ROOT_PATH:-/path/to/project/root}/main.py
