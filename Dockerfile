# Use the official Debian image from Docker Hub
FROM debian:latest

# Set the working directory in the container
WORKDIR /app

# Install necessary packages
RUN apt-get update -y && \
    apt-get install -y \
    coreutils \
    parted \
    ntfs-3g \
    python3 \
    python3-pip \
    dosfstools && \
    apt-get clean

# Copy the entire project into the /app directory in the container
COPY . /app

# Clean up unnecessary files (if any)
RUN rm -rf /app/setup.sh  # Only if you included the setup.sh script in your COPY command

# Set the default command to run the Python script
CMD ["python3", "/app/code/main.py"]
