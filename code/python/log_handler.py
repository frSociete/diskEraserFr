import logging
import re
from subprocess import check_output, CalledProcessError

# Set up the logging configuration
log_file = "disk_erase.log"
log_handler = logging.FileHandler(log_file)
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

import re
from subprocess import check_output, CalledProcessError

def get_uuid(disk: str) -> str:
    """Return the UUID of the disk's first partition, e.g., /dev/vdd1."""
    try:
        # Define the partition (assuming the first partition for simplicity)
        partition = f"/dev/{disk}1"

        # Run blkid with shell=False
        output = check_output(["blkid", partition]).decode()

        # Use regex to find the UUID in the output
        uuid_match = re.search(r'UUID="([0-9a-fA-F-]+)"', output)
        if uuid_match:
            return uuid_match.group(1)
        else:
            return "Unknown"
    
    except CalledProcessError as e:
        logger.error(f"Failed to execute blkid command for {disk}: {e}")
    except Exception as e:
        logger.error(f"Failed to retrieve UUID for {disk}: {e}")
    
    return "Unknown"


def log_uuid_change(disk: str, prev_uuid: str, new_uuid: str) -> None:
    """Log UUID change to the log file."""
    logger.info(f"Previous UUID => New UUID: {prev_uuid} => {new_uuid}")
    with open(log_file, "a") as log:
        log.write(f"{disk}: {prev_uuid} => {new_uuid}\n")

def log_info(message: str) -> None:
    """Log general information to both the console and log file."""
    logger.info(message)

def log_error(message: str) -> None:
    """Log error message to both the console and log file."""
    logger.error(message)
