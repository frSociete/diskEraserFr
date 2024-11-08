#!/bin/bash

# Install required packages for the Secure Disk Erase Tool

echo "Updating package lists..."
sudo apt-get update -y

echo "Installing necessary packages..."
# Install shred for secure erasure, parted for partitioning, and ntfs-3g for NTFS support
sudo apt-get install -y coreutils parted ntfs-3g python3 python3-pip

echo "Setup complete. You can now run the Secure Disk Erase Tool."

