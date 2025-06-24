#!/bin/bash
#SBATCH --job-name=tgi-llama
#SBATCH --output=tgi-llama-%j.out
#SBATCH --error=tgi-llama-%j.err
#SBATCH --mail-user=kremlingph95027@th-nuernberg.de
#SBATCH --mail-type=NONE

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=p2
#SBATCH --gres=gpu:1
#SBATCH --mem-per-gpu=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=08:00:00
#SBATCH --qos=interactive

#SBATCH --container-image=ghcr.io/huggingface/text-generation-inference:3.3.2
#SBATCH --container-mounts=/nfs/scratch/students/kremlingph95027/models/qlora/llama-8B/v3/checkpoint-3826/:/models/llama

echo "=================================================================="
echo "Starting TGI Job at $(date)"
echo "Partition: ${SLURM_JOB_PARTITION}, GPUs: ${SLURM_GPUS_ON_NODE}, Mem/GPU: ${SLURM_MEM_PER_GPU}, CPUs: ${SLURM_CPUS_ON_NODE}"
echo "=================================================================="

text-generation-server \
  --model-id /models/llama \
  --quantize bitsandbytes \
  --load-in-8bit \
  --dtype float16 \
  --host 0.0.0.0 \
  --port 8195 \
  --max-batch-size 8 \
  --max-seq-len 2048