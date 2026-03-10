# =============================================================================
# LLARS Smoke & E2E Test Container
# =============================================================================
# Portable container with all tools for smoke and E2E tests.
# Base image includes Node.js and Playwright with Chromium pre-installed.
#
# Usage:
#   # Smoke tests
#   docker compose --profile testing run --rm smoke-test-service \
#     bash /tests/smoke/smoke_test.sh
#
#   # E2E tests
#   docker compose --profile testing run --rm smoke-test-service \
#     bash -c "cd /tests/e2e && npx playwright test --project=chromium --workers=1"
# =============================================================================

FROM mcr.microsoft.com/playwright:v1.57.0-jammy

# System tools for smoke tests
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir 'python-socketio[client]>=5.11,<6' requests

WORKDIR /tests

# --- Smoke test scripts ---
COPY scripts/ci/smoke_test.sh /tests/smoke/
COPY scripts/ci/smoke_test_evaluation.sh /tests/smoke/
COPY scripts/ci/smoke_test_prompt_eng.sh /tests/smoke/
COPY scripts/ci/smoke_test_llm_response.py /tests/smoke/
COPY scripts/ci/wait_for_health.sh /tests/smoke/
COPY scripts/smoke_test_wizard.sh /tests/smoke/

RUN chmod +x /tests/smoke/*.sh

# --- E2E test dependencies ---
COPY llars-frontend/package.json llars-frontend/package-lock.json /tests/e2e/
COPY llars-frontend/playwright.config.js /tests/e2e/
COPY llars-frontend/e2e/ /tests/e2e/e2e/
RUN mkdir -p /tests/e2e/src/config
COPY llars-frontend/src/config/home_tiles.contract.json /tests/e2e/src/config/home_tiles.contract.json

# Install Node dependencies (Playwright browsers already in base image)
RUN cd /tests/e2e && npm ci --prefer-offline

ENTRYPOINT ["/bin/bash"]
