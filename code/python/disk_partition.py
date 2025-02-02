import logging
from utils import run_command

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def partition_disk(disk):
    logging.info(f"Partitioning disk {disk}...")

    try:
        run_command(["parted", f"/dev/{disk}", "--script", "mklabel", "gpt"])
        run_command(["parted", f"/dev/{disk}", "--script", "mkpart", "primary", "0%", "100%"])
        logging.info(f"Disk {disk} partitioned successfully.")
    except FileNotFoundError:
        logging.info(f"Error: `parted` command not found. Ensure it is installed.")
    except subprocess.CalledProcessError:
        logging.info(f"Error: Failed to partition {disk}.")
