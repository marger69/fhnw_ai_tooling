#!/bin/bash
#SBATCH --job-name=hello-ai-tooling
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:02:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
hostname
date
sleep 10
echo "job finished"