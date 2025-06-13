# Use an official Python runtime as a parent image with a specific version
FROM python:3.10-slim-buster

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY --chown=appuser:appuser ./admin /app
# Copy common sources into the container at /app
COPY --chown=appuser:appuser ./common /app/common

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# Install libmagic
RUN apt-get update && apt-get install -y libmagic1

# Remove unnecessary tools and clean up
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set permissions
RUN chmod -R 755 /app

# Switch to non-root user
USER appuser

# Make port 8502 available to the world outside this container
EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8502/_stcore/health || exit 1

# Run __main__.py when the container launches
CMD ["streamlit", "run", "__main__.py", "--server.port=8502", "--server.headless=true", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"]
