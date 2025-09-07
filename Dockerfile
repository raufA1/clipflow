FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r clipflow && useradd -r -g clipflow clipflow

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data temp logs && \
    chown -R clipflow:clipflow /app

# Switch to non-root user
USER clipflow

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import asyncio; from clipflow_main import ClipFlowOrchestrator, ConfigManager; exit(0 if asyncio.run(ClipFlowOrchestrator(ConfigManager.load_from_env()).health_check())['overall_status'] == 'healthy' else 1)"

# Expose port (for future web interface)
EXPOSE 8000

# Start application
CMD ["python", "clipflow_main.py"]