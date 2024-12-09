import os
from disk_erase import erase_disk
from disk_partition import partition_disk
from disk_format import format_disk
from utils import list_disks
from argparse import ArgumentParser

def main(fs_choice):
    # List available disks
    list_disks()
    
    # Disk selection
    disk = input("Enter the disk to erase (e.g., sda, sdb): ").strip()
    
    # Erase disk content
    erase_disk(disk)
    
    # Partition disk after data removal
    partition_disk(disk)
    
    # Filesystem to install on disk
    while not fs_choice:
        print("Choose a filesystem to format the disk:")
        print("1. NTFS")
        print("2. EXT4")
        print("3. VFAT")
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        
        if choice == "1":
            fs_choice = "ntfs"
        elif choice == "2":
            fs_choice = "ext4"
        elif choice == "3":
            fs_choice = "vfat"
        else:
            print("Invalid choice. Please select a correct choice from displayed menu.")
            
    
    # Format partition using selected filesystem
    format_disk(disk, fs_choice)
    print("Operation completed successfully.")

def sudo_check(args):
    if os.geteuid() != 0:
        print("This script must be run as root!")
    else:
        main(args.f)

def _parse_args():
    parser = ArgumentParser(description="Secure Disk Eraser Tool")
    parser.add_argument(
        '-f', 
        help="Filesystem type (ext4, ntfs, vfat)",
        choices=['ext4', 'ntfs', 'vfat'], 
        required=False
    )
    return parser.parse_args()

def app():
    args = _parse_args()
    sudo_check(args)

if __name__ == "__main__":
    app()
