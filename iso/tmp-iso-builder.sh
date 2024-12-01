#!/bin/bash

set -e

# Variables
ISO_NAME="secure_disk_eraser.iso"
WORK_DIR="/bootable_iso"
DEBIAN_VERSION="bullseye"
TARGET_DIR="${WORK_DIR}/iso_root"
SCRIPT_DIR="${WORK_DIR}/scripts"
GRUB_CFG_DIR="${TARGET_DIR}/boot/grub"
KERNEL_VERSION="linux-image-amd64" # Meta-package for the latest Debian kernel
PACKAGE_DIR="/tmp/kernel-packages"

# Step 1: Install dependencies on the host system
echo "Installing necessary tools on the host system..."
apt-get update --fix-missing
apt-get install -y live-build xorriso squashfs-tools debootstrap grub-pc-bin grub-efi-amd64-bin grub2-common python3 python3-pip parted ntfs-3g coreutils dosfstools apt-utils wget

# Step 2: Set up working directories
echo "Creating working directories..."
mkdir -p "${TARGET_DIR}" "${SCRIPT_DIR}" "${GRUB_CFG_DIR}" "${PACKAGE_DIR}"

# Step 3: Clean up previous debootstrap or incomplete install in target directory
echo "Cleaning up the target directory to avoid conflicts..."
rm -rf "${TARGET_DIR}"/*

# Step 4: Create a minimal Debian system in iso_root using debootstrap
echo "Installing minimal Debian system using debootstrap..."
debootstrap --arch=amd64 --variant=minbase "${DEBIAN_VERSION}" "${TARGET_DIR}" http://deb.debian.org/debian/

# Step 5: Download kernel and initramfs-tools packages
echo "Downloading kernel and initramfs-tools packages..."

# Ensure proper permissions for the download directory
mkdir -p "${PACKAGE_DIR}" && chmod -R 755 "${PACKAGE_DIR}"

# Identify the kernel package dependency for linux-image-amd64
echo "Determining the actual kernel package..."
KERNEL_PACKAGE=$(apt-cache depends linux-image-amd64 | grep 'Depends:' | awk '{print $2}')

# Validate if the kernel package name was fetched correctly
if [ -z "${KERNEL_PACKAGE}" ]; then
    echo "Failed to determine the kernel package name. Exiting..."
    exit 1
fi

# Download the required kernel and initramfs-tools packages
echo "Downloading kernel package: ${KERNEL_PACKAGE} and initramfs-tools..."
apt-get download "${KERNEL_PACKAGE}" initramfs-tools || {
    echo "apt-get download failed, trying an alternative method..."
    apt-get install --download-only -y "${KERNEL_PACKAGE}" initramfs-tools
}

# Move downloaded packages to the PACKAGE_DIR
echo "Moving downloaded packages to ${PACKAGE_DIR}..."
mv /initramfs-tools*.deb /linux-image-*.deb "${PACKAGE_DIR}/" 2>/dev/null || true

# Check if the packages were moved
echo "Checking downloaded packages in ${PACKAGE_DIR}..."
ls -l "${PACKAGE_DIR}"

# Ensure packages are downloaded
if [ "$(ls -A $PACKAGE_DIR | grep -E '\.deb$')" == "" ]; then
    echo "Failed to download kernel or initramfs-tools packages. Check your network or package names."
    exit 1
fi


# Step 6: Enter chroot and install packages
echo "Entering chroot to install necessary packages and kernel..."
cp "${PACKAGE_DIR}"/*.deb "${TARGET_DIR}/tmp/"
chroot "${TARGET_DIR}" /bin/bash <<EOF
set -e
# Install required packages
dpkg -i /tmp/*.deb || apt-get install -f -y
# Clean up temporary files
rm -rf /tmp/*.deb
EOF

# Step 7: Install kernel and initramfs-tools inside the chroot
echo "Installing kernel and initramfs-tools inside the chroot..."

# Mount /tmp/kernel-packages to ensure access inside chroot
mount --bind /tmp/kernel-packages /mnt/tmp/kernel-packages

chroot "${TARGET_DIR}" /bin/bash <<EOF
set -e

# Ensure the system is updated inside the chroot
apt-get update

# Install dependencies for kernel and initramfs-tools
apt-get install -y kmod linux-base initramfs-tools-core

# Install the downloaded kernel and initramfs-tools packages
dpkg -i /mnt/tmp/kernel-packages/initramfs-tools_0.142+deb12u1_all.deb
dpkg -i /mnt/tmp/kernel-packages/linux-image-6.1.0-28-amd64_6.1.119-1_amd64.deb

# Fix broken dependencies
apt-get -f install -y
EOF

# Unmount after installation
umount /mnt/tmp/kernel-packages



# Step 8: Copy the kernel and initramfs to the ISO root
echo "Copying kernel and initramfs to the ISO root..."
cp "${TARGET_DIR}/boot/vmlinuz-${INSTALLED_KERNEL}" "${TARGET_DIR}/boot/vmlinuz"
cp "${TARGET_DIR}/boot/initrd.img-${INSTALLED_KERNEL}" "${TARGET_DIR}/boot/initrd.img"

# Step 9: Install GRUB for BIOS and UEFI booting
echo "Installing GRUB bootloader..."
chroot "${TARGET_DIR}" apt-get install -y grub-pc-bin grub-efi-amd64-bin grub2-common

# Create necessary directories for GRUB
mkdir -p "${TARGET_DIR}/boot/grub/i386-pc"
mkdir -p "${TARGET_DIR}/boot/efi"

# Install GRUB for BIOS
echo "Creating BIOS El Torito boot image..."
grub-mkimage \
    -O i386-pc \
    -o "${TARGET_DIR}/boot/grub/i386-pc/eltorito.img" \
    -p "/boot/grub" \
    biosdisk part_msdos ext2 configfile normal

# Install GRUB for UEFI
mkdir -p "${TARGET_DIR}/boot/efi/EFI/BOOT"
grub-mkstandalone \
    --format=x86_64-efi \
    --output="${TARGET_DIR}/boot/efi/EFI/BOOT/BOOTX64.EFI" \
    --modules="part_gpt part_msdos fat ext2 normal configfile linux" \
    --locales="" \
    --themes="" \
    --fonts=""

# Step 10: Create GRUB configuration
echo "Creating GRUB configuration..."
bash -c "cat <<EOF > ${GRUB_CFG_DIR}/grub.cfg
set timeout=5
set default=0

menuentry \"Secure Disk Eraser\" {
    linux /boot/vmlinuz root=/dev/sr0 rw quiet
    initrd /boot/initrd.img
}
EOF"

# Step 11: Build the ISO image using xorriso
echo "Building the bootable ISO with xorriso..."
xorriso -as mkisofs \
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
