# GitHub Actions compatible Ubuntu runner
FROM ubuntu:22.04

# Set environment variables to match GitHub Actions
ENV DEBIAN_FRONTEND=noninteractive
ENV RUNNER_OS=Linux
ENV RUNNER_ARCH=X64
ENV GITHUB_ACTIONS=true
ENV CI=true

# Install system dependencies that match GitHub Actions runner
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python versions that match CI matrix
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default (matches CI primary version)
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install uv (matches CI setup)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create working directory
WORKDIR /workspace

# Copy project files
COPY . .

# Install dependencies (matches CI step)
RUN uv sync --extra dev

# Set up entry point for CI commands
COPY docker/ci-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
