FROM quay.io/astronomer/astro-runtime:11.0.0

# Switch to root for system packages
USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to astro user
USER astro

# Configure Git (required for DVC and Git operations)
RUN git config --global user.email "airflow@astronomer.io" && \
    git config --global user.name "Airflow Pipeline" && \
    git config --global init.defaultBranch main

# Create data directory with proper permissions
RUN mkdir -p /usr/local/airflow/include/data && \
    chmod -R 755 /usr/local/airflow/include

# Set working directory
WORKDIR /usr/local/airflow