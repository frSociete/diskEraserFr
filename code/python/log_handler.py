import logging
import re
import sys
from subprocess import check_output, CalledProcessError

# Define the log file path
log_file = "/var/log/disk_erase.log"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    log_handler = logging.FileHandler(log_file)
    log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
except PermissionError:
    print("Error: Permission denied. Please run the script with sudo.", file=sys.stderr)
    sys.exit(1)  # Exit the script to enforce sudo usage

def get_uuid(disk: str) -> str:
    """Return the UUID of the disk's first partition, e.g., /dev/vdd1."""
    try:
        partition = f"/dev/{disk}1"
        output = check_output(["blkid", partition]).decode()
        uuid_match = re.search(r'UUID="([0-9a-fA-F-]+)"', output)
        return uuid_match.group(1) if uuid_match else "Unknown"
    except CalledProcessError as e:
        logger.error(f"Failed to execute blkid command for {disk}: {e}")
    except Exception as e:
        logger.error(f"Failed to retrieve UUID for {disk}: {e}")
    return "Unknown"

def log_uuid_change(disk: str, prev_uuid: str, new_uuid: str) -> None:
    """Log UUID change to the log file."""
    message = f"UUID changed for {disk}: {prev_uuid} => {new_uuid}"
    logger.info(message)

def log_erase_success(disk: str, uuid: str, filesystem: str) -> None:
    """Log successful erasure with UUID and filesystem format."""
    message = f"Erasure successful for {disk}. UUID: {uuid}, Filesystem: {filesystem}"
    logger.info(message)

def log_info(message: str) -> None:
    """Log general information to both the console and log file."""
    logger.info(message)

def log_error(message: str) -> None:
    """Log error message to both the console and log file."""
    logger.error(message)
