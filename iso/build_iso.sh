#!/bin/bash

set -e

# Variables
ISO_NAME="secure_disk_eraser.iso"
WORK_DIR="/bootable_iso"
DEBIAN_VERSION="bullseye"
TARGET_DIR="${WORK_DIR}/iso_root"
SCRIPT_DIR="${WORK_DIR}/scripts"
GRUB_CFG_DIR="${TARGET_DIR}/boot/grub"
KERNEL_VERSION="$(uname -r)"
PACKAGE_DIR="/tmp/kernel-packages"

# Step 1: Install dependencies on the host system
echo "Installing necessary tools on the host system..."
apt-get update --fix-missing
apt-get install -y live-build xorriso squashfs-tools debootstrap grub-pc-bin grub-efi-amd64-bin grub2-common python3 python3-pip parted ntfs-3g coreutils dosfstools

# Step 2: Set up working directories
echo "Creating working directories..."
mkdir -p "${TARGET_DIR}" "${SCRIPT_DIR}" "${GRUB_CFG_DIR}"

# Step 3: Clean up previous debootstrap or incomplete install in target directory
echo "Cleaning up the target directory to avoid conflicts..."
rm -rf "${TARGET_DIR}"/*

# Step 4: Create a minimal Debian system in iso_root using debootstrap
echo "Installing minimal Debian system using debootstrap..."
debootstrap --arch=amd64 --variant=minbase "${DEBIAN_VERSION}" "${TARGET_DIR}" http://deb.debian.org/debian/

# Step 5: Chroot into the system and prepare it for sysvinit
echo "Entering chroot to install necessary packages..."
chroot "${TARGET_DIR}" /bin/bash <<EOF
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
cp -r ${SCRIPT_DIR}/* "${TARGET_DIR}/root/"

# Step 7: Create startup script to run Python program
echo "Creating startup script to run Python program..."
chroot "${TARGET_DIR}" mkdir -p /etc/profile.d/
chroot "${TARGET_DIR}" bash -c 'cat <<EOF > /etc/profile.d/startup.sh
#!/bin/bash
python3 /root/main.py
EOF'
chroot "${TARGET_DIR}" chmod +x /etc/profile.d/startup.sh

# Step 8: Install GRUB for BIOS and UEFI booting
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

# Step 9: Create GRUB configuration
echo "Creating GRUB configuration..."
bash -c "cat <<EOF > ${GRUB_CFG_DIR}/grub.cfg
set timeout=5
set default=0

menuentry \"Secure Disk Eraser\" {
    linux /boot/vmlinuz root=/dev/sr0 rw quiet
    initrd /boot/initrd.img
}
EOF"

# Step 10: Copy the kernel and initramfs
echo "Copying kernel and initramfs..."

# Ensure the downloaded packages exist
if [ ! -d "$PACKAGE_DIR" ] || [ "$(ls -A $PACKAGE_DIR)" == "" ]; then
    echo "Kernel packages not found in $PACKAGE_DIR. Please verify the Dockerfile setup."
    exit 1
fi

# Copy the downloaded packages into the chroot environment
cp "${PACKAGE_DIR}"/*.deb "${TARGET_DIR}/tmp/"

# Install the kernel and initramfs inside the chroot
chroot "${TARGET_DIR}" /bin/bash <<EOF
cd /tmp
dpkg -i linux-image-*.deb || apt-get install -f -y
dpkg -i initramfs-tools*.deb || apt-get install -f -y
EOF

# Determine the installed kernel version
INSTALLED_KERNEL=$(chroot "${TARGET_DIR}" bash -c "ls /boot/vmlinuz-* | xargs -n1 basename | sed 's/vmlinuz-//'")
if [ -z "$INSTALLED_KERNEL" ]; then
    echo "Failed to determine the installed kernel version."
    exit 1
fi

# Copy the kernel and initramfs images
cp "${TARGET_DIR}/boot/vmlinuz-${INSTALLED_KERNEL}" "${TARGET_DIR}/boot/vmlinuz"
cp "${TARGET_DIR}/boot/initrd.img-${INSTALLED_KERNEL}" "${TARGET_DIR}/boot/initrd.img"

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
