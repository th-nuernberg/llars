FROM python:3.11-slim

WORKDIR /agent

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY docker/livekit-agents/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY docker/livekit-agents/agent.py .

CMD ["python", "agent.py"]
