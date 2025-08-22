# Multi-stage build for optimized image size
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app/config /app/logs /app/models && \
    chown -R botuser:botuser /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# Copy application code
COPY --chown=botuser:botuser src/ ./src/
COPY --chown=botuser:botuser config/ ./config/

# Set Python path
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from src.bot import TelegramModerationBot; \
    bot = TelegramModerationBot('dummy'); \
    asyncio.run(bot.health_check())" || exit 1

# Run the bot
CMD ["python", "-u", "src/bot.py"]