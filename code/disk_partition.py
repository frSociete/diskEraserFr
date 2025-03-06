import logging
from utils import run_command
import sys
from subprocess import CalledProcessError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def partition_disk(disk: str) -> None:
    logging.info(f"Partitioning disk {disk}...")

    try:
        # Make sure we're working with just the device name without /dev/
        disk_name = disk.replace('/dev/', '')
        
        # Create a new GPT partition table
        run_command(["parted", f"/dev/{disk_name}", "--script", "mklabel", "gpt"])
        
        # Create a primary partition using 100% of disk space
        run_command(["parted", f"/dev/{disk_name}", "--script", "mkpart", "primary", "0%", "100%"])
        
        logging.info(f"Disk {disk_name} partitioned successfully.")
    except FileNotFoundError:
        logging.error(f"Error: `parted` command not found. Ensure it is installed.")
        sys.exit(2)
    except CalledProcessError as e:
        logging.error(f"Error: Failed to partition {disk}: {e}")
        sys.exit(1)