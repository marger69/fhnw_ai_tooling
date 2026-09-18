#!/bin/bash
#SBATCH --job-name=myproject
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"

singularity run \
  --bind "$SLURM_SUBMIT_DIR/artifacts:/outputs" \
  "$SLURM_SUBMIT_DIR/myproject-0.1.0.sif" \
  --config /app/configs/baseline.yaml \
  --output-dir "/outputs/slurm-${SLURM_JOB_ID}"