FROM public.ecr.aws/docker/library/python:3.11.12-slim

WORKDIR /agent

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY docker/livekit-agents/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy agent code
COPY docker/livekit-agents/agent.py .

CMD ["python", "agent.py", "start"]
