# Use Debian 12 as base image
FROM debian:latest

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
    curl \
    wget


# Set the working directory to /bootable_iso
WORKDIR /bootable_iso

RUN mkdir -p /tmp/kernel-packages


# Copy the kernel packages from the host machine to the container's /tmp/kernel-packages
COPY bootable_iso/tmp_packages /tmp/kernel-packages

# Copy the contents of the current directory (including bootable_iso) into the container
COPY bootable_iso /bootable_iso
COPY build_iso.sh /

# Make the build script executable
RUN chmod +x /build_iso.sh

# Set the entrypoint to run the build script
ENTRYPOINT ["/build_iso.sh"]
