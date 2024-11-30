#!/bin/bash

set -e

# Variables
ISO_NAME="secure_disk_eraser.iso"
WORK_DIR="$(pwd)/bootable_iso"
DEBIAN_VERSION="bullseye"
TARGET_DIR="${WORK_DIR}/iso_root"
SCRIPT_DIR="${WORK_DIR}/scripts"
GRUB_CFG_DIR="${TARGET_DIR}/boot/grub"
KERNEL_VERSION="$(uname -r)"

# Step 1: Install dependencies
echo "Installing necessary tools..."
sudo apt-get update
sudo apt-get install -y live-build syslinux isolinux genisoimage squashfs-tools debootstrap grub-pc-bin grub2-common

# Step 2: Set up working directories
echo "Creating working directories..."
mkdir -p "${TARGET_DIR}" "${SCRIPT_DIR}" "${GRUB_CFG_DIR}"

# Step 3: Create a minimal Debian system in iso_root using debootstrap
echo "Installing minimal Debian system using debootstrap..."
sudo debootstrap --arch=amd64 "${DEBIAN_VERSION}" "${TARGET_DIR}" http://deb.debian.org/debian/

# Step 4: Chroot into the system and install dependencies
echo "Entering chroot to install dependencies..."
sudo chroot "${TARGET_DIR}" /bin/bash <<EOF
apt-get update
apt-get install -y python3 python3-pip parted ntfs-3g shred dosfstools
pip3 install --upgrade pip
EOF

# Step 5: Copy Python code into the new system
echo "Copying Python code into the chroot environment..."
sudo cp -r ./scripts/* "${TARGET_DIR}/root/"

# Step 6: Create startup script to run the Python code as root
echo "Creating startup script to run Python program..."
sudo bash -c 'cat <<EOF > ${TARGET_DIR}/etc/profile.d/startup.sh
#!/bin/bash
python3 /root/main.py
EOF'

sudo chmod +x "${TARGET_DIR}/etc/profile.d/startup.sh"

# Step 7: Create GRUB configuration
echo "Creating GRUB configuration..."
sudo bash -c 'cat <<EOF > ${GRUB_CFG_DIR}/grub.cfg
set timeout=5
set default=0

menuentry "Secure Disk Eraser" {
    linux /boot/vmlinuz root=/dev/sr0 rw quiet
    initrd /boot/initrd.img
}
EOF'

# Step 8: Copy the kernel and initramfs
echo "Copying kernel and initramfs..."
sudo cp /boot/vmlinuz-${KERNEL_VERSION} "${TARGET_DIR}/boot/vmlinuz"
sudo cp /boot/initrd.img-${KERNEL_VERSION} "${TARGET_DIR}/boot/initrd.img"

# Step 9: Build the ISO image
echo "Building the bootable ISO..."
sudo genisoimage -o "${WORK_DIR}/${ISO_NAME}" \
    -b boot/grub/i386-pc/eltorito.img \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    -iso-level 3 "${TARGET_DIR}"

# Step 10: Finished!
echo "Bootable ISO ${ISO_NAME} has been created successfully!"

echo "You can now flash this ISO to a USB drive using the following command:"
echo "sudo dd if=${WORK_DIR}/${ISO_NAME} of=/dev/sdX bs=4M status=progress"
