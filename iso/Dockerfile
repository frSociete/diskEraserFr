# Use Debian 12 as base image
FROM debian:latest

# Set the maintainer label (optional)
LABEL maintainer="your-email@example.com"

# Update and install required packages
RUN apt-get update && apt-get install -y \
    live-build \
    xorriso \
    squashfs-tools \
    debootstrap \
    grub-pc-bin \
    grub-efi-amd64-bin \
    grub2-common \
    python3 \
    python3-pip \
    parted \
    ntfs-3g \
    coreutils \
    dosfstools \
    git \
    curl \
    wget

# Create directory for kernel packages
RUN mkdir -p /tmp/kernel-packages

# Download kernel packages
RUN curl -o /tmp/kernel-packages/linux-image.deb http://deb.debian.org/debian/pool/main/l/linux/linux-image-6.1.0-28-amd64.deb \
    && curl -o /tmp/kernel-packages/initramfs-tools.deb http://deb.debian.org/debian/pool/main/i/initramfs-tools/initramfs-tools_*.deb


# Verify downloaded files
RUN ls -la /tmp/kernel-packages

# Set the working directory to /bootable_iso
WORKDIR /bootable_iso

# Copy the contents of the current directory (including bootable_iso) into the container
COPY ./bootable_iso /bootable_iso
COPY ./build_iso.sh /

# Make the build script executable
RUN chmod +x /build_iso.sh

# Set the entrypoint to run the build script
ENTRYPOINT ["/build_iso.sh"]
