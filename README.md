# Disk Eraser - Secure Disk Wiping and Formatting Tool 🗑️💽

# Disk Eraser

**Disk Eraser** 🔒 is a tool for securely erasing data from hard drives or USB keys, while also providing the option to format the disk with a chosen file system (EXT4, NTFS, or VFAT). It can erase multiple disks in parallel, ensuring thorough data wiping with multiple overwrite passes.

The tool operates with pre-selected confirmation and formatting options, requiring no further interaction from the user once the erasure process begins.

The project is designed to run inside a Docker container 🐳, as a bootable ISO 💿, directly as Python code 🐍, or as a Linux command stored in `/usr/local/bin` under the name `diskeraser`.

---

## Features ✨

- **List Available Disks** 📝: Displays all detected disks for easy selection and allows the user to erase one or more disks.
- **Secure Erase** 🔐: Uses multiple passes of random data followed by a final zero pass to prevent data recovery.
- **Parallel Erasure** ⚡: Uses multi-threading to erase multiple disks simultaneously, optimizing performance.
- **Automatic Partitioning** 📊: Configures the disk with a single partition after erasure.
- **Flexible Formatting** 📁: Supports NTFS, EXT4, or VFAT file systems.
- **Non-Interactive Mode** 🤖: Erasure and formatting options are pre-selected, eliminating the need for user input during execution.
- **Docker Support** 🐳: Runs securely in a containerized environment.
- **Bootable ISO** 💿: Can be converted into a bootable ISO for standalone operation.
- **Command Line Utility** 💻: Can be installed as a Linux command (`diskeraser`) for ease of use.
- **Configurable Erase Passes** 🔄: Users can specify the number of overwrite passes (default is 6).
- **Error Handling and Logging** 📋: Logs errors, including permission issues and failed disk operations.
- **Automatic Disk Verification** ✅: Confirms the integrity of the disk after the erasure process.
- **Root Privilege Check** 👑: Ensures the tool runs with proper administrative permissions to prevent incomplete operations.
- **Log File Creation** 📝: Automatically creates and maintains a log file at `/var/log/disk_erase.log` to store detailed information about the erasure process, errors, and system events.

---

## Prerequisites 📋

- **Root privileges** 👑 (required for disk access).
- **Docker** 🐳 (if running inside a container).
- **GCC Compiler** 🔨 (if compiling the C version).
- **Basic disk management knowledge** 📚, as the tool **permanently erases data** ⚠️.

---

## Installation and Usage 🚀

### Using Direct Python Code 🐍

1. **Download the repository**:

```bash
git clone https://github.com/Bolo101/diskEraser.git
```
2. **Execute code**:

```bash
cd diskEraser/code/python
sudo python3 main.py
```

### Install as a Linux Command (`diskeraser`) 💻

1. **Copy the scripts to `/usr/local/bin`**:
```bash
sudo mkdir -p /usr/local/bin/diskeraser
sudo cp diskEraser/code/python/*.py /usr/local/bin/diskeraser
sudo chmod +x /usr/local/bin/diskeraser/main.py
sudo ln -s /usr/local/bin/diskeraser/main.py /usr/local/bin/diskeraser
```
2. **Run the tool**:

```bash
sudo diskeraser
```
This allows you to execute the tool as a simple command from anywhere on your system.

### Using C compiled code 🔨

1. **Navigate to the C code directory**:

```bash
cd diskEraser/code/c
```

### Using with Docker 🐳

You can also deploy a Docker container to use the disks eraser tool. If Docker is not install on your system, you can execute the **installDocker.sh** script on a Debian based system. 
[Install Docker Script](https://github.com/Bolo101/Qemu.sh)

For other distributions please access the Docker download page.

#### Version 3.1 (New Version) 🆕

1. **Pull the latest Docker image**:

```bash
docker pull zkbolo/diskeraser-v3.1:latest
```

2. **Run the Docker Image with Necessary Privileges**:

```bash
docker run --rm -it --privileged zkbolo/diskeraser-v3.1:latest
```

3. **Follow the interactive instructions inside the container to select and erase one or more disks**:

- The tool will list all available disks, allow you to select which ones to erase, and confirm before starting the erasure process.

- You will also be prompted to choose a file system (EXT4, NTFS, or VFAT) after erasure.

### Using the Bootable ISO 💿

1. **Create the ISO**: Use the provided Bash script in the project to generate a bootable ISO file:

```bash
cd diskEraser/iso && chmod +x forgeIso.sh && sudo bash forgeIso.sh
```

If you prefer not to build the ISO yourself, you can download the pre-built ISO files for your system from the following links:

- [Download the latest version of the ISO (version 3.1)](https://archive.org/details/diskEraserV3-1)

These ISO file is ready to be flashed to a USB key and used for bootable operations.

---

2. **Flash the ISO to a USB key** 📀: Use a tool like `dd` or `Rufus`:

With a terminal to forge USB using **dd** command
```bash
sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
```

3. **Boot from the USB key**:

- Configure your BIOS/UEFI to boot from the USB key.

- Follow the on-screen instructions to use the tool, select the disks to erase, and choose a file system for formatting.

---

## Command Line Options ⌨️

When running the project directly in Python or via Docker, you can provide arguments to automate certain steps:

**Select file system** 💾:

- `-f ext4`: Format the disk with the EXT4 file system.
- `-f ntfs`: Format the disk with the NTFS file system.
- `-f vfat`: Format the disk with the VFAT file system.

### Example:

```bash
python3 main.py -f ext4
```

This will erase the selected disk(s), then format it using the EXT4 file system.

---

## Project Structure 📁

Here is the main structure of the project:

```bash
project/
├── README.md               # Documentation for the project 📚
├── code/                   # Main Python scripts for the tool 🐍
│   ├── disk_erase.py       # Module for secure data erasure 🗑️
│   ├── disk_format.py      # Module for formatting disks 💾
│   ├── disk_partition.py   # Module for creating partitions 📊
│   ├── log_handler.py      # Module for logging functionality 📝
│   ├── main.py             # Main script with program logic ⚙️
│   └── utils.py            # Utility functions (e.g., disk listing) 🔧
├── iso/                    # Files related to creating the bootable ISO 💿
│   ├── forgeIsoPy.sh       # Script to generate the bootable ISO 🔨
│   └── makefile            # Build automation for ISO creation 🏗️
├── setup.sh                # Script to install dependencies and prepare the project 🛠️
├── LICENSE                 # Common Creative 4 license ⚖️
└── Dockerfile              # Dockerfile to build docker image locally 🐳


```

---

## Notes ⚠️

- **Disk Safety** 🛡️: The tool **permanently erases** data from the selected disks. Make sure you have backups of any important data before proceeding.
- **Root Access** 👑: Ensure you are running the program with sufficient privileges to access and modify disks (i.e., root or `sudo`).
- **Non-Interactive Operation** 🤖: Once the erasure process begins, no further user interaction is required. All confirmation prompts and formatting options are selected beforehand.
- **Small Disks** 💾: If you are erasing very small disks, the tool may skip partitioning or formatting operations if the disk is too small to handle them.

## License ⚖️

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)

You are free to:
- Share 🔄: Copy and redistribute the material in any medium or format.
- Adapt 🔧: Remix, transform, and build upon the material.

Under the following terms:
- **Attribution** ✍️: You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- **NonCommercial** 💰❌: You may not use the material for commercial purposes.
- **ShareAlike** 🤝: If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

For more details, see the [license terms](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---