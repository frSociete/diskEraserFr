import logging
import subprocess

LOG_FILE = "/var/log/disk_erase.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_disk_uuid(disk: str) -> str:
    """Retrieve the UUID of a disk if available."""
    try:
        result = subprocess.run(
            ["blkid", f"/dev/{disk}"], capture_output=True, text=True, check=True
        )
        for item in result.stdout.split():
            if item.startswith("UUID="):
                return item.split("=")[1].strip('"')
    except subprocess.CalledProcessError:
        return "UUID not found"
    return "UUID not found"

def log_disk_erasure(disk: str) -> None:
    """Log the disk UUID and successful erasure."""
    uuid = get_disk_uuid(disk)
    logging.info(f"Disk {disk} (UUID: {uuid}) has been successfully erased.")
