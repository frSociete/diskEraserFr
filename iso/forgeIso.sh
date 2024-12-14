#!/bin/bash

# Exit on any error
set -e

# Variables
ISO_NAME="secure_disk_eraser.iso"
WORK_DIR="$HOME/debian-live-build"
CODE_DIR="$HOME/diskEraser/iso/code"  # Path to your Python code directory
REQUIRED_PACKAGES="coreutils parted ntfs-3g python3 python3-pip dosfstools firmware-linux-free firmware-linux-nonfree"

# Install necessary tools
echo "Installing live-build..."
sudo apt update
sudo apt install -y live-build python3 python3-pip

# Create working directory
echo "Setting up live-build workspace..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Initialize live-build
lb config

# Add required packages
echo "Adding required packages..."
echo "$REQUIRED_PACKAGES" > config/package-lists/custom.list.chroot

# Add firmware repository for Debian 12 (Bookworm)
echo "Configuring APT sources for non-free firmware..."
mkdir -p config/archives
cat << EOF > config/archives/debian.list.chroot
deb http://deb.debian.org/debian bookworm main contrib non-free-firmware
deb-src http://deb.debian.org/debian bookworm main contrib non-free-firmware
EOF

# Copy all Python files from the code directory
echo "Copying Python files..."
mkdir -p config/includes.chroot/usr/local/bin/
cp "$CODE_DIR"/*.py config/includes.chroot/usr/local/bin/
chmod +x config/includes.chroot/usr/local/bin/*.py

# Modify .bashrc for the "user" profile to run main.py
echo "Configuring .bashrc to run main.py as root..."
mkdir -p config/includes.chroot/etc/skel/
cat << 'EOF' > config/includes.chroot/etc/skel/.bashrc
if [ "$(id -u)" -ne 0 ]; then
    echo "Running main.py as root..."
    sudo python3 /usr/local/bin/main.py
else
    python3 /usr/local/bin/main.py
fi
EOF

# Configure passwordless sudo for the "user" account
echo "Configuring passwordless sudo for 'user'..."
mkdir -p config/includes.chroot/etc/sudoers.d/
cat << EOF > config/includes.chroot/etc/sudoers.d/user_nopasswd
user ALL=(ALL) NOPASSWD:ALL
EOF

# Build the ISO
echo "Building the ISO..."
sudo lb build

# Move the ISO to the home directory
if [ -f live-image-amd64.hybrid.iso ]; then
    mv live-image-amd64.hybrid.iso "$HOME/$ISO_NAME"
    echo "ISO created successfully: $HOME/$ISO_NAME"
else
    echo "ISO build failed."
    exit 1
fi

# Cleanup (optional)
echo "Cleaning up..."
sudo lb clean

echo "Done."
