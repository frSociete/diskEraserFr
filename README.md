# Disk Eraser - Secure Disk Wiping and Formatting Tool

Disk Eraser is a powerful tool for securely erasing data from hard drives or USB keys, while also providing the option to format the disk with a chosen file system (EXT4 or NTFS).

The project is designed to run inside a Docker container or as a bootable ISO.

---

## Features

- **List Available Disks**: Displays all detected disks for easy selection.
- **Secure Erase**: Uses random data overwriting to ensure deleted data cannot be recovered.
- **Automatic Partitioning**: Configures the disk with a single partition after erasure.
- **Flexible Formatting**: Allows you to format the disk with NTFS or EXT4 file systems.
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
docker pull <your_username>/disk-eraser:latest
 ```

2. **Run the Docker Image with Necessary Privileges**:

```bash
docker run --rm -it --privileged <your_username>/disk-eraser:latest
```

3. **Follow the interactive instructions inside the container to select and erase a disk**.

## Using the Bootable ISO

1. **Create the ISO: Use the provided Bash script in the project to generate a bootable ISO file**.

2. **Flash the ISO to a USB key**: Use a tool like dd or Rufus:

```bash
sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
```
