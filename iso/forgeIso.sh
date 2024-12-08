#!/bin/bash

# Exit on any error
set -e

# Variables
ISO_NAME="custom-debian-live.iso"
WORK_DIR="$HOME/debian-live-build"
SCRIPT_PATH="/path/to/your_programi/main.py"
REQUIRED_PACKAGES="coreutils parted ntfs-3g python3 python3-pip dosfstools"

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
echo "$REQUIRED_PACKAGES" >> config/package-lists/custom.list.chroot

# Copy the Python script to the ISO filesystem
echo "Copying the Python script..."
mkdir -p config/includes.chroot/usr/local/bin/
cp "$SCRIPT_PATH" config/includes.chroot/usr/local/bin/
chmod +x config/includes.chroot/usr/local/bin/$(basename "$SCRIPT_PATH")

# Modify .bashrc for the "user" profile
echo "Configuring .bashrc to run the program as root..."
mkdir -p config/includes.chroot/etc/skel/
cat << 'EOF' > config/includes.chroot/etc/skel/.bashrc
    sudo python3 /usr/local/bin/main.py
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

