#!/bin/bash

# Exit on any error
set -e

# Variables
ISO_NAME="secure_disk_eraser.iso"
WORK_DIR="$HOME/debian-live-build"
CODE_DIR="$HOME/diskEraser/code/c/elf"  # Path to your C code directory
ELF_BINARY="disk_tool"  # ELF binary to execute
REQUIRED_PACKAGES="coreutils parted ntfs-3g dosfstools firmware-linux-free firmware-linux-nonfree debian-installer-launcher calamares calamares-settings-debian"

# Install necessary tools
echo "Installing live-build..."
sudo apt update
sudo apt install -y live-build wget

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

# Set keyboard layout to AZERTY
echo "Configuring AZERTY keyboard layout..."
mkdir -p config/includes.chroot/etc/default/
cat << EOF > config/includes.chroot/etc/default/keyboard
XKBMODEL="pc105"
XKBLAYOUT="fr"
XKBVARIANT="azerty"
XKBOPTIONS=""
EOF

# Copy the ELF binary to /usr/local/bin
echo "Copying ELF binary..."
mkdir -p config/includes.chroot/usr/local/bin/
cp "$CODE_DIR/$ELF_BINARY" config/includes.chroot/usr/local/bin/
chmod +x config/includes.chroot/usr/local/bin/$ELF_BINARY

# Configure .bashrc to execute the ELF binary as root
echo "Configuring .bashrc to execute the ELF binary..."
mkdir -p config/includes.chroot/etc/skel/
cat << 'EOF' > config/includes.chroot/etc/skel/.bashrc
if [ "$(id -u)" -ne 0 ]; then
    echo "Running disk_tool as root..."
    sudo /usr/local/bin/disk_tool
else
    /usr/local/bin/disk_tool
fi
EOF

# Configure passwordless sudo for the "user" account
echo "Configuring passwordless sudo for 'user'..."
mkdir -p config/includes.chroot/etc/sudoers.d/
cat << EOF > config/includes.chroot/etc/sudoers.d/user_nopasswd
user ALL=(ALL) NOPASSWD:ALL
EOF

# Enable Debian Installer
echo "Adding Debian Installer..."
mkdir -p config/includes.installer
touch config/includes.installer/install

# Ensure Debian Installer files are included
echo "Downloading and adding Debian Installer files..."
mkdir -p config/debian-installer
wget -P config/debian-installer http://ftp.debian.org/debian/dists/bookworm/main/installer-amd64/current/images/netboot/debian-installer/amd64/linux
wget -P config/debian-installer http://ftp.debian.org/debian/dists/bookworm/main/installer-amd64/current/images/netboot/debian-installer/amd64/initrd.gz

mkdir -p config/includes.binary/install.amd
cp config/debian-installer/linux config/includes.binary/install.amd/vmlinuz
cp config/debian-installer/initrd.gz config/includes.binary/install.amd/initrd.gz

# Modify Boot Configuration for Installer Option
echo "Configuring boot options..."

# ISOLINUX (BIOS-based boot)
mkdir -p config/includes.binary/isolinux
cat << 'EOF' > config/includes.binary/isolinux/live.cfg
label install
    menu label ^Install Debian Secure Disk Eraser
    kernel /install.amd/vmlinuz
    append initrd=/install.amd/initrd.gz
EOF

# GRUB (UEFI-based boot)
mkdir -p config/includes.binary/grub
cat << 'EOF' > config/includes.binary/grub/grub.cfg
menuentry "Install Debian Secure Disk Eraser" {
    linux /install.amd/vmlinuz
    initrd /install.amd/initrd.gz
}
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
