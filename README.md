# Disk Eraser - Secure Disk Wiping and Formatting Tool

Disk Eraser is a powerful tool for securely erasing data from hard drives or USB keys, while also providing the option to format the disk with a chosen file system (EXT4, NTFS or VFAT).

The project is designed to run inside a Docker container or as a bootable ISO.

---

## Features

- **List Available Disks**: Displays all detected disks for easy selection.
- **Secure Erase**: Uses random data overwriting to ensure deleted data cannot be recovered.
- **Automatic Partitioning**: Configures the disk with a single partition after erasure.
- **Flexible Formatting**: Allows you to format the disk with NTFS, EXT4 OR VFAT file systems.
- **Docker Support**: Designed to run securely in a containerized environment.
- **Bootable ISO**: Can be converted into a bootable ISO for standalone operation.

---

## Prerequisites

- Docker installed on your system (for running in a container).
- Root privileges (required for disk access).

---

## Installation and Usage

### Using with Docker

1. **Pull the Docker image from Docker Hub**:
```bash
docker pull zkbolo/disk-eraser-debian:1.0
 ```

2. **Run the Docker Image with Necessary Privileges**:

```bash
docker run --rm -it --privileged zkbolo/disk-eraser-debian:1.0
```

3. **Follow the interactive instructions inside the container to select and erase a disk**.

## Using the Bootable ISO

1. **Create the ISO: Use the provided Bash script in the project to generate a bootable ISO file**.

To run the script :

```bash
cd diskEraser/iso && chmod +x createIso.sh && sudo bash createIso.sh
```

2. **Flash the ISO to a USB key**: Use a tool like dd or Rufus:

```bash
sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
```

3. **Boot from the USB key**:

- Configure your BIOS/UEFI to boot from the USB key.

- Follow the on-screen instructions to use the tool.

## Command Line Options

When running the project directly in Python or via Docker, you can provide arguments to automate certain steps.

**Select file system**:

- -f ext4: Format the disk with the EXT4 file system.

- -f ntfs: Format the disk with the NTFS file system.

- -f vfat: Format the disk with the VFAT file system

Example :

```bash
python3 main.py -f ext4
```

## Project Structure

Here is the main structure of the project:

```bash
project/
├── README.md                   # Documentation for the project
├── code/                       # Main Python scripts for the tool
│   ├── disk_erase.py           # Module for secure data erasure
│   ├── disk_format.py          # Module for formatting disks
│   ├── disk_partition.py       # Module for creating partitions
│   ├── mainParse.py            # Main script with argument parsing
│   └── utils.py                # Utility functions (e.g., disk listing)
├── iso/                        # Files related to creating the bootable ISO
│   └── forgeIso.sh            # Script to generate the bootable ISO
├── setup.sh                    # Script to install dependencies and prepare the project
└── Dockerfile                  # Docker file to build docker image locally
```
