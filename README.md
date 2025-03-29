# Disk Eraser - Secure Disk Wiping and Formatting Tool 🗑️💽

**Disk Eraser** 🔒 is a tool for securely erasing data from hard drives or USB keys, while also providing the option to format the disk with a chosen file system (EXT4, NTFS, or VFAT). It can erase multiple disks in parallel, ensuring thorough data wiping with multiple overwrite passes.

> ⚠️ **IMPORTANT: SSD COMPATIBILITY WARNING** ⚠️
> 
> This tool is **PRIMARILY RECOMMENDED FOR HDD DRIVES ONLY**. While the tool can detect SSDs and will work on them, it is **NOT RECOMMENDED for secure SSD erasure** due to the following reasons:
> 
> - **SSD Wear Leveling**: SSDs use wear leveling algorithms that redistribute write operations across all memory cells. This means data may not be overwritten in the same physical location when using traditional wiping methods.
> 
> - **Over-provisioning**: SSDs often have hidden reserved space that cannot be accessed by standard tools but may still contain sensitive data.
> 
> - **Device Lifespan**: Multiple overwrite passes can significantly reduce the lifespan of an SSD due to the limited write cycles of flash memory.
> 
> **For secure SSD data erasure, please use manufacturer-provided secure erase tools or ATA Secure Erase commands.**

The tool operates with pre-selected confirmation and formatting options, requiring no further interaction from the user once the erasure process begins.

The project is designed to run as a bootable ISO 💿, directly as Python code 🐍, or as a Linux command stored in `/usr/local/bin` under the name `diskeraser`.

---

## Features ✨

- **Enhanced User Interface** 🖥️: Available in both CLI and GUI modes for flexibility
- **SSD Detection** 🔍: Automatically detects SSD devices and provides appropriate warnings
- **List Available Disks** 📝: Displays all detected disks for easy selection and allows the user to erase one or more disks
- **Secure Erase** 🔐: Uses multiple passes of random data followed by a final zero pass to prevent data recovery
- **Active System Disk Detection** 🛡️: Identifies and warns before erasing the active system disk
- **Parallel Erasure** ⚡: Uses multi-threading to erase multiple disks simultaneously, optimizing performance
- **Automatic Partitioning** 📊: Configures the disk with a single partition after erasure
- **Flexible Formatting** 📁: Supports NTFS, EXT4, or VFAT file systems
- **Bootable ISO** 💿: Can be converted into a bootable ISO for standalone operation
- **Command Line Utility** 💻: Can be installed as a Linux command (`diskeraser`) for ease of use
- **Configurable Erase Passes** 🔄: Users can specify the number of overwrite passes (default is 5)
- **Error Handling and Logging** 📋: Logs errors, including permission issues and failed disk operations
- **Root Privilege Check** 👑: Ensures the tool runs with proper administrative permissions to prevent incomplete operations
- **Log File Creation** 📝: Automatically creates and maintains a log file to store detailed information about the erasure process, errors, and system events
- **Disk Serial Identification** 🏷️: Uses disk serial numbers for more reliable identification

---

## GUI Mode Features 🖥️

The GUI interface provides a user-friendly way to interact with the Disk Eraser tool:

- **Fullscreen Operation**: Starts in fullscreen mode with an option to exit fullscreen
- **Visual Disk Selection**: Shows all available disks with checkboxes for selection
- **Disk Information Display**: Shows disk model, size, and serial number
- **Color-Coded Warnings**: Highlights active system disks and SSDs in red
- **SSD Warning Messages**: Displays specific warnings when SSD devices are detected
- **Progress Tracking**: Shows real-time progress of the erasure operation
- **Live Log Display**: Provides a scrollable log window to monitor operations
- **Multiple Confirmation Dialogs**: Ensures users understand the risks before proceeding
- **Filesystem Selection**: Radio buttons for choosing between EXT4, NTFS, and FAT32
- **Pass Configuration**: Allows users to specify the number of overwrite passes
- **Refresh Capability**: Button to refresh the disk list

---

## CLI Mode Features 💻

The command-line interface offers powerful features for advanced users and scripting:

- **Detailed Disk Information**: Shows comprehensive details about each disk
- **Serial Number Identification**: Identifies disks by their serial numbers
- **Type Detection**: Displays whether each disk is an SSD or HDD
- **Active Disk Warning**: Clearly marks system disks with danger warnings
- **Multi-Level Confirmation**: Requires explicit confirmation for each disk
- **Enhanced Safety**: Requires typing "DESTROY" to confirm system disk erasure
- **Parallel Processing**: Erases multiple disks simultaneously
- **Progress Reporting**: Shows real-time progress for each disk operation
- **Filesystem Selection**: Interactive menu for choosing the filesystem
- **Argument Support**: Accepts command-line arguments for automation
- **Error Handling**: Detailed error messages and logging

---

## ISO Features 💿

The bootable ISO provides a standalone environment for disk erasure:

