import subprocess
import logging
import sys
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_disk_serial(device: str) -> str:
    """
    Get a stable disk identifier using hdparm or lsblk
    This provides a more consistent identifier across operations
    """
    try:
        # Try hdparm first for serial number
        output = subprocess.run(
            ["hdparm", "-I", f"/dev/{device}"], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        ).stdout.decode()
        serial_match = re.search(r'Serial Number:\s*(\S+)', output)
        if serial_match:
            return serial_match.group(1)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        # Fallback to using device model from lsblk
        output = subprocess.run(
            ["lsblk", "-d", "-o", "MODEL", f"/dev/{device}"], 
            check=True, 
            stdout=subprocess.PIPE
        ).stdout.decode()
        lines = output.strip().split('\n')
        if len(lines) > 1:
            return lines[1].strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Final fallback
    return f"UNKNOWN_{device}"

def is_ssd(device: str) -> bool:
    try:
        output = subprocess.run(
            ["cat", f"/sys/block/{device}/queue/rotational"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output.stdout.decode().strip() == "0"
    except FileNotFoundError:
        logging.error(f"SSD check failed: {device} not found.")
        sys.exit(2)
    except subprocess.SubprocessError:
        logging.error(f"Error executing subprocess for SSD check on {device}.")
        sys.exit(1)
    return False

def erase_disk(device: str, passes: int) -> str:
    try:
        # Type-casting arguments to ensure correct types
        device = str(device)
        passes = int(passes)

        # Get stable disk identifier before erasure
        disk_serial = get_disk_serial(device)

        if is_ssd(device):
            logging.info(f"Warning: {device} appears to be an SSD. Use `hdparm` for secure erase.")
            return disk_serial

        logging.info(f"Erasing {device} using shred with {passes} passes...")
        subprocess.run(["shred", "-n", f"{passes}", "-v", f"/dev/{device}"], check=True)

        logging.info(f"Wiping partition table of {device} using dd...")
        subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{device}", "bs=1M", "count=10"], check=True)

        logging.info(f"Disk {device} successfully erased.")
        return disk_serial
    except FileNotFoundError:
        logging.error(f"Error: Required command not found.")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error(f"Error: Failed to erase {device} using shred or dd.")
        sys.exit(1)