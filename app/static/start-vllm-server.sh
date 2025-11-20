#!/bin/bash
#SBATCH --job-name=vllm-server
#SBATCH --output=vllm-server-%j.out
#SBATCH --error=vllm-server-%j.err
#SBATCH --mail-user=kremlingph95027@th-nuernberg.de
#SBATCH --mail-type=NONE

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=p1
#SBATCH --gres=gpu:1
#SBATCH --mem-per-gpu=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=08:00:00
#SBATCH --qos=interactive

echo "=================================================================="
echo "Starting VLLM Server at $(date)"
echo "Partition: ${SLURM_JOB_PARTITION}, GPUs: ${SLURM_GPUS_ON_NODE}, Mem/GPU: ${SLURM_MEM_PER_GPU}, CPUs: ${SLURM_CPUS_ON_NODE}"
echo "=================================================================="

module load cuda/cuda-11.8.0

# shellcheck disable=SC1090
source "/home/$USER/venv/bin/activate"

CACHE_DIR=/nfs/scratch/students/$USER/.cache
export PIP_CACHE_DIR=$CACHE_DIR
export HF_HOME=$CACHE_DIR
export TRANSFORMERS_USE_BF16=1
mkdir -p "$CACHE_DIR"

BASE_MODEL_PATH=/nfs/scratch/students/kremlingph95027/.cache/models--meta-llama--Llama-3.1-8B/snapshots/d04e592bb4f6aa9cfee91e2e20afa771667e1d4b
LORA_ADAPTER_PATH=/nfs/scratch/students/kremlingph95027/models/qlora/llama-8B/v3/checkpoint-3826
BASE_VLLM_MODEL_NAME=llama-8B-base
LORA_VLLM_MODEL_NAME=llama-8B-v3-qlora

python -m vllm.entrypoints.openai.api_server \
  --model "${BASE_MODEL_PATH}" \
  --served-model-name "${BASE_VLLM_MODEL_NAME}" \
  --enable-lora \
  --lora-modules ${LORA_VLLM_MODEL_NAME}="${LORA_ADAPTER_PATH}" \
  --max_lora_rank 64 \
  --host 0.0.0.0 \
  --port 8195 \
  --max-model-len 40960 \
  --gpu-memory-utilization 0.9 \
  --dtype float16 \
  --load-format auto \
  --chat-template "{{ messages[0]['content'] }}"