- **Debian-Based Live Environment**: Built on Debian Bookworm for stability
- **XFCE Desktop Environment**: Provides a lightweight graphical interface
- **Auto-Start Capability**: Automatically launches the Disk Eraser tool on boot
- **French AZERTY Keyboard Support**: Configured for French users by default
- **Terminal Auto-Launch**: Starts the tool automatically in terminal mode
- **Dual Boot Options**: Includes options to run live or install to disk
- **Calamares Installer**: Integrated installer for permanent installation
- **Network Support**: Includes Network Manager for connectivity
- **Complete Firmware Support**: Includes non-free firmware for wide hardware compatibility
- **Integrated Disk Eraser**: Tool is pre-installed and ready to use
- **Desktop Launcher**: Desktop icon for easy access to the tool
- **Passwordless Sudo**: Configured for ease of use without password prompts

---

## Prerequisites 📋

- **Root privileges** 👑 (required for disk access)
- **Python 3** 🐍 (for running the Python version)
- **Tkinter** 🖼️ (for the GUI interface)
- **Basic disk management knowledge** 📚, as the tool **permanently erases data** ⚠️

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
sudo python3 main.py         # For GUI mode (default)
sudo python3 main.py --cli   # For command-line mode
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
sudo diskeraser           # For GUI mode (default)
sudo diskeraser --cli     # For command-line mode
```

This allows you to execute the tool as a simple command from anywhere on your system.


3. **Follow the interactive instructions inside the container to select and erase one or more disks**:

- The tool will list all available disks, allow you to select which ones to erase, and confirm before starting the erasure process.

- You will also be prompted to choose a file system (EXT4, NTFS, or VFAT) after erasure.

### Using the Bootable ISO 💿

1. **Create the ISO**: Use the provided Bash script in the project to generate a bootable ISO file:

```bash
cd diskEraser/iso && chmod +x forgeIso.sh && sudo bash forgeIso.sh
```

If you prefer not to build the ISO yourself, you can download the pre-built ISO files for your system from the following links:

- [Download the latest version of the ISO (version 4.0)](https://archive.org/details/diskEraser-v4)

This ISO file is ready to be flashed to a USB key and used for bootable operations.

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

When running the project directly in Python you can provide arguments to automate certain steps:

**Mode selection**:
- `--cli`: Run in command-line interface mode instead of GUI mode

**Filesystem selection** 💾:
- `-f ext4` or `--filesystem ext4`: Format the disk with the EXT4 file system
- `-f ntfs` or `--filesystem ntfs`: Format the disk with the NTFS file system
- `-f vfat` or `--filesystem vfat`: Format the disk with the VFAT file system

**Erase passes**:
- `-p 3` or `--passes 3`: Specify the number of passes for secure erasure (default is 5)

### Examples:

```bash
# Run in GUI mode with EXT4 filesystem and 3 passes
python3 main.py -f ext4 -p 3

# Run in CLI mode with NTFS filesystem
python3 main.py --cli -f ntfs
```

---

## Project Structure 📁

Here is the main structure of the project:

```bash
project/
├── README.md               # Documentation for the project 
├── code/                   # Main Python scripts for the tool
│   ├── disk_erase.py       # Module for secure data erasure 
│   ├── disk_format.py      # Module for formatting disks 
│   ├── disk_operations.py  # Module for disk operations 
│   ├── disk_partition.py   # Module for creating partitions 
│   ├── gui_interface.py    # GUI interface for the tool 
│   ├── cli_interface.py    # CLI interface for the tool 
│   ├── log_handler.py      # Module for logging functionality 
│   ├── main.py             # Main script with program logic 
│   └── utils.py            # Utility functions (e.g., disk listing) 
├── iso/                    # Files related to creating the bootable ISO 
│   ├── forgeIsoPy.sh       # Script to generate the bootable ISO 
│   └── makefile            # Build automation for ISO creation 
├── setup.sh                # Script to install dependencies and prepare the project 
└── LICENSE                 # Common Creative 4 license 
```

---

## Notes ⚠️

- **Disk Safety** : The tool **permanently erases** data from the selected disks. Make sure you have backups of any important data before proceeding.
- **Root Access** : Ensure you are running the program with sufficient privileges to access and modify disks (i.e., root or `sudo`).
- **SSD Limitations** : As mentioned above, this tool is primarily designed for HDDs. While it can detect and work with SSDs, manufacturer tools are strongly recommended for secure SSD data erasure.
- **Active System Disk** : The tool will detect and warn if you attempt to erase the disk containing the active system. Proceeding with such an operation will cause system failure.

## License ⚖️

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)

You are free to:
- Share 🔄: Copy and redistribute the material in any medium or format.
- Adapt 🔧: Remix, transform, and build upon the material.

Under the following terms:
- **Attribution** : You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- **NonCommercial** : You may not use the material for commercial purposes.
- **ShareAlike** : If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

For more details, see the [license terms](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---