import time
import re
from subprocess import CalledProcessError
from disk_erase import erase_disk_hdd, get_disk_serial, is_ssd, erase_disk_crypto
from disk_partition import partition_disk
from disk_format import format_disk
from log_handler import log_info, log_error, log_erase_operation, blank
from utils import run_command

# Now let's update the process_disk function in disk_operations.py
def process_disk(disk: str, fs_choice: str, passes: int, use_crypto: bool = False, crypto_fill: str = "random", log_func=None) -> None:
    """
    Process a single disk: erase, partition, and format it.
    
    Args:
        disk: The disk name (e.g. 'sda')
        fs_choice: Filesystem choice for formatting
        passes: Number of passes for secure erasure
        use_crypto: Whether to use cryptographic erasure method
        crypto_fill: Fill method for crypto erasure ('random' or 'zero')
        log_func: Optional function for logging progress
    """
    try:
        disk_id = get_disk_serial(disk)
        log_info(f"Processing disk identifier: {disk_id}")
        if log_func:
            log_func(f"Processing disk identifier: {disk_id}")
        
        # Check if disk is SSD and log a warning
        if is_ssd(disk) and not use_crypto:
            log_info(f"WARNING: {disk_id} is an SSD. Multiple-pass erasure may not securely erase all data.")
            if log_func:
                log_func(f"WARNING: {disk_id} is an SSD. Multiple-pass erasure may not securely erase all data.")
        
        # Erase disk using selected method
        if use_crypto:
            method_str = f"Cryptographic erasure with {crypto_fill} filling"
            log_info(f"Using cryptographic erasure ({crypto_fill} fill) for disk ID: {disk_id}")
            if log_func:
                log_func(f"Using cryptographic erasure ({crypto_fill} fill) for disk ID: {disk_id}")
            erase_result = erase_disk_crypto(disk, filling_method=crypto_fill, log_func=log_func)
        else:
            method_str = f"{passes} overwriting passes"
            log_info(f"Using standard multi-pass erasure for disk ID: {disk_id}")
            if log_func:
                log_func(f"Using standard multi-pass erasure for disk ID: {disk_id}")
            erase_result = erase_disk_hdd(disk, passes, log_func=log_func)
        
        log_info(f"Erase completed on disk ID: {disk_id}")
        if log_func:
            log_func(f"Erase completed on disk ID: {disk_id}")
        
        log_info(f"Creating partition on disk ID: {disk_id}")
        if log_func:
            log_func(f"Creating partition on disk ID: {disk_id}")
        
        partition_disk(disk)
        
        log_info("Waiting for partition to be recognized...")
        if log_func:
            log_func("Waiting for partition to be recognized...")
        
        time.sleep(5)  # Wait for the system to recognize the new partition
        
        log_info(f"Formatting disk ID: {disk_id} with {fs_choice}")
        if log_func:
            log_func(f"Formatting disk ID: {disk_id} with {fs_choice}")
        
        format_disk(disk, fs_choice)
        
        log_erase_operation(disk_id, fs_choice, method_str)
        
        log_info(f"Completed operations on disk ID: {disk_id}")
        if log_func:
            log_func(f"Completed operations on disk ID: {disk_id}")
        
        blank()
        
    except FileNotFoundError as e:
        log_error(f"Required command not found: {str(e)}")
        if log_func:
            log_func(f"Required command not found: {str(e)}")
        raise
    except CalledProcessError as e:
        log_error(f"Command execution failed for disk {disk}: {str(e)}")
        if log_func:
            log_func(f"Command execution failed for disk {disk}: {str(e)}")
        raise
    except PermissionError as e:
        log_error(f"Permission denied for disk {disk}: {str(e)}")
        if log_func:
            log_func(f"Permission denied for disk {disk}: {str(e)}")
        raise
    except OSError as e:
        log_error(f"OS error for disk {disk}: {str(e)}")
        if log_func:
            log_func(f"OS error for disk {disk}: {str(e)}")
        raise
    except KeyboardInterrupt:
        log_error(f"Processing of disk {disk} interrupted by user")
        if log_func:
            log_func(f"Processing of disk {disk} interrupted by user")
        raise

def get_active_disk():
    """Get the disk containing the active filesystem or live boot media"""
    
    try:
        devices = set()
        
        # Get the mount point of the root filesystem
        output = run_command(["df", "-h", "/"])
        lines = output.strip().split('\n')
        if len(lines) >= 2:  # Header plus at least one entry
            # The device should be in the first column of the second line
            device = lines[1].split()[0]
            # Extract just the base device (e.g., sda from /dev/sda1)
            match = re.search(r'/dev/([a-zA-Z]+)', device)
            if match:
                devices.add(match.group(1))
        
        # Look for live boot media mount points
        output = run_command(["df", "-h"])
        lines = output.strip().split('\n')
        for line in lines[1:]:  # Skip header line
            parts = line.split()
            if len(parts) >= 6:  # Ensure we have enough columns
                device = parts[0]
                mount_point = parts[5]
                
                if "/run/live" in mount_point:
                    match = re.search(r'/dev/([a-zA-Z]+)', device)
                    if match:
                        devices.add(match.group(1))
        
        return list(devices) if devices else None
    except FileNotFoundError:
        log_error(f"Error: 'df' command not found")
        return None
    except CalledProcessError as e:
        log_error(f"Error running 'df' command: {str(e)}")
        return None
    except (IndexError, ValueError) as e:
        log_error(f"Error parsing 'df' output: {str(e)}")
        return None
    except KeyboardInterrupt:
        log_error("Operation interrupted by user")
        return None