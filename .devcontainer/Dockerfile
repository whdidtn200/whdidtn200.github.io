FROM mcr.microsoft.com/devcontainers/universal:2

# Install lightweight tooling not included by default
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    jq \
    tree \
    curl \
    htop \
  && rm -rf /var/lib/apt/lists/*
