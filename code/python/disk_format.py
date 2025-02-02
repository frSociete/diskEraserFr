import logging
from utils import run_command
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def format_disk(disk, fs_choice):
    partition = f"/dev/{disk}1"
    
    try:
        if fs_choice == "ntfs":
            logging.info(f"Formatting {partition} as NTFS...")
            run_command(["mkfs.ntfs", "-f", partition])
        elif fs_choice == "ext4":
            logging.info(f"Formatting {partition} as EXT4...")
            run_command(["mkfs.ext4", partition])
        elif fs_choice == "vfat":
            logging.info(f"Formatting {partition} as VFAT...")
            run_command(["mkfs.vfat", "-F", "32", partition])

        logging.info(f"Partition {partition} formatted successfully.")
    except FileNotFoundError:
        logging.error(f"Error: Filesystem utility not found for {fs_choice}. Ensure necessary tools are installed.")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error(f"Error: Failed to format {partition}.")
        sys.exit(1)
