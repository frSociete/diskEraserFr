# Use Alpine Linux as the base image
FROM alpine:latest

# Set environment variables for non-interactive installations
ENV PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY ./code /app/code
COPY setup.sh /app/setup.sh

# Update Alpine and install required packages
RUN apk update && apk add --no-cache \
    bash \
    coreutils \
    parted \
    ntfs-3g \
    python3 \
    py3-pip \
    && chmod +x /app/setup.sh \
    && /app/setup.sh

# Grant execute permissions for Python scripts
RUN chmod +x /app/code/*.py

# Set the entry point
ENTRYPOINT ["python3", "/app/code/main.py"]

