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

# Step 1: Install dependencies on the host system
echo "Installing necessary tools on the host system..."
sudo apt-get update
sudo apt-get install -y live-build xorriso squashfs-tools debootstrap grub-pc-bin grub-efi-amd64-bin grub2-common python3 python3-pip parted ntfs-3g coreutils dosfstools

# Step 2: Set up working directories
echo "Creating working directories..."
mkdir -p "${TARGET_DIR}" "${SCRIPT_DIR}" "${GRUB_CFG_DIR}"

# Step 3: Clean up previous debootstrap or incomplete install in target directory
echo "Cleaning up the target directory to avoid conflicts..."
sudo rm -rf "${TARGET_DIR}"/*

# Step 4: Create a minimal Debian system in iso_root using debootstrap
echo "Installing minimal Debian system using debootstrap..."
sudo debootstrap --arch=amd64 --variant=minbase "${DEBIAN_VERSION}" "${TARGET_DIR}" http://deb.debian.org/debian/

# Step 5: Chroot into the system and prepare it for sysvinit
echo "Entering chroot to install necessary packages..."
sudo chroot "${TARGET_DIR}" /bin/bash <<EOF
# Remove systemd if installed and replace with sysvinit
apt-get remove --purge -y systemd
apt-get install -y sysvinit-core python3 python3-pip parted ntfs-3g coreutils dosfstools

# Clean up any lingering systemd packages
apt-get autoremove --purge -y

# Upgrade pip
pip3 install --upgrade pip
EOF

# Step 6: Copy Python code into the chroot environment
echo "Copying Python code into the chroot environment..."
sudo cp -r ${SCRIPT_DIR}/* "${TARGET_DIR}/root/"

# Step 7: Create startup script to run Python program
echo "Creating startup script to run Python program..."
sudo chroot "${TARGET_DIR}" mkdir -p /etc/profile.d/
sudo chroot "${TARGET_DIR}" bash -c 'cat <<EOF > /etc/profile.d/startup.sh
#!/bin/bash
python3 /root/main.py
EOF'
sudo chroot "${TARGET_DIR}" chmod +x /etc/profile.d/startup.sh

# Step 8: Install GRUB for BIOS and UEFI booting
echo "Installing GRUB bootloader..."
sudo chroot "${TARGET_DIR}" apt-get install -y grub-pc-bin grub-efi-amd64-bin grub2-common

# Create necessary directories for GRUB
sudo mkdir -p "${TARGET_DIR}/boot/grub/i386-pc"
sudo mkdir -p "${TARGET_DIR}/boot/efi"

# Create necessary directories for GRUB
sudo mkdir -p "${TARGET_DIR}/boot/grub/i386-pc"
sudo mkdir -p "${TARGET_DIR}/boot/efi"

# Install GRUB for BIOS
echo "Creating BIOS El Torito boot image..."
sudo grub-mkimage \
    -O i386-pc \
    -o "${TARGET_DIR}/boot/grub/i386-pc/eltorito.img" \
    -p "/boot/grub" \
    biosdisk part_msdos ext2 configfile normal

# Install GRUB for UEFI
sudo mkdir -p "${TARGET_DIR}/boot/efi/EFI/BOOT"
sudo grub-mkstandalone \
    --format=x86_64-efi \
    --output="${TARGET_DIR}/boot/efi/EFI/BOOT/BOOTX64.EFI" \
    --modules="part_gpt part_msdos fat ext2 normal configfile linux" \
    --locales="" \
    --themes="" \
    --fonts=""


# Step 9: Create GRUB configuration
echo "Creating GRUB configuration..."
sudo bash -c "cat <<EOF > ${GRUB_CFG_DIR}/grub.cfg
set timeout=5
set default=0

menuentry \"Secure Disk Eraser\" {
    linux /boot/vmlinuz root=/dev/sr0 rw quiet
    initrd /boot/initrd.img
}
EOF"

# Step 10: Copy the kernel and initramfs
echo "Copying kernel and initramfs..."
sudo cp /boot/vmlinuz-${KERNEL_VERSION} "${TARGET_DIR}/boot/vmlinuz"
sudo cp /boot/initrd.img-${KERNEL_VERSION} "${TARGET_DIR}/boot/initrd.img"

# Step 11: Build the ISO image using xorriso
echo "Building the bootable ISO with xorriso..."
sudo xorriso -as mkisofs \
    -o "${WORK_DIR}/${ISO_NAME}" \
    -b boot/grub/i386-pc/eltorito.img \
    -c boot.catalog \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    --efi-boot boot/efi/EFI/BOOT/BOOTX64.EFI \
    -eltorito-alt-boot \
    -no-emul-boot \
    -iso-level 3 \
    "${TARGET_DIR}"


# Step 12: Finished!
echo "Bootable ISO ${ISO_NAME} has been created successfully!"

echo "You can now flash this ISO to a USB drive using the following command:"
echo "sudo dd if=${WORK_DIR}/${ISO_NAME} of=/dev/sdX bs=4M status=progress"
