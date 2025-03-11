import sys
import os
import re
import errno
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError

from disk_erase import get_disk_serial, is_ssd
from disk_operations import process_disk
from utils import list_disks, choose_filesystem
from log_handler import log_info, log_error

def select_disks() -> list[str]:
    """
    Let the user select disks to erase from the command line.
    
    Returns:
        A list of disk names (e.g., ['sda', 'sdb'])
    """
    try:
        disk_list = list_disks()
        if not disk_list:
            print("No disks detected.")
            return []
            
        # Show available disks to the user directly in the console
        # WITHOUT logging to the log file
        print("Available disks:")
        for line in disk_list.strip().split('\n'):
            print(line)
        
        # Show SSD warning
        print("\nWARNING: If any of these disks are SSDs, using this tool with multiple passes")
        print("may damage the SSD and NOT achieve secure data deletion due to SSD wear leveling.")
        print("For SSDs, manufacturer-provided secure erase tools are recommended instead.\n")
        
        selected_disks = input("Enter the disks to erase (comma-separated, e.g., sda,sdb): ").strip()
        disk_names = [disk.strip() for disk in selected_disks.split(",") if disk.strip()]
        
        # Validate disk names
        valid_disks = []
        for disk in disk_names:
            # Check if disk name follows proper format (letters followed by optional numbers)
            if re.match(r'^[a-zA-Z]+[0-9]*$', disk):
                # Verify disk exists
                disk_path = f"/dev/{disk}"
                if os.path.exists(disk_path):
                    valid_disks.append(disk)
                    # Check if it's an SSD and warn
                    if is_ssd(disk):
                        print(f"WARNING: {disk} appears to be an SSD. Using this tool may damage the device and not securely erase all data.")
                else:
                    print(f"Disk {disk_path} not found. Skipping.")
            else:
                print(f"Invalid disk name format: {disk}. Disk names should be like 'sda', 'sdb', etc. Skipping.")
        
        return valid_disks
        
    except KeyboardInterrupt:
        log_error("Disk selection interrupted by user (Ctrl+C)")
        print("\nDisk selection interrupted by user (Ctrl+C)")
        sys.exit(130)
    except IOError as e:
        if e.errno == errno.ENOENT:
            log_error(f"File not found: {str(e)}")
        elif e.errno == errno.EACCES:
            log_error(f"Permission denied: {str(e)}")
        else:
            log_error(f"I/O error: {str(e)}")
        print(f"Error: {str(e)}")
        return []

def confirm_erasure(disk: str) -> bool:
    """
    Get confirmation from the user to erase a specific disk.
    
    Args:
        disk: The name of the disk (e.g., 'sda')
        
    Returns:
        True if user confirms, False otherwise
    """
    while True:
        try:
            # Use disk identifier instead of device path
            disk_id = get_disk_serial(disk)
            # Check if disk is an SSD and add warning if necessary
            is_disk_ssd = is_ssd(disk)
            if is_disk_ssd:
                print("\nWARNING: The selected disk appears to be an SSD.")
                print("Using this program on SSDs may harm the device and not guarantee secure erasure.")
                print("SSDs require specific secure erase commands for proper data removal.\n")
            
            confirmation = input(f"Are you sure you want to securely erase disk ID: {disk_id}? This cannot be undone. (y/n): ").strip().lower()
            if confirmation in {"y", "n"}:
                return confirmation == "y"
            print("Invalid input. Please enter 'y' or 'n'.")
        except KeyboardInterrupt:
            log_error("Erasure confirmation interrupted by user (Ctrl+C)")
            print("\nErasure confirmation interrupted by user (Ctrl+C)")
            sys.exit(130)
        except EOFError:
            log_error("Unexpected end of input during confirmation")
            print("\nUnexpected end of input")
            return False

def get_disk_confirmations(disks: list[str]) -> list[str]:
    """Get confirmation for each disk in the list."""
    try:
        return [disk for disk in disks if confirm_erasure(disk)]
    except KeyboardInterrupt:
        log_error("Disk confirmation process interrupted by user (Ctrl+C)")
        print("\nDisk confirmation process interrupted by user (Ctrl+C)")
        sys.exit(130)
    except EOFError:
        log_error("Unexpected end of input during disk confirmation")
        print("\nUnexpected end of input")
        return []

def run_cli_mode(args):
    """
    Run the command-line interface version.
    
    Args:
        args: Command-line arguments from argparse
    """
    try:
        fs_choice = args.filesystem
        passes = args.passes
        
        disks = select_disks()
        if not disks:
            print("No disks selected. Exiting.")
            return

        confirmed_disks = get_disk_confirmations(disks)
        if not confirmed_disks:
            print("No disks confirmed for erasure. Exiting.")
            return

        if not fs_choice:
            fs_choice = choose_filesystem()

        print("All disks confirmed. Starting operations...\n")
        log_info("Starting disk erasure operations")

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_disk, disk, fs_choice, passes) for disk in confirmed_disks]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except FileNotFoundError as e:
                    log_error(f"Required command not found: {str(e)}")
                    print(f"Error: Required command not found: {str(e)}")
                except CalledProcessError as e:
                    log_error(f"Command execution failed: {str(e)}")
                    print(f"Error: Command execution failed: {str(e)}")
                except PermissionError as e:
                    log_error(f"Permission denied: {str(e)}")
                    print(f"Error: Permission denied: {str(e)}")
                except OSError as e:
                    log_error(f"OS error: {str(e)}")
                    print(f"Error: OS error: {str(e)}")
                except KeyboardInterrupt:
                    # Cancel all pending futures
                    for f in futures:
                        f.cancel()
                    log_error("Disk operations interrupted by user (Ctrl+C)")
                    print("\nDisk operations interrupted by user (Ctrl+C)")
                    sys.exit(130)

        print("All operations completed successfully.")
        log_info("All operations completed successfully.")        
            
    except KeyboardInterrupt:
        print("\nTerminating program")
        log_error("Program terminated by user (Ctrl+C)")
        sys.exit(130)
    except SystemExit:
        # Allow system exit to propagate
        raise
    except Exception as e:
        # Keep one generic exception handler as last resort
        log_error(f"Unexpected error: {str(e)}")
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)