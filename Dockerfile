# Use Alpine Linux as the base image
FROM alpine:latest

# Set environment variables for non-interactive installations
ENV LANG=fr_FR.UTF-8 \
    LC_ALL=fr_FR.UTF-8 \
    PYTHONUNBUFFERED=1

# Install necessary dependencies and tools
RUN apk update && apk add --no-cache \
    bash \
    coreutils \
    parted \
    ntfs-3g \
    python3 \
    py3-pip \
    alpine-sdk \
    && echo "export LANG=fr_FR.UTF-8" >> /etc/profile \
    && echo "export LC_ALL=fr_FR.UTF-8" >> /etc/profile

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY ./code /app/code
COPY setup.sh /app/setup.sh

# Grant execute permissions to setup.sh and run it
RUN chmod +x /app/setup.sh \
    && /app/setup.sh

# Grant execute permissions for Python scripts
RUN chmod +x /app/code/*.py

# Set the entry point
ENTRYPOINT ["python3", "/app/code/main.py"]
