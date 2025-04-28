# Disk Eraser - Secure Disk Wiping and Formatting Tool 💽

<div style="display: flex; align-items: center;">
  <img src="./background" alt="Logo" width="120" style="margin-right: 20px;">
  <p>
    <b>Disk Eraser</b> is a tool for securely erasing data from storage devices while providing the option to format with your chosen file system (EXT4, NTFS, or VFAT). It supports parallel disk erasure with configurable overwrite passes for thorough data sanitization.
  </p>
</div>

## Secure Erasure Methods

### For HDDs: Multiple Overwrite Passes
- Recommended for traditional mechanical hard drives
- Uses multiple passes of random data followed by a zero pass
- Prevents data recovery through physical analysis of magnetic residue

### For SSDs: Cryptographic Erasure
- Recommended for solid-state drives and flash storage
- Options include:
  - **Random Data Fill**: Overwrites with cryptographically secure random data
  - **Zero Fill**: Quick erasure by writing zeros to all addressable locations
- Works with ATA Secure Erase for compatible devices

> ⚠️ **SSD COMPATIBILITY WARNING**
> 
> While this tool can detect and work with SSDs, please note:
> 
> - **SSD Wear Leveling**: Makes traditional overwrite methods less effective
> - **Over-provisioning**: Hidden reserved space may retain data
> - **Device Lifespan**: Multiple passes can reduce SSD longevity
> 
> For SSDs, cryptographic erasure methods are recommended over multiple overwrite passes.

---

## Features ✨

- **Dual Interface**: CLI and GUI modes for flexibility
- **Smart Device Detection**: Automatically identifies SSDs vs HDDs
- **Secure Erasure Methods**:
  - Multiple overwrite passes for HDDs
  - Cryptographic erasure for SSDs (random or zero fill)
- **Safety Features**: Detects active system disks and requires confirmation
- **Parallel Processing**: Erases multiple disks simultaneously
- **Post-Erasure Setup**: Automatic partitioning and formatting
- **Flexible Formats**: Supports NTFS, EXT4, and VFAT file systems
- **Multiple Deployment Options**: Run as Python code, Linux command, or bootable ISO

---

## Prerequisites 📋

- **Root privileges** (required for disk access)
- **Python 3** with **Tkinter** (for GUI mode)
- **Basic disk management knowledge** - this tool **permanently erases data** ⚠️

---

## Installation and Usage 🚀

### Using Python Code 🐍

```bash
git clone https://github.com/Bolo101/diskEraser.git
cd diskEraser/code/python
sudo python3 main.py         # GUI mode (default)
sudo python3 main.py --cli   # Command-line mode
```

### Install as Linux Command 💻

```bash
sudo mkdir -p /usr/local/bin/diskeraser
sudo cp diskEraser/code/python/*.py /usr/local/bin/diskeraser
sudo chmod +x /usr/local/bin/diskeraser/main.py
sudo ln -s /usr/local/bin/diskeraser/main.py /usr/local/bin/diskeraser

# Then run:
sudo diskeraser           # GUI mode
sudo diskeraser --cli     # CLI mode
```

### Using Bootable ISO 💿

1. **Create or download ISO**:
   - Create XFCE based iso:
   
   ```bash
   cd diskEraser/iso && make
   ```

   - Create KDE based iso:

   ```bash
   cd diskEraser/iso && make kde
   ```
   - Pre-built ISO

   Download pre-built: [Disk Eraser ISO v5.0](https://archive.org/details/diskEraser-V5)

2. **Flash to USB**:
   ```bash
   sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
   ```

3. **Boot from USB** and follow on-screen instructions

---

## Command Line Options ⌨️

```bash
# Format options
-f ext4|ntfs|vfat, --filesystem ext4|ntfs|vfat

# Erase pass count
-p NUMBER, --passes NUMBER

# Interface mode
--cli           # Use command-line interface

# Examples:
python3 main.py -f ext4 -p 3      # GUI, EXT4, 3 passes
python3 main.py --cli -f ntfs     # CLI, NTFS, default passes
```

---

## Project Structure 📁

```
project/
├── README.md               # Documentation
├── code/                   # Python scripts
│   ├── disk_erase.py       # Erasure module
│   ├── disk_format.py      # Formatting module
│   ├── disk_operations.py  # Disk operations
│   ├── disk_partition.py   # Partitioning module
│   ├── gui_interface.py    # GUI interface
│   ├── cli_interface.py    # CLI interface
│   ├── log_handler.py      # Logging functionality
│   ├── main.py             # Main program logic
│   └── utils.py            # Utility functions
├── iso/                    # ISO creation resources
│   ├── forgeIsoPy.sh       # ISO generator
│   └── makefile            # Build automation
├── setup.sh                # Dependency installer
└── LICENSE                 # CC 4.0 license
```

---

## Safety Notes ⚠️

- **Data Loss**: This tool **permanently erases** data. Back up important information first.
- **Root Access**: Run with appropriate privileges (root/sudo).
- **Storage Types**: Different erasure methods are optimized for different storage technologies:
  - For HDDs: Multiple overwrite passes
  - For SSDs: Cryptographic erasure (random or zero fill)
- **System Protection**: The tool detects and warns about active system disks.

---

## License ⚖️

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)

You are free to:
- **Share**: Copy and redistribute the material
- **Adapt**: Remix, transform, and build upon the material

Under the following terms:
- **Attribution**: Provide appropriate credit
- **NonCommercial**: Not for commercial use
- **ShareAlike**: Distribute modifications under the same license
