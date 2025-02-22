# Use the lightweight Debian Slim image
FROM debian:bullseye-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary packages for the Secure Disk Erase Tool
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    coreutils \
    parted \
    ntfs-3g \
    dosfstools \
    e2fsprogs \
    util-linux \
    python3 \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire project into the /app directory in the container
COPY ./code /app

# Set the default command to run the Python script
CMD ["python3", "/app/main.py"]