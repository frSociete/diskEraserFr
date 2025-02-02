import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def is_ssd(device):
    """
    Check if the given device is an SSD.
    """
    try:
        output = subprocess.run(
            ["cat", f"/sys/block/{device}/queue/rotational"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output.stdout.decode().strip() == "0"
    except FileNotFoundError:
        logging.info(f"SSD check failed: {device} not found.")
    except subprocess.SubprocessError:
        logging.info(f"Error executing subprocess for SSD check on {device}.")
    return False

def erase_disk(device, passes):
    """
    Securely erase the entire disk using `shred`, then wipe the partition table using `dd`.
    """
    try:
        if is_ssd(device):
            logging.info(f"Warning: {device} appears to be an SSD. Use `hdparm` for secure erase.")
            return

        logging.info(f"Erasing {device} using shred with {passes} passes...")

        # Loop through each pass and call shred, printing progress
        for i in range(1, passes + 1):
            logging.info(f"Pass {i} of {passes} is being processed...")
            subprocess.run(["shred", "-n", "1", "-z", f"/dev/{device}"], check=True)

        logging.info(f"Wiping partition table of {device} using dd...")
        subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{device}", "bs=1M", "count=10"], check=True)

        logging.info(f"Disk {device} successfully erased.")
    except subprocess.CalledProcessError:
        logging.error(f"Error: Failed to erase {device} using shred or dd.")